from time import sleep

def waitForPodReady(api, namespace):
    """Using K8s api, waits for a pod to be ready (pass its health check)"""
    tries = 0
    while(tries < 20):
        tries += 1


        pods = api.list_namespaced_pod(namespace)
        pod = pods.items[0]
        pod = api.read_namespaced_pod(pod.metadata.name, namespace)

        for condition in pod.status.conditions:
            if condition.type == "Ready" and condition.status == "True":
                print("--------------------")
                print("Done. Pod is ready")
                return
            
        print("--------------------")
        print("Waiting... Pod is not ready. Try " + str(tries) + "/20")

        sleep(3)

    print("--------------------")
    print("Exceeded max tries")
    exit(1)