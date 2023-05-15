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


if __name__ == "__main__":
    main()