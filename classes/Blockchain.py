import json
from hashlib import sha256
import os

def compute_hash(info:dict):
    info_string = json.dumps(info, sort_keys=True)
    return sha256(info_string.encode()).hexdigest()

class Blockchain:

    def __init__(self, MemoryApiInstance, Block):
        self.mem_api = MemoryApiInstance
        self.Block = Block
    
    # a method that compiles a blockchain from directory path
    def load(self, path_to_ledger):pass

    def append(self, block, fn): self.mem_api.save_json(block, fn)

    @property
    def last_block_added(self):
        os_dir = self.settings['ledger-dir']
        seq = [int(i.split('.json')[0]) for i in os.listdir(os_dir)]
        if len(seq) == 0: return False
        fn = max(seq)
        try:
            data = self.mem_api.load_json(os.path.join(os_dir, f"{fn}.json"))
            return data
        except IOError:
            logger.error("cannot load json required")
            return False

    # verifies proof of authorization
    def is_valid_authorized_entities(self, block): True

    # verify blocks for accurate work
    def is_valid_work(self, block): True

    def add_block(self, block): self.mem_api.write_json(block.__dict__, os.path.join(self.settings['ledger-dir'], f"{block.index}.json"))
    
    def publish_block(self, block):
        
        if self.is_valid_authorized_entities(block) is False: return False
        if self.is_valid_work(block) is False: return False
        self.add_block(block)
        return True
        
    def publish(self, transactions, worker_token:str):

        if not transactions: return {'success':False}
        last_block = self.last_block_added

        previous_hash = '0' if not last_block else last_block['hash']
        index = 0 if previous_hash == '0' else last_block['index']+1

        new_block = self.Block.Block(index
                                ,transactions
                                ,previous_hash)
        new_block.authorized_entities = last_block['authorized_entities']+[worker_token] if index > 0 and not worker_token in last_block['authorized_entities'] else [worker_token]
        new_block.hash = compute_hash(new_block.__dict__)
        if self.publish_block(new_block):
            return {'success':True, 'block':new_block}
        return {'success':False}
