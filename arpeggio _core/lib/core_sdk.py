import requests

u = {}

def configure(configuration:dict):
    u = configuration

def minify_blockchain_copy(url:str,data:dict):
    data['configuration'] = u
    return requests.post(url, data).json()
