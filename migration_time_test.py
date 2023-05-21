import requests
import json
from time import sleep

from manager.nbi_interactions import *

BASE_URL = "http://localhost:8000/"
VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"
INSTANCE_NAME = "toupeirito"

NTESTS = 10

session = requests.Session()
session.verify = False

def main():
    vim_acc = VIM_ACCOUNT_1

    # MAKE TEST INSTANCE
    getToken()
    
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages()

    instance_id = createNSInstance(vim_accounts[vim_acc], ns_packages["vvcu-as-acnf_ns"], INSTANCE_NAME)
    instantiateNSInstance(instance_id, vim_accounts[vim_acc], INSTANCE_NAME)
    waitForNSState(instance_id, "READY")
    
    # START MIGRATION TESTING
    times_till_ready = []
    times_till_done = []
    for i in range(NTESTS):
        print("Migration test " + str(i))
        vim_acc = VIM_ACCOUNT_1 if vim_acc == VIM_ACCOUNT_2 else VIM_ACCOUNT_2

        url = BASE_URL + "osm/ns/" + instance_id + "/migrate"
        payload = {
            "instance_name": INSTANCE_NAME,
            "future_vim_account": vim_acc
        }
        
        r = session.get(url=url, data=json.dumps(payload))
        data = json.loads(r.text)
        times_till_ready.append(data["time_till_ready"])
        times_till_done.append(data["time_till_done"])
        
        instance_id = data["new_instance"]["id"]
        
        print(data["time_till_ready"])
        print(data["time_till_done"])

    print(times_till_ready)
    print(times_till_done)

    deleteToken()

if __name__ == "__main__":
    main()