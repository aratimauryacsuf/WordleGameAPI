import requests 
import dataclasses
import httpx
from redis import Redis
from rq import Queue

#need edit
def send_score(data):
    try:
        response = httpx.post(data["url"], json={'username':data["username"], "game_status": data["outcome"], "guess_count": data["guess_num"]})
        success = True
        print("client registration successful") 
    except Exception as e:
        print(f"service registration failed")
    return 0



