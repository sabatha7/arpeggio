import requests

u = {}

def configure(configuration:dict):
    u = configuration

def fetch_latest_pipeline_feed(endpoint:str,data:dict):
    data['configuration'] = u
    return requests.post(endpoint, data).json()

def notify_latest_work(endpoint:str,data:dict):
    data['configuration'] = u
    return requests.post(endpoint, data).json()
