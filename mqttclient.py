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
    global last_topic, last_migrate, current_vim_account, instance_id, instance_name, migration_cooldown

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

        print("Migration complete!")
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

random_string = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
instance_name = "frog-ns-" + random_string

token = getToken()
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
    
    dts = {}
    ns_instances = listNSInstances()
    for instance_id in ns_instances:
        data = getNSInstanceInfo(instance_id)
        info = yaml.safe_load(data)

        if "vim_info" not in info["vld"][0] or len(info["vld"][0]["vim_info"]) == 0:
            dts[ns_instances[instance_id]["name"]] = {"vim": "None", "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"]}
        else: 
            vim = info["vld"][0]["vim_info"]
            vim2 = list(vim.keys())[0]
            vim3 = vim2.split(":")[1]
            dts[ns_instances[instance_id]["name"]] = {"vim": vim3, "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"]}

    deleteToken(token)
    return dts

publish_client = mqtt.Client()
publish_client.connect("10.255.32.4", 1883)

publish_interval = 5 # seconds
start_time = time.time()
while True:
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time >= publish_interval:
        print("publishing...")
        publish_client.publish("manager", json.dumps(get_dts()))
        start_time = time.time()