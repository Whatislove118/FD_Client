from email.policy import default
import string
from sys import stderr, stdout
import requests
from dataclasses import dataclass
import os
import random
import json
from dotenv import load_dotenv

load_dotenv()

def prettyprint_json(raw_json: str, file=stdout):
    parsed = json.loads(raw_json)
    print(json.dumps(parsed, indent=4, sort_keys=True), file=file)

@dataclass
class Config:
    host = os.getenv("REMOTE_HOST", "localhost")
    default_username = os.getenv("AUTH_USERNAME")   
    default_password = os.getenv("AUTH_PASSWORD") 


class Request:
    credentials: dict = {}
    
    @classmethod
    def authorize_requests(cls, url, username, password):
        data = {"username": username, "password": password}
        response = cls.send_request(url=url, data=data)
        if response.status_code != 200:
            print("Bad credentials")
            os.system.exit(127)
        token = response.json().get("access_token")
        print("Login in")
        cls.credentials = {"Authorization" : f"Bearer {token}"}
    
    @classmethod
    def send_request(cls, url, method="post", *args, **kwargs):
        try:
            requests_func = getattr(requests, method)
        except AttributeError:
            print("[PROGRAMMING ERROR] Wrong type of requests method", file=stderr)
        response = requests_func(url, *args, **kwargs, headers=cls.credentials) 
        return response
        

def auth():
    print("Enter username: (pass empty for default)")

    username = input()
    if username == '':
        username = Config.default_username

    print("Enter password: (pass empty for default)")
    password = input()
    if password == '':
        password = Config.default_password
    Request.authorize_requests(
        url=Config.host + "/api/auth/login/",
        username=username,
        password=password,
    )


def create_task():
    while True:
        try:
            print("Enter filename")
            filepath = input()
            if not os.path.exists(filepath):
                raise Exception()
        except:
            print("Wrong file path", file=stderr)
            continue
        break
    file = open(filepath,'rb')
    
    print("Enter jenkins user(pass empty for random)")
    jenkins_user = input()
    if jenkins_user is None:
        jenkins_user = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    response = Request.send_request(
        url=Config.host + "/api/tasks/",
        files={"file": file},
        data={"jenkins_user": jenkins_user},
    )

    if response.status_code == 201:
        print("Task created")
    else:
        print(f"Bad request")
    prettyprint_json(response.text)


def list_task():
    response = Request.send_request(
        url=Config.host + "/api/tasks/",
        method="get"
    )
    prettyprint_json(response.text)


def get_task():
    print("Enter task id")
    task_id = int(input())
    response = Request.send_request(
        url=Config.host + f"/api/tasks/{task_id}",
        method="get"
    )
    if response.status_code == 200:
        print("OK")
        prettyprint_json(response.text)
    else:
        print("Not found")


def main():
    action_association = {
        1: create_task,
        2: list_task,
        3: get_task
    }
    print("Auth process")
    auth()
    while True:

        print(
            "Choose action:\n" \
            "1. Create task\n" \
            "2. List tasks\n" \
            "3. Get tasks\n"    
        )
        try:
            action = action_association[int(input())]
        except:
            print("Wron command type.", file=stderr)
            continue
        action()


if __name__ == "__main__":
    main()
