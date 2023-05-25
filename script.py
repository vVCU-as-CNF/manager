from time import sleep
from kubernetes import client, config

from manager.nbi_interactions import *
from manager.k8s_interactions import *

#
# STATIC VARIABLES
#

# OSM
VIM_ACCOUNT_1 = "Jarvis"
VIM_ACCOUNT_2 = "Jarvis2"

CLUSTER_1 = "vvcu_k8s_cluster_1"
CLUSTER_2 = "vvcu_k8s_cluster_2"

# creating a new NS instance
INSTANCE_NAME = "nbi-test" # instance name
NSD_NAME = "vvcu-as-acnf_ns" # descriptor name

# K8S
CLUSTER_NAMESPACE = "pi-vvcu" # "2a6f15e7-cef8-4037-9423-74516a7ccfa8"

#
# MAIN
#
def main():
    # load 1st cluster
    vim_acc = VIM_ACCOUNT_2
    config.load_kube_config(config_file="manager/clusters/kubelet1.config")
    k8s_api = client.CoreV1Api()
    
    getToken()

    # create 1st ns instance (the one to be migrated)
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages(print_info=True)
    # k8s_clusters = listK8SClusters()

    instance1_id = createNSInstance(vim_accounts[vim_acc], ns_packages[NSD_NAME], INSTANCE_NAME + "1")

    waitForNSState(instance1_id, "NOT_INSTANTIATED")
    instantiateNSInstance(instance1_id, vim_accounts[vim_acc], INSTANCE_NAME + "1")

    # waitForNSState(INSTANCE_NAME + "1", "READY")
    # waitForPodReady(k8s_api, CLUSTER_NAMESPACE)

    # # load 2nd cluster
    # cluster = vvcu_k8s_cluster_2
    # config.load_kube_config(config_file="kubelet2.config")
    # k8s_api = client.CoreV1Api()
    
    # # create 2nd ns instance (the one to migrate to)
    # vim_accounts = listVIMAccounts()
    # ns_packages = listNSPackages(print_info=True)

    # instance2_id = createNSInstance(vim_accounts[vim_acc], ns_packages[NSD_NAME], INSTANCE_NAME + "2")

    # waitForNSState(INSTANCE_NAME + "2", "NOT_INSTANTIATED")
    # instantiateNSInstance(instance2_id, vim_accounts[vim_acc], INSTANCE_NAME + "2")

    # waitForNSState(INSTANCE_NAME + "2", "READY")
    # waitForPodReady(k8s_api, CLUSTER_NAMESPACE)

    # # when 2nd ns instance is ready, delete 1st ns instance
    # cluster = vvdu_k8s_cluster_1

    # waitForNSState(INSTANCE_NAME + "1", "READY")
    # terminateNSInstance(instance1_id)

    # waitForNSState(INSTANCE_NAME + "1", "NOT_INSTANTIATED")
    # deleteNSInstance(instance1_id)

    deleteToken()


if __name__ == "__main__":
    main()