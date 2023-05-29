import requests
import random
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

from common.nbi_interactions import *

BASE_URL = "http://manager:8000/"
VIM_ACCOUNT_1 = "Jarvis"
VIM_ACCOUNT_2 = "Jarvis2"

session = requests.Session()
session.verify = False

# listening
def on_message(client, userdata, msg):
    global last_topic
    topic = msg.topic
    if topic != last_topic:
        on_topic_change(topic)

def on_topic_change(topic):
    global last_topic, last_migrate, current_vim_account, instance_id, instance_name, migration_cooldown, migration_counter

    locationTrigger = False
    lastData = last_topic.split("/")
    data = topic.split("/")
    if last_topic != "" and data[-7] != lastData[-7]:
        locationTrigger = True
    onCooldown = datetime.now() < last_migrate + timedelta(minutes=migration_cooldown)

    last_topic = topic
    
    if locationTrigger: # and not on cooldown
        print("Migration time!")
        last_migrate = datetime.now()

        current_vim_account = VIM_ACCOUNT_1 if current_vim_account == VIM_ACCOUNT_2 else VIM_ACCOUNT_2

        url = BASE_URL + "osm/ns/" + instance_id + "/migrate"
        payload = {
            "instance_name": instance_name,
            "future_vim_account": current_vim_account
        }

        listen_client.unsubscribe(listen_topic)

        r = session.get(url=url, data=json.dumps(payload))
        data = json.loads(r.text)
        instance_id = data["new_instance_id"]

        print("Migration started!")
        migration_counter += 1
        # print("Time \l Ready: " + str(data["time_till_ready"]))
        # print("Time Till Done: " + str(data["time_till_done"]))

        listen_client.subscribe(listen_topic)
    else:
        print("Not migration time!")
        # print("Time till next migration: " + countdown())

listen_client = mqtt.Client()
listen_client.on_message = on_message
listen_client.connect("es-broker.av.it.pt", 1883)
listen_topic = "its_center/inqueue/json/3306/CAM/#"

instance_name = ""
instance_id = ""
current_vim_account = VIM_ACCOUNT_1 if random.randint(0,1) == 0 else VIM_ACCOUNT_2

last_topic = ""

last_migrate = datetime.now()
migration_cooldown = 5 # minutes
migration_counter = 0

token = getToken()
random_string = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
instance_name = "frog" #-ns-" + random_string
vim_accounts = listVIMAccounts()
ns_packages = listNSPackages()
instance_id = createNSInstance(vim_accounts[current_vim_account], ns_packages["vvcu-as-acnf_ns"], instance_name)
instantiateNSInstance(instance_id, vim_accounts[current_vim_account], instance_name)
waitForNSState(instance_id, "READY")
deleteToken(token)

print("Instance created and instantiated. Listening...")
last_migrate = datetime.now() - timedelta(minutes=4, seconds=30) # 1 min to start migrations

listen_client.subscribe(listen_topic)
listen_client.loop_start()

# publishing
def get_dts():
    token = getToken()
    
    vim_accounts = listVIMAccounts()
    vim_accounts = {value: key for key, value in vim_accounts.items()}
    ns_instances = listNSInstances()
    
    dts = {}
    for instance_id in ns_instances:
        data = getNSInstanceInfo(instance_id)
        info = yaml.safe_load(data)

        if "vld" not in info or "vim_info" not in info["vld"][0] or len(info["vld"][0]["vim_info"]) == 0:
            dts[ns_instances[instance_id]["name"]] = {"name": ns_instances[instance_id]["name"], "vim": "null", "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"], "future_vim_account": "null"}
        else: 
            vim = info["vld"][0]["vim_info"]
            vim2 = list(vim.keys())[0]
            vim3 = vim2.split(":")[1]
            dts[ns_instances[instance_id]["name"]] = {"name": ns_instances[instance_id]["name"], "vim": vim_accounts[vim3], "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"], "future_vim_account": "null"}

    deleteToken(token)
    return dts

def get_vims():
    token = getToken()

    vim_accounts = listVIMAccounts()
    vim_accounts = {value: key for key, value in vim_accounts.items()}
    ns_instances = listNSInstances()

    vims = {}
    for instance in ns_instances:
        data = getNSInstanceInfo(instance)
        info = yaml.safe_load(data)
        vim = ""
        if "vld" not in info or "vim_info" not in info["vld"][0] or len(info["vld"][0]["vim_info"]) == 0:
            vim = "null"
        else:
            vim = info["vld"][0]["vim_info"]
            vim2 = list(vim.keys())[0]
            vim3 = vim2.split(":")[1]
            vim = vim3

        if vim != "null":
            if vim_accounts[vim] not in vims:
                vims[vim_accounts[vim]] = [ns_instances[instance]["name"]]
            else:
                vims[vim_accounts[vim]].append(ns_instances[instance]["name"])

    deleteToken(token)
    new_vims = {vim: {} for vim in vims}
    instances = [ns_instances[ns] for ns in ns_instances]

    for vim in vims:
        for instance in vims[vim]:
            new_vims[vim][instance] = True
    for instance in instances:
        for vim in new_vims:
            if instance["name"] not in new_vims[vim]:
                new_vims[vim][instance["name"]] = False

    return new_vims
        
publish_client = mqtt.Client()
publish_client.connect("10.255.32.4", 1883)

times_till_ready = []
times_till_done = []
last_ts = ""

publish_interval = 5 # seconds
start_time = time.time()
while True:
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time >= publish_interval:
        print("publishing...")
        publish_client.publish("manager", json.dumps(get_dts()))

        vims = get_vims()
        publish_client.publish("vims", json.dumps(vims))
        
        r = session.get(url=BASE_URL + "osm/migration_times")
        publish_client.publish("migration_times", r.text)
        
        publish_client.publish("migration_counter", migration_counter)
        
        start_time = time.time()

