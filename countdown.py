import requests, random
from time import sleep

session = requests.Session()
session.verify = False

def main():
    while True:
        r = session.get("http://localhost:8000/listener/countdown")
        print(r.text)
        sleep(random.randint(1, 10))

if __name__ == "__main__":
    main()