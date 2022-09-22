from fastapi import FastAPI
from pydantic import BaseModel
from elasticsearch import Elasticsearch
import requests
from PIL import Image
import imagehash
import json


# =================================== Globals ========================================= #

app = FastAPI()

es = Elasticsearch('http://es-singlenode:9200/',timeout=60, max_retries=10, retry_on_timeout=True)
print(es.info())
index = "image_hash"
es.indices.create(index=index, ignore=400)


class Payload(BaseModel):
    url: str

# =================================== Helper ========================================= #

def imageHash(url):

    img = Image.open(requests.get(url, stream=True).raw)
    a_hash = imagehash.average_hash(img)
    p_hash = imagehash.phash(img)
    d_hash = imagehash.dhash(img)

    result =  { "url":url, "a_hash": str(a_hash), "p_hash": str(p_hash), "d_hash":str(d_hash)}

    return result

def search_api(doc):
    body = {
        "query": {
            "bool": {
            "must": [
                { "match": { "a_hash": doc.get("a_hash") } },
                { "match": { "p_hash": doc.get("p_hash") } },
                { "match": { "d_hash": doc.get("d_hash") } }
            ]
            }
        }
    }

    res = es.search(index=index, body=body)
    is_exist = res.get("hits").get("total").get("value")
    data = res.get("hits").get("hits")
    return is_exist, data
    

# =================================== Routes ========================================= #

@app.post("/")
async def read_root(payload: Payload):
    payload_dict = payload.dict()
    doc = imageHash(payload_dict.get("url"))

    is_exist, data = search_api(doc)
    if is_exist:
        return {"status": "Image already exists", "data": data}

    es.index(index=index, document=doc)    
    return {"status": "Newly created"}





