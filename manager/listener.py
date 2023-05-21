import requests
import random
import json
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

from nbi_interactions import *

BASE_URL = "http://localhost:8000/"
VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"


class Listener():
    def __init__(self) -> None:
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect("es-broker.av.it.pt", 1883) # futuramente no localhost porque é p rodar na nossa maquina
        self.topic = "its_center/inqueue/json/3306/CAM/#"

        self.session = requests.Session()
        self.session.verify = False

        self.instance_name = ""
        self.instance_id = ""
        self.current_vim_account = VIM_ACCOUNT_1 if random.randint(0,1) == 0 else VIM_ACCOUNT_2

        self.migration_cooldown = 5 # minutes

        self.last_topic = ""
        self.last_migrate = datetime.now()


    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")

        if topic != self.last_topic:
            self.on_topic_change(topic)

    def on_topic_change(self, topic):
        self.last_topic = topic
        
        if datetime.now() > self.last_migrate + timedelta(minutes=self.migration_cooldown):
            print("Migration time!", topic[-8:-1])
            self.last_migrate = datetime.now()

            self.current_vim_account = VIM_ACCOUNT_1 if self.current_vim_account == VIM_ACCOUNT_2 else VIM_ACCOUNT_2

            url = BASE_URL + "osm/ns/" + self.instance_id + "/migrate"
            payload = {
                "instance_name": self.instance_name,
                "future_vim_account": self.current_vim_account
            }

            self.client.unsubscribe(self.topic)

            r = session.get(url=url, data=json.dumps(payload))
            data = json.loads(r.text)
            self.instance_id = data["new_instance"]["id"]

            print("Migration complete!")
            print("Time Till Ready: " + str(data["time_till_ready"]))
            print("Time Till Done: " + str(data["time_till_done"]))

            self.client.subscribe(self.topic)
        else:
            print("Not migration time!")
            print("Time till next migration: " + str(self.last_migrate + timedelta(minutes=self.migration_cooldown) - datetime.now()))


    def start(self):
        if self.instance_name != "":
            return 1
        
        random_string = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
        self.instance_name = "frog-ns-" + random_string

        getToken()

        vim_accounts = listVIMAccounts()
        ns_packages = listNSPackages()

        self.instance_id = createNSInstance(vim_accounts[self.current_vim_account], ns_packages["vvcu-as-acnf_ns"], self.instance_name)
        instantiateNSInstance(self.instance_id, vim_accounts[self.current_vim_account], self.instance_name)
        waitForNSState(self.instance_id, "READY")
        deleteToken()

        print("Instance created and instantiated. Listening...")
        self.last_migrate = datetime.now() - timedelta(minutes=4) # 1 min to start migrations

        self.client.subscribe(self.topic)
        self.client.loop_start()
        return 0

    def stop(self):
        if self.instance_name == "":
            return 1
        
        self.client.unsubscribe(self.topic)
        self.client.loop_stop()
        
        getToken()
        terminateNSInstance(self.instance_id)
        waitForNSState(self.instance_id, "NOT_INSTANTIATED")
        deleteNSInstance(self.instance_id)
        deleteToken()

        self.instance_name = ""
        self.instance_id = ""
        
        return 0
    
    def countdown(self):
        return str(self.last_migrate + timedelta(minutes=self.migration_cooldown) - datetime.now())
        

