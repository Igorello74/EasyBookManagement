from core.bulk_operations import BulkManager
from core.factory import ObjectFactory

def format_currency(val):
    if val is None: return 0
    val = int(val)
    return f"{val:,}".replace(",", " ")