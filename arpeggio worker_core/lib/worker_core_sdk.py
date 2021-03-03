import requests

def fetch_latest_pipeline_feed(endpoint:str, config:dict, data:dict):
    data['access-token'] = config['access-token']
    return requests.post(endpoint, data).json()

def notify_latest_work(endpoint:str, config:dict, data:dict, reason='broadcast'):
    data['access-token'] = config['access-token']
    data['reason'] = reason
    return requests.post(endpoint, data).json()

def minify_blockchain_copy(url:str,data:dict):
    data['configuration'] = u
    return requests.post(url, data).json()
