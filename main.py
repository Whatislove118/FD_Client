from requests_toolbelt.multipart import encoder
import string
from sys import stderr, stdout
import time
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
            return
        token = response.json().get("access_token")
        print("Login in")
        cls.credentials = {"Authorization" : f"Bearer {token}"}
        return token
    
    @classmethod
    def send_request(cls, url, method="post", headers=None, *args, **kwargs):
        if headers:
            headers = dict(headers, **cls.credentials)
        else:
            headers = cls.credentials
        
        try:
            requests_func = getattr(requests, method)
        except AttributeError:
            print("[PROGRAMMING ERROR] Wrong type of requests method", file=stderr)
        response = requests_func(url, *args, **kwargs, headers=headers) 
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
    
    token = Request.authorize_requests(
        url=Config.host + "/api/auth/login/",
        username=username,
        password=password,
    )
    if not token:
        auth()


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
    if jenkins_user == '':
        jenkins_user = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    start = time.monotonic()
    data = {"jenkins_user": jenkins_user}
    response = Request.send_request(
        url=Config.host + "/api/tasks/",
        files={"file": file},
        data=data,
    )
    total_time = time.monotonic() - start
    print(f"Total time - {total_time}")

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
        3: get_task,
        4: auth
    }
    print("Auth process")
    auth()
    while True:

        print(
            "Choose action:\n" \
            "1. Create task\n" \
            "2. List tasks\n" \
            "3. Get tasks\n"
            "4. Logout"    
        )
        try:
            action = action_association[int(input())]
        except:
            print("Wron command type.", file=stderr)
            continue
        action()


if __name__ == "__main__":
    main()
