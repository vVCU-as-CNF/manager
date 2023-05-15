import yaml
import requests
import urllib3

from time import sleep

#
# STATIC VARIABLES
#

BASE_URL = "https://10.255.28.79:9999/osm/"

session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#
# TOKENS
#
def getToken():
    """Get token from OSM"""
    url = BASE_URL + "admin/v1/tokens"
    payload = {
        "username": "admin",
        "password": "admin"
    }
    r = session.post(url, data=payload)

    token = yaml.safe_load(r.text)["id"]
    
    print("--------------------")
    print("Got token: " + token)

    return token

def deleteToken():
    """Deletes current token from OSM"""
    url = BASE_URL + "admin/v1/tokens"
    r = session.delete(url)

    token = r.text.split(" ")[2].replace("\'", "")

    print("--------------------")
    print("Deleted current token: " + token)

def allTokens():
    """Lists all tokens from OSM"""
    url = BASE_URL + "admin/v1/tokens"
    r = session.get(url)

    tokens = yaml.safe_load(r.text)
    tokens = [t["id"] for t in tokens]

    print("--------------------")
    print("All active tokens: ")
    for t in tokens:
        print(" - " + t)

    return tokens

#
# VIM ACCOUNTS
#

def listVIMAccounts():
    """Lists all VIM accounts from OSM"""
    url = BASE_URL + "admin/v1/vim_accounts"
    r = session.get(url)

    vim_accounts = yaml.safe_load(r.text)
    vim_accounts = {a["name"]: a["_id"] for a in vim_accounts}

    print("--------------------")
    print("All VIM Accounts: ")
    for k in vim_accounts:
        print("  " + k)
        print("  id - " + vim_accounts[k])

    return vim_accounts

def getVIMAccountInfo(account_id):
    """Gets VIM account info from OSM"""
    url = BASE_URL + "admin/v1/vim_accounts/" + account_id
    r = session.get(url)

    print(r.text)

#
# VNF PACKAGES
#

def listVNFPackages():
    """Lists all VNF packages on OSM"""
    url = BASE_URL + "vnfpkgm/v1/vnf_packages"
    r = session.get(url)

    # lines = r.text.split("\n")

    # vnf_packages = [l.replace("        name: ", "") for l in lines if l.startswith("        name: ")]
    # vnf_packages_ids = [l.replace("    _id: ", "") for l in lines if l.startswith("    _id: ")]

    vnf_packages = yaml.safe_load(r.text)
    vnf_packages = {a["name"]: a["_id"] for a in vnf_packages}

    print("--------------------")   
    print("All VNF packages: ")
    for k in vnf_packages:
        print("  " + k)
        print("  id - " + vnf_packages[k])

    return vnf_packages

def getVNFPackageInfo(package_id):
    """Gets VNF package info from OSM"""
    url = BASE_URL + "vnfpkgm/v1/vnf_packages/" + package_id
    r = session.get(url)

    print(r.text)

#
# NS PACKAGES
#

def listNSPackages(print_info=False):
    """Lists all NS packages from OSM"""
    url = BASE_URL + "nsd/v1/ns_descriptors"
    r = session.get(url)

    ns_packages = yaml.safe_load(r.text)
    ns_packages = {a["name"]: a["_id"] for a in ns_packages}

    if print_info:
        print("--------------------")   
        print("All NS packages: ")
        for k in ns_packages:
            print("  " + k)
            print("  id - " + ns_packages[k])

    return ns_packages

def getNSPackageInfo(package_id):
    """Gets NS package info from OSM"""
    url = BASE_URL + "nsd/v1/ns_descriptors/" + package_id
    r = session.get(url)

    print(r.text)


#
# NS INSTANCES
#

def listNSInstances():
    """Lists all NS instances on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances"
    r = session.get(url)

    ns_instances = yaml.safe_load(r.text)
    ns_instances = {a["name"]: {"id": a["_id"], "state": a["nsState"]} for a in ns_instances}

    print("--------------------")
    print("All NS instances: ")
    for k in ns_instances:
        print("  " + k)
        print("  id    - " + ns_instances[k]["id"])
        print("  state - " + ns_instances[k]["state"])

    return ns_instances

def getNSInstanceInfo(id):
    """Gets NS instance info from OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + id
    r = session.get(url)

    print(r.text)

def createNSInstance(vim_acc_id, nsd_id, instance_name):
    """Creates NS instance on OSM (does not instantiate it)"""
    url = BASE_URL + "nslcm/v1/ns_instances"
    payload = {
        "vimAccountId": vim_acc_id,
        "nsdId": nsd_id, 
        "nsName": instance_name,
    }

    r = session.post(url, data=payload)

    instance = yaml.safe_load(r.text)
    instance_id = instance["id"]

    print("--------------------")
    print("Created NS instance: ")
    print("  name - " + instance_name)
    print("  id   - " + instance_id)
    print("  nsd  - " + nsd_id)

    return instance_id

def instantiateNSInstance(instance_id, vim_acc_id, instance_name):
    """Instantiates a given NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + instance_id + "/instantiate"
    payload = {
        "nsdId": instance_id,
        "vimAccountId": vim_acc_id,
        "nsName": instance_name,
    }

    r = session.post(url, data=payload)

    instance = yaml.safe_load(r.text)
    instance_id = instance["id"]

    print("--------------------")
    print("Instantiated NS instance: ")
    print("  name - " + instance_name)
    print("  id   - " + instance_id)

def buildNSInstance(vim_acc_id, nsd_id, instance_name):
    """Creates and instantiates NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances_content"
    payload = {
        "nsdId": nsd_id, 
        "vimAccountId": vim_acc_id,
        "nsName": instance_name,
    }

    r = session.post(url, data=payload)
    print(r.text)
    instance = yaml.safe_load(r.text)
    instance_id = instance["id"]

    print("--------------------")
    print("Created and instantiated NS instance: ")
    print("  name - " + instance_name)
    print("  id   - " + instance_id)

    return instance_id    

def terminateNSInstance(instance_id):
    """Terminates a given NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + instance_id + "/terminate"

    r = session.post(url)

    print("--------------------")
    print("Terminated NS instance: ")
    # print("  name - " + NAME)
    print("  id - " + instance_id)

def deleteNSInstance(instance_id):
    """Deletes a given NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + instance_id
    r = session.delete(url)

    print(r.text)

    print("--------------------")
    print("Deleted NS instance: ")
    print("  id - " + instance_id)

def waitForNSState(instance_name, state):
    """Waits for an instance to reach a certain state in OSM"""
    instances = listNSInstances()
    
    while(instances[instance_name]["state"] != state):
        print("--------------------")
        print("Waiting... " + instance_name + " is " + instances[instance_name]["state"] + ", need " + state)

        sleep(3)
        instances = listNSInstances()

        if instances[instance_name]["state"] == "BROKEN":
            print("--------------------")
            print("NS IS BROKEN")
            exit(1)

    print("--------------------")
    print("Done. " + instance_name + " is " + state)