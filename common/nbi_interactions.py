import yaml
import requests
import urllib3

from time import sleep

#
# STATIC VARIABLES
#

BASE_URL = "https://10.255.28.33:9999/osm/"
CLUSTER_NAMESPACE = "2a6f15e7-cef8-4037-9423-74516a7ccfa8"

session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#
# TOKENS
#
def getToken(print_info=False):
    """Get token from OSM"""
    url = BASE_URL + "admin/v1/tokens"
    payload = {
        "username": "admin",
        "password": "admin"
    }
    r = session.post(url, data=payload)

    token = yaml.safe_load(r.text)["id"]

    if print_info:    
        print("--------------------")
        print("Got token: " + token)

    return token

def deleteToken(token=None, print_info=False):
    """Deletes current token from OSM"""
    url = BASE_URL + "admin/v1/tokens" if token == None else BASE_URL + "admin/v1/tokens/" + token
    r = session.delete(url)

    token = r.text.split(" ")[2].replace("\'", "")
    
    if print_info:    
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

def listVIMAccounts(print_info=False):
    """Lists all VIM accounts from OSM"""
    url = BASE_URL + "admin/v1/vim_accounts"
    r = session.get(url)

    vim_accounts = yaml.safe_load(r.text)
    vim_accounts = {a["name"]: a["_id"] for a in vim_accounts}

    if print_info:
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

    return r.text

#
# K8S CLUSTERS
#

def listK8SClusters():
    """Lists all available K8s Clusters from OSM"""
    url = BASE_URL + "admin/v1/k8sclusters"
    r = session.get(url)

    k8s_clusters = yaml.safe_load(r.text)
    k8s_clusters = {a["name"]: a["_id"] for a in k8s_clusters}

    print("--------------------")
    print("All K8s Clusters: ")
    for k in k8s_clusters:
        print("  " + k)
        print("  id - " + k8s_clusters[k])
    
    return k8s_clusters

def getK8SClusterInfo(cluster_id):
    """Gets K8s cluster info from OSM"""
    url = BASE_URL + "admin/v1/k8sclusters/" + cluster_id
    r = session.get(url)

    return r.text

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

    return r.text

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

    return r.text


#
# NS INSTANCES
#

def listNSInstances(print_info=False):
    """Lists all NS instances on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances"
    r = session.get(url)

    ns_instances = yaml.safe_load(r.text)
    ns_instances = {a["_id"]: {"name": a["name"],
                                "state": a["nsState"],
                                "nsd_name": a["nsd-name-ref"],
                                "nsd_id": a["nsd-id"]
                            } for a in ns_instances}

    if print_info:
        print("--------------------")
        print("All NS instances: ")
        for k in ns_instances:
            print("  " + k)
            print("  name  - " + ns_instances[k]["name"])
            print("  state - " + ns_instances[k]["state"])

    return ns_instances

def getNSInstanceInfo(id):
    """Gets NS instance info from OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + id
    r = session.get(url)

    return r.text

def createNSInstance(vim_acc_id, nsd_id, instance_name):
    """Creates NS instance on OSM (does not instantiate it)"""
    url = BASE_URL + "nslcm/v1/ns_instances"
    payload = {
        "vimAccountId": vim_acc_id,
        "nsdId": nsd_id, 
        "nsName": instance_name,
        "k8s-namespace": CLUSTER_NAMESPACE,
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
        "k8s-namespace": CLUSTER_NAMESPACE,
    }

    r = session.post(url, data=payload)

    instance = yaml.safe_load(r.text)
    instance_id = instance["id"]

    print("--------------------")
    print("Instantiated NS instance: ")
    print("  name - " + instance_name)
    print("  id   - " + instance_id)

def terminateNSInstance(instance_id):
    """Terminates a given NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + instance_id + "/terminate"

    r = session.post(url)

    print("--------------------")
    print("Terminating NS instance: ")
    # print("  name - " + NAME)
    print("  id - " + instance_id)

def deleteNSInstance(instance_id):
    """Deletes a given NS instance on OSM"""
    url = BASE_URL + "nslcm/v1/ns_instances/" + instance_id
    r = session.delete(url)

    print("--------------------")
    print("Deleted NS instance: ")
    print("  id - " + instance_id)

def waitForNSState(ns_id, state):
    """Waits for an instance to reach a certain state in OSM"""
    instances = listNSInstances()
    
    tries = 0
    while(instances[ns_id]["state"] != state and tries < 10):
        tries += 1
        print("--------------------")
        print("Waiting... " + instances[ns_id]["name"] + " is " + instances[ns_id]["state"] + ", need " + state + " (" + str(tries) + "/10)")

        sleep(8)
        instances = listNSInstances()

        if instances[ns_id]["state"] == "BROKEN":
            print("--------------------")
            print("NS IS BROKEN")
            deleteToken()
            exit(1)

    print("--------------------")
    print("Done. " + instances[ns_id]["name"] + " is " + state)