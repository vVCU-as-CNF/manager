from time import sleep
from kubernetes import client, config

from nbi_interactions import *
from k8s_interactions import *

#
# STATIC VARIABLES
#

# OSM
VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"

# creating a new NS instance
INSTANCE_NAME = "nbi-test" # instance name
NSD_NAME = "vvcu-as-acnf_ns" # descriptor name

# K8S
CLUSTER_NAMESPACE = "99df5250-1cec-49f5-aba8-25017a9aadb7"

#
# MAIN
#
def main():
    # load 1st vim
    vim_acc = VIM_ACCOUNT_1
    config.load_kube_config(config_file="kubelet1.config")
    k8s_api = client.CoreV1Api()
    
    getToken()

    # create 1st ns instance (the one to be migrated)
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages(print_info=True)

    instance1_id = createNSInstance(vim_accounts[vim_acc], ns_packages[NSD_NAME], INSTANCE_NAME + "1")

    waitForNSState(INSTANCE_NAME + "1", "NOT_INSTANTIATED")
    instantiateNSInstance(instance1_id, vim_accounts[vim_acc], INSTANCE_NAME + "1")

    waitForNSState(INSTANCE_NAME + "1", "READY")
    waitForPodReady(k8s_api, CLUSTER_NAMESPACE)

    # load 2nd vim
    vim_acc = VIM_ACCOUNT_2
    config.load_kube_config(config_file="kubelet2.config")
    k8s_api = client.CoreV1Api()
    
    # create 2nd ns instance (the one to migrate to)
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages(print_info=True)

    instance2_id = createNSInstance(vim_accounts[vim_acc], ns_packages[NSD_NAME], INSTANCE_NAME + "2")

    waitForNSState(INSTANCE_NAME + "2", "NOT_INSTANTIATED")
    instantiateNSInstance(instance2_id, vim_accounts[vim_acc], INSTANCE_NAME + "2")

    waitForNSState(INSTANCE_NAME + "2", "READY")
    waitForPodReady(k8s_api, CLUSTER_NAMESPACE)

    # when 2nd ns instance is ready, delete 1st ns instance
    vim_acc = VIM_ACCOUNT_1

    waitForNSState(INSTANCE_NAME + "1", "READY")
    terminateNSInstance(instance1_id)

    waitForNSState(INSTANCE_NAME + "1", "NOT_INSTANTIATED")
    deleteNSInstance(instance1_id)

    deleteToken()


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

def waitForPodReady(api, namespace):
    """Using K8s api, waits for a pod to be ready (pass its health check)"""
    tries = 0
    while(tries < 20):
        tries += 1

        print("--------------------")
        print("Waiting... Pod is not ready. Try " + str(tries) + "/20")
        pods = api.list_namespaced_pod(namespace)
        pod = pods.items[0]
        pod = api.read_namespaced_pod(pod.metadata.name, namespace)

        for condition in pod.status.conditions:
            if condition.type == "Ready" and condition.status == "True":
                print("--------------------")
                print("Done. Pod is ready")
                return
            
        sleep(3)

    print("--------------------")
    print("Exceeded max tries")
    exit(1)


if __name__ == "__main__":
    main()