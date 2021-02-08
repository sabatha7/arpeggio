

class Blockchain:

    def __init__(self, MemoryApiInstance):
        self.mem_api = MemoryApiInstance
    
    # a method that compiles a blockchain from directory path
    def load(self, path_to_ledger):
        pass

    def append(self, block):pass

    @property
    def last_block_added(self):
        return ''

    # todo::
    @property
    def network_lag(self, block): return 60

    # todo:: appends to the block best known nodes
    def proof_of_authorized_entities(self, block):
        pass

    # verifies proof of authorization
    def is_valid_authorized_entities(self, block):
        True
    
    def add_block(self, block):
        last_block = self.last_block_added
        previous_hash = '0' if last_block.id == -1 else last_block.hash

        if previous_hash != block.previous_hash: return False
        if not self.is_valid_authorized_entities(block): return False

        # todo::call to memoryapi, linked list struct
        self.append(block)
        return True

    def compile_authorized_entities(self, last_block, auth = []):
        if 'deauthorization' in last_block.__dict__.keys(): return [i for i in last_block.authorized_entities if not i in last_block.deauthorized_entities]
        else: return auth
        
    def mine(self, transactions, worker_token):

        if not transactions: return False
        last_block = self.last_block_added
        previous_hash = '0' if last_block.id == -1 else last_block.hash
        index = 0 if previous_hash == '0' else last_block.id+1
        # ct stores current time 
        ct = datetime.datetime.now() 
        # ts store timestamp of current time 
        ts = ct.timestamp()
        new_block = Block.Block(index
                                ,transactions
                                ,ts
                                ,previous_hash)
        proof_of_authorized_entities = last_block.authorized_entities
        new_block.authorized_entities = compile_authorized_entities(last_block, [worker_token])
        new_block.hash = compute_hash(new_block)
        #self.add_block(new_block)
        return new_block
