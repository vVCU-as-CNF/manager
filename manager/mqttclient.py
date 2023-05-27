import requests
import random
import threading
import json
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

from nbi_interactions import *

BASE_URL = "http://localhost:8000/"
VIM_ACCOUNT_1 = "Jarvis"
VIM_ACCOUNT_2 = "Jarvis2"


class MqttClient():
    def __init__(self) -> None:
        self.listen_client = mqtt.Client()
        self.listen_client.on_message = self.on_message
        self.listen_client.connect("es-broker.av.it.pt", 1883)

        self.listen_topic = "its_center/inqueue/json/3306/CAM/#"

        self.session = requests.Session()
        self.session.verify = False

        self.instance_name = ""
        self.instance_id = ""
        self.current_vim_account = VIM_ACCOUNT_1 if random.randint(0,1) == 0 else VIM_ACCOUNT_2

        self.topics = []
        self.last_topic = ""

        self.last_migrate = datetime.now()
        self.migration_cooldown = 5 # minutes


        self.publish_client = mqtt.Client()
        self.publish_client.connect("10.255.32.4", 1883)

        self.publish_thread = None
        self.publishing = False

    def on_message(self, client, userdata, msg):
        topic = msg.topic

        if topic != self.last_topic:
            self.on_topic_change(topic)

    def on_topic_change(self, topic):
        print(topic)
        if topic not in self.topics:
            self.topics.append(topic)

        locationTrigger = False
        lastData = self.last_topic.split("/")
        data = topic.split("/")
        if self.last_topic != "" and data[-7] != lastData[-7]:
            locationTrigger = True
        onCooldown = datetime.now() < self.last_migrate + timedelta(minutes=self.migration_cooldown)

        self.last_topic = topic

        if locationTrigger: # and not on cooldown
            print("Migration time!")
            self.last_migrate = datetime.now()

            self.current_vim_account = VIM_ACCOUNT_1 if self.current_vim_account == VIM_ACCOUNT_2 else VIM_ACCOUNT_2

            url = BASE_URL + "osm/ns/" + self.instance_id + "/migrate"
            payload = {
                "instance_name": self.instance_name,
                "future_vim_account": self.current_vim_account
            }

            self.listen_client.unsubscribe(self.listen_topic)

            r = session.get(url=url, data=json.dumps(payload))
            print(r.text)
            data = json.loads(r.text)
            # self.instance_id = data["new_instance"]["id"]

            print("Migration complete!")
            # print("Time \l Ready: " + str(data["time_till_ready"]))
            # print("Time Till Done: " + str(data["time_till_done"]))

            self.listen_client.subscribe(self.listen_topic)
        else:
            print("Not migration time!")
            # print("Time till next migration: " + self.countdown())

    def startListening(self):
        if self.instance_name != "":
            return 1
        
        random_string = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
        self.instance_name = "frog-ns-" + random_string

        token = getToken()

        vim_accounts = listVIMAccounts()
        ns_packages = listNSPackages()

        self.instance_id = createNSInstance(vim_accounts[self.current_vim_account], ns_packages["vvcu-as-acnf_ns"], self.instance_name)
        instantiateNSInstance(self.instance_id, vim_accounts[self.current_vim_account], self.instance_name)
        waitForNSState(self.instance_id, "READY")
        deleteToken(token)

        print("Instance created and instantiated. Listening...")
        self.last_migrate = datetime.now() - timedelta(minutes=4, seconds=40) # 1 min to start migrations

        self.listen_client.subscribe(self.listen_topic)
        self.listen_client.loop_start()
        return 0

    def stopListening(self):
        if self.instance_name == "":
            return 1
        
        self.listen_client.unsubscribe(self.listen_topic)
        self.listen_client.loop_stop()
        
        token = getToken()
        terminateNSInstance(self.instance_id)
        waitForNSState(self.instance_id, "NOT_INSTANTIATED")
        deleteNSInstance(self.instance_id)
        deleteToken(token)

        self.instance_name = ""
        self.instance_id = ""
        
        return 0
    
    def countdown(self):
        onCooldown = datetime.now() < (self.last_migrate + timedelta(minutes=self.migration_cooldown))
        return str(self.last_migrate + timedelta(minutes=self.migration_cooldown) - datetime.now()) if onCooldown else "00:00:00"
    
    def startPublishing(self):
        self.publishing = True
        self.publish_thread = threading.Thread(target=self.publish)
        self.publish_thread.start()

    def stopPublishing(self):
        self.publishing = False
        self.publish_thread.join()

    def publish(self):
        print("publishing")
        while(self.publishing):
            self.publish_client.publish("manager", json.dumps(self.get_dts()))
            sleep(5)

    def get_dts(self):
        token = getToken()
        
        dts = {}
        ns_instances = listNSInstances()
        for instance_id in ns_instances:
            data = getNSInstanceInfo(instance_id)
            info = yaml.safe_load(data)
            # print(list(info["vld"][0]["vim_info"].keys()))
            if "vim_info" not in info["vld"][0] or len(info["vld"][0]["vim_info"]) == 0:
                dts[ns_instances[instance_id]["name"]] = {"vim": "None", "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"]}
            else: 
                vim = info["vld"][0]["vim_info"]
                vim2 = list(vim.keys())[0]
                vim3 = vim2.split(":")[0]

                dts[ns_instances[instance_id]["name"]] = {"vim": vim3, "id": instance_id, "nsd_name": ns_instances[instance_id]["nsd_name"], "state": ns_instances[instance_id]["state"]}

        deleteToken(token)
        return dts