import requests, random
from time import sleep

session = requests.Session()
session.verify = False

def main():
    while True:
        sleep(random.randint(1, 10))
        r = session.get("https://localhost:8000/listener/countdown")
        print(r.text)

if __name__ == "__main__":
    main()