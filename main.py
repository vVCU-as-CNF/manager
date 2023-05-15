from fastapi import FastAPI

from nbi_interactions import *
from k8s_interactions import *

CONFIG1 = "clusters/kubelet1.config"
CONFIG2 = "clusters/kubelet2.config"

VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"

CLUSTER_NAMESPACE = "99df5250-1cec-49f5-aba8-25017a9aadb7"

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/osm/create")
def create():
    getToken()
    
    deleteToken()
    return {"Hello": "World"}

@app.get("/osm/{ns_id}/status")
def status():
    return {"Hello": "World"}

@app.delete("/osm/{ns_id}/delete")
def delete():
    return {"Hello": "World"}

@app.put("/osm/{ns_id}/migrate")
def migrate():
    return {"Hello": "World"}
