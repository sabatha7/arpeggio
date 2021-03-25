import sys
sys.path.append("..") # Adds higher directory to python modules path.

import os
import time
import json
import requests

from lib import worker_core_sdk
from classes import Block
from classes import Memory
from classes import Blockchain

configure = {'access-token':os.environ.get('ACCESS_TOKEN')}

settings_file = os.path.join("settings.json")
mem = Memory.StorageAPI(json)

feed_endpoint = 'https://sircoin.org/latest-pipeline-feed/'
broadcast_endpoint = 'https://sircoin.org/latest-pipeline-broadcast/'

bc = Blockchain.Blockchain(mem, Block)
bc.settings = mem.load_json(settings_file)

class Worker:
    def run(self):
        
        while True:
            feed = {}

            try:feed = self.feed(feed_endpoint)
            except IOError as e:
                print('waiting for host...')
                print(e)
                continue

            if len(feed.keys()):
                r = self.publish([feed['data'][i] for i in feed['data'].keys() if not i == 'success'])
                print(r)
                if r['success']:
                    print(f"block {r['block'].index} published")
                    try: self.broadcast(r['block'].__dict__)
                    except IOError: continue
                else: print('awaiting')
            time.sleep(60) # point of delay
            self.clear()

    def feed(self, endpoint:str): return self.send_request(endpoint,{})

    def send_request(self, endpoint:str, transaction:dict, reason=None):
        r = worker_core_sdk.fetch_latest_pipeline_feed(endpoint, configure, data=transaction) if not transaction.keys() else worker_core_sdk.notify_latest_work(endpoint, configure, data=transaction)
        return r

    def publish(self, transactions): return bc.publish(transactions, configure['access-token'])

    def broadcast(self, block:dict): return self.send_request(broadcast_endpoint, {block['index']:[i['paymentID'] for i in block['transactions']]})

    def clear(self):

        # for windows
        if os.name == 'nt':
            _ = os.system('cls')

        # for mac and linux(here, os.name is 'posix')
        else:
            _ = os.system('clear')

if __name__ == "__main__":
    worker = Worker()
    worker.run()
