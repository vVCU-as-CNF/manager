from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from nbi_interactions import *
from k8s_interactions import *

CONFIG1 = "clusters/kubelet1.config"
CONFIG2 = "clusters/kubelet2.config"

VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"

CLUSTER_NAMESPACE = "99df5250-1cec-49f5-aba8-25017a9aadb7"

app = FastAPI()

# fodase
@app.get("/")
def read_root():
    return {"Hello": "World"}

# create a new ns instance
class CreateNSData(BaseModel):
    vim_account: str
    nsd: str
    instance_name: str
@app.post("/osm/ns/create")
async def create(data: CreateNSData):
    getToken()
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages()

    instance_id = createNSInstance(vim_accounts[data.vim_account], ns_packages[data.nsd], data.instance_name)
    instantiateNSInstance(instance_id, vim_accounts[data.vim_account], data.instance_name)

    deleteToken()
    return {"instance_id": instance_id, "instance_name": data.instance_name, "vim_account": data.vim_account, "nsd": data.nsd}

# get info about ns instance
@app.get("/osm/ns/{ns_name}/status")
def status(ns_name: str):
    getToken()
    ns_instances = listNSInstances()
    
    deleteToken()
    if ns_name not in ns_instances:
        raise HTTPException(status_code=404, detail="NS instance not found")
    
    return ns_instances[ns_name]

# delete ns instance
@app.delete("/osm/ns/{ns_name}/delete")
async def delete(ns_name: str):
    getToken()
    ns_instances = listNSInstances()

    if ns_name not in ns_instances:
        deleteToken()
        raise HTTPException(status_code=404, detail="NS instance not found")

    terminateNSInstance(ns_instances[ns_name]["id"])
    waitForNSState(ns_name, "NOT_INSTANTIATED")
    deleteNSInstance(ns_instances[ns_name]["id"])
    deleteToken()
    return {"id": ns_instances[ns_name]["id"], "name": ns_name}

# migrate vnf from one cluster/ns/vim to another
@app.put("/osm/vnf/{vnf_id}/migrate")
def migrate():
    return {"Hello": "World"}