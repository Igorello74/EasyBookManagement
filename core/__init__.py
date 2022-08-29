from core.bulk_operations import BulkManager
from core.factory import ObjectFactory

def format_currency(val):
    val = int(val)
    return f"{val:,}".replace(",", " ")