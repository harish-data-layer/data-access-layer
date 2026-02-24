from db.base import engine
from sqlalchemy import inspect
import json

inspector = inspect(engine)
cols = inspector.get_columns('lfa1', schema='sap')
print(json.dumps([c['name'] for c in cols], indent=2))
