

class Block:

    def __init__(self, index, transactions, previous_hash):
        self.previous_hash = previous_hash
        self.index = index
        self.transactions = transactions
