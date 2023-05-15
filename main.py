from fastapi import FastAPI

app = FastAPI()

CONFIG1 = "clusters/kubelet1.config"
CONFIG2 = "clusters/kubelet2.config"



@app.get("/")
def read_root():
    return {"Hello": "World"}
