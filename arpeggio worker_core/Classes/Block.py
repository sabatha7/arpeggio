

class Block:

    def __init__(self, index, transactions, timestamp, previous_hash, authorized_entities):
        self.previous_hash = previous_hash
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.authorized_entities = authorized_entities
