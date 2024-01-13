import requests
import time

credentials = {}


def getcredentials():
    credentials.setdefault("username", "Vvyibaba")
    credentials.setdefault("password", "ffggffgg")


class tokenobj:
    def __init__(self):
        self.token = 0
        self.timestamp = 0


token = tokenobj()


def tokenacq():
    if token.token == 0 or time.monotonic()-token.timestamp >= 3600:
        locreq = requests.put(
            "https://api.mangaupdates.com/v1/account/login", data=credentials)
        if locreq.ok:
            print(locreq.json()["context"]["session_token"])


getcredentials()
tokenacq()
