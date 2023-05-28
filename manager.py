import yaml
import uvicorn

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from kubernetes import client, config
from datetime import datetime

from common.nbi_interactions import *
from common.k8s_interactions import *

CONFIG1 = "common/clusters/kubelet1.config"
CONFIG2 = "common/clusters/kubelet2.config"

VIM_ACCOUNT_1 = "Jarvis"
VIM_ACCOUNT_2 = "Jarvis2"

CLUSTER_NAMESPACE = "2a6f15e7-cef8-4037-9423-74516a7ccfa8"

app = FastAPI()

time1 = None
time2 = None
timestamp = None

# fodase
@app.get("/")
def read_root():
    return {"Hello": "World"}

# list all ns instances
@app.get("/osm/ns/")
async def list_instances():
    token = token = getToken()
    ns_instances = listNSInstances(print_info=True)
    
    deleteToken(token)
    return ns_instances

# create a new ns instance
class CreateNSData(BaseModel):
    vim_account: str
    nsd_name: str
    instance_name: str
@app.post("/osm/ns/create")
async def create(data: CreateNSData):
    token = token = getToken()
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages()

    instance_id = createNSInstance(vim_accounts[data.vim_account], ns_packages[data.nsd_name], data.instance_name)
    instantiateNSInstance(instance_id, vim_accounts[data.vim_account], data.instance_name)

    deleteToken(token)
    return {"instance_id": instance_id, "instance_name": data.instance_name, "vim_account": data.vim_account, "nsd": data.nsd_name}

# get info about ns instance
@app.get("/osm/ns/{ns_id}")
async def get_instance(ns_id: str):
    token = getToken()
    ns_instances = listNSInstances()
    
    deleteToken(token)
    if ns_id not in ns_instances:
        raise HTTPException(status_code=404, detail="NS instance (id) not found")
    
    return ns_instances[ns_id]

# delete ns instance
@app.delete("/osm/ns/{ns_id}/delete")
async def delete_instance(ns_id: str):
    token = getToken()
    ns_instances = listNSInstances()
    
    if ns_id not in ns_instances:
        deleteToken(token)
        raise HTTPException(status_code=404, detail="NS instance not found")

    terminateNSInstance(ns_id)
    waitForNSState(ns_id, "NOT_INSTANTIATED")
    deleteNSInstance(ns_id)
    deleteToken(token)
    return {"id": ns_id, "name": ns_instances[ns_id]["name"]}

# migrate a ns instance
class MigrateNSData(BaseModel):
    instance_name: str
    future_vim_account: str
@app.get("/osm/ns/{ns_id}/migrate")
async def migrate_instance(ns_id: str, data: MigrateNSData, tasks: BackgroundTasks):
    token = getToken()
    ns_instances = listNSInstances()
    ns_name = data.instance_name
    
    if ns_id not in ns_instances:
        deleteToken(token)
        raise HTTPException(status_code=404, detail="NS instance (id) not found")

    if ns_name not in [ns_instances[i]["name"] for i in ns_instances]:
        deleteToken(token)
        raise HTTPException(status_code=404, detail="NS instance (name) not found")

    if ns_instances[ns_id]["state"] != "READY":
        deleteToken(token)
        raise HTTPException(status_code=400, detail="NS instance is not ready")

    old_instance = ns_instances[ns_id]
    vim_accounts = listVIMAccounts()
    if data.future_vim_account not in vim_accounts:
        deleteToken(token)
        raise HTTPException(status_code=404, detail="VIM account not found")

    new_instance_id = createNSInstance(vim_accounts[data.future_vim_account], old_instance["nsd_id"], ns_name)
    deleteToken(token)
    tasks.add_task(migrate, ns_id, new_instance_id, ns_name, data.future_vim_account)
    return {"message": "migrating", "old_instance_id": ns_id, "instance_name": ns_name, "future_vim_account": data.future_vim_account, "new_instance_id": new_instance_id}

@app.get("/osm/migration_times")
def get_migration_times():
    global time1, time2, timestamp
    return {"time_till_ready": time1, "time_till_done": time2, "ts": timestamp}

def migrate(ns_id, new_instance_id, instance_name, future_vim_account):
    token = getToken()

    vim_accounts = listVIMAccounts()

    ts = datetime.now()
    waitForNSState(new_instance_id, "NOT_INSTANTIATED")
    instantiateNSInstance(new_instance_id, vim_accounts[future_vim_account], instance_name)
    waitForNSState(new_instance_id, "READY")
    
    if future_vim_account == VIM_ACCOUNT_1:
        config.load_kube_config(config_file="common/clusters/kubelet1.config")
    elif future_vim_account == VIM_ACCOUNT_2:
        config.load_kube_config(config_file="common/clusters/kubelet2.config")

    global time1, time2, timestamp

    api = client.CoreV1Api()
    waitForPodReady(api, CLUSTER_NAMESPACE)
    time1 = (datetime.now() - ts).total_seconds()

    terminateNSInstance(ns_id)
    waitForNSState(ns_id, "NOT_INSTANTIATED")
    deleteNSInstance(ns_id)
    time2 = (datetime.now() - ts).total_seconds()

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    deleteToken(token)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
