from db.base import SessionLocal
from db.models.test import PromotedVendor
import traceback

with open('full_error.txt', 'w') as f:
    try:
        db = SessionLocal()
        v = PromotedVendor(vendor_id='test_err', sap_code='test_err', name='test_err')
        db.add(v)
        db.commit()
    except Exception:
        f.write(traceback.format_exc())
    finally:
        db.close()
