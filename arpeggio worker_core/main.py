import json
import time
import requests
from hashlib import sha256
import datetime
from lib import worker_core_sdk
import os
from Enums import Enums
from Classes import Block
from Classes import Memory
from Classes import Blockchain
from hashlib import sha256

secret_key = os.urandom(24)
domain = 'localhost::5001'
worker_core_sdk.configure({'access-token':secret_key,
                           'domain':domain})

settings_file = os.path.join("settings.json")
mem = Memory.StorageAPI(json)
app_settings = mem.load_json(settings_file)

bc = Blockchain.Blockchain(mem)


def compute_hash(info={}):
    info_string = json.dumps(info, sort_keys=True)
    return sha256(info_string.encode()).hexdigest()

def verify_worker():pass # verify nodes

class Worker:
    def run(self):
        while True:
            feed_endpoint = 'http://localhost:5000/latest-pipeline-feed'
            feed = self.feed(feed_endpoint)
            if len(feed.keys()):
                print(feed)
                r = self.publish(feed['data'])
                #if r['success']: print(f"{r['block']['id']]} was published")
                #else:
                #    self.update(r['consensus'])
                #    print(f"{len(r['consensus'])} block updates")
            time.sleep(60)
            self.clear() # given data for outdated nodes

    def publish(self, transactions):
        #bc.mine(transactions)
        #r = self.send_request()
        return ''

    def feed(self, endpoint):
        r = self.send_request(endpoint, {})
        return r

    def send_request(self, endpoint:str, transaction:dict):
        r = worker_core_sdk.fetch_latest_pipeline_feed(endpoint, data=transaction)
        return r

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
