from time import sleep
from kubernetes import client, config

from nbi_interactions import *
from k8s_interactions import *




#
# STATIC VARIABLES
#

VIM_ACCOUNT_1 = "5gasp-k8s-1"
VIM_ACCOUNT_2 = "5gasp-k8s-2"

NS_PACKAGE_NAME = "vvcu-as-cnf_ns"

# creating a new NS instance
INSTANCE_NAME = "nbi-test" # instance name
NSD_NAME = "vvcu-as-acnf_ns" # descriptor name

#
# MAIN
#
def main():
    vim_acc = VIM_ACCOUNT_2
    
    getToken()
    
    vim_accounts = listVIMAccounts()
    ns_packages = listNSPackages(print_info=True)

    instance_id = createNSInstance(vim_accounts[vim_acc], ns_packages[NSD_NAME], INSTANCE_NAME)
    

    waitForState(INSTANCE_NAME, "NOT_INSTANTIATED")
    instantiateNSInstance(instance_id, vim_accounts[vim_acc], INSTANCE_NAME)

    waitForState(INSTANCE_NAME, "READY")
    getNSInstanceInfo(instance_id)

    sleep(10)
    getNSInstanceInfo(instance_id)
    
    # waitForState(INSTANCE_NAME, "READY")
    # terminateNSInstance(instance_id)

    # waitForState(INSTANCE_NAME, "NOT_INSTANTIATED")
    # deleteNSInstance(instance_id)

    deleteToken()

def waitForState(instance_name, state):
    """Waits for an instance to reach a certain state in OSM"""
    instances = listNSInstances()
    
    while(instances[instance_name]["state"] != state):
        print("--------------------")
        print("Waiting... " + instance_name + " is " + instances[instance_name]["state"] + ", need " + state)

        sleep(3)
        instances = listNSInstances()

    print("--------------------")
    print("Done. " + instance_name + " is " + state)

if __name__ == "__main__":
    main()