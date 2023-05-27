import yaml
import uvicorn
import threading

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from kubernetes import client, config
from datetime import datetime

from nbi_interactions import *
from k8s_interactions import *
from mqttclient import *

CONFIG1 = "clusters/kubelet1.config"
CONFIG2 = "clusters/kubelet2.config"

VIM_ACCOUNT_1 = "Jarvis"
VIM_ACCOUNT_2 = "Jarvis2"

CLUSTER_NAMESPACE = "2a6f15e7-cef8-4037-9423-74516a7ccfa8"

app = FastAPI()
mqttclient = None
publish_thread = None
publish_flag = False

@app.on_event("startup")
def startup():
    global mqttclient
    mqttclient = MqttClient()

# fodase
@app.get("/")
def read_root():
    return {"Hello": "World"}

# start tile listener
@app.get("/listener/start")
async def start_listerner():
    global mqttclient
    if mqttclient.startListening() == 0:
        return {"message": "tile listener started"}
    else:
        return {"message": "tile listener already started"}

# stop the listener
@app.get("/listener/stop")
async def stop_listener():
    global mqttclient
    if mqttclient.stopListening() == 0:
        return {"message": "tile listener stopped"}
    else:
        return {"message": "tile listener not started"}
    
# get time till next migration
@app.get("/listener/countdown")
async def countdown():
    global mqttclient
    return {"countdown": mqttclient.countdown()}

@app.get("/listener/topics")
async def get_topics():
    global mqttclient
    return {"topics": mqttclient.topics}

# list all ns instances
@app.get("/osm/ns/")
async def list_instances():
    getToken()
    ns_instances = listNSInstances(print_info=True)
    
    deleteToken()
    return ns_instances

# create a new ns instance
class CreateNSData(BaseModel):
    vim_account: str
    nsd_name: str
    instance_name: str
@app.post("/osm/ns/create")
async def create(data: CreateNSData):
    getToken()
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages()

    instance_id = createNSInstance(vim_accounts[data.vim_account], ns_packages[data.nsd_name], data.instance_name)
    instantiateNSInstance(instance_id, vim_accounts[data.vim_account], data.instance_name)

    deleteToken()
    return {"instance_id": instance_id, "instance_name": data.instance_name, "vim_account": data.vim_account, "nsd": data.nsd_name}

# get info about ns instance
@app.get("/osm/ns/{ns_id}")
async def get_instance(ns_id: str):
    getToken()
    ns_instances = listNSInstances()
    
    deleteToken()
    if ns_id not in ns_instances:
        raise HTTPException(status_code=404, detail="NS instance (id) not found")
    
    return ns_instances[ns_id]

# delete ns instance
@app.delete("/osm/ns/{ns_id}/delete")
async def delete_instance(ns_id: str):
    getToken()
    ns_instances = listNSInstances()

    if ns_id not in ns_instances:
        deleteToken()
        raise HTTPException(status_code=404, detail="NS instance not found")

    terminateNSInstance(ns_id)
    waitForNSState(ns_id, "NOT_INSTANTIATED")
    deleteNSInstance(ns_id)
    deleteToken()
    return {"id": ns_id, "name": ns_instances[ns_id]["name"]}

# migrate a ns instance
class MigrateNSData(BaseModel):
    instance_name: str
    future_vim_account: str
@app.get("/osm/ns/{ns_id}/migrate")
async def migrate_instance(ns_id: str, data: MigrateNSData):
    getToken()
    ns_instances = listNSInstances()
    ns_name = data.instance_name
    
    if ns_id not in ns_instances:
        deleteToken()
        raise HTTPException(status_code=404, detail="NS instance (id) not found")

    if ns_name not in [ns_instances[i]["name"] for i in ns_instances]:
        deleteToken()
        raise HTTPException(status_code=404, detail="NS instance (name) not found")

    if ns_instances[ns_id]["state"] != "READY":
        deleteToken()
        raise HTTPException(status_code=400, detail="NS instance is not ready")

    old_instance = ns_instances[ns_id]
    vim_accounts = listVIMAccounts()
    if data.future_vim_account not in vim_accounts:
        deleteToken()
        raise HTTPException(status_code=404, detail="VIM account not found")

    ts = datetime.now()
    new_instance_name = ns_name
    new_instance_id = createNSInstance(vim_accounts[data.future_vim_account], old_instance["nsd_id"], new_instance_name)
    waitForNSState(new_instance_id, "NOT_INSTANTIATED")
    instantiateNSInstance(new_instance_id, vim_accounts[data.future_vim_account], new_instance_name)
    waitForNSState(new_instance_id, "READY")
    
    if data.future_vim_account == VIM_ACCOUNT_1:
        config.load_kube_config(config_file="clusters/kubelet1.config")
    elif data.future_vim_account == VIM_ACCOUNT_2:
        config.load_kube_config(config_file="clusters/kubelet2.config")

    api = client.CoreV1Api()
    waitForPodReady(api, CLUSTER_NAMESPACE)
    time1 = (datetime.now() - ts).total_seconds()

    terminateNSInstance(ns_id)
    waitForNSState(ns_id, "NOT_INSTANTIATED")
    deleteNSInstance(ns_id)
    time2 = (datetime.now() - ts).total_seconds()

    deleteToken()

    return {"old_instance": old_instance, "new_instance": {"id": new_instance_id, "name": new_instance_name, "vim_account": data.future_vim_account}, "time_till_ready": time1, "time_till_done": time2}

@app.get("/publisher/start")
async def start_publisher():
    global mqttclient
    mqttclient.startPublishing()    
    
    return {"message": "publisher started"}

@app.get("/publisher/stop")
async def stop_publisher():
    global mqttclient
    mqttclient.stopPublishing()

    return {"message": "publisher stopped"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
