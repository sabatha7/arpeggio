import enum

class TransactionType(enum.Enum):
    MINT = 0
    PURCHASE = 1
    SPEND = 2
    REFUND = 3
    TRANSFER = 4
