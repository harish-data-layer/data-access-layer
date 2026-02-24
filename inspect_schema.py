from db.base import engine
from sqlalchemy import inspect
import json

inspector = inspect(engine)
tables = ['_sync_state', 'promoted_vendors', 'promoted_invoices', 'promoted_inventory', 'promoted_purchase_orders']
result = {}

for t in tables:
    try:
        cols = inspector.get_columns(t, schema='ai')
        result[t] = [c['name'] for c in cols]
    except Exception as e:
        result[t] = str(e)

with open('schema_info.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)
