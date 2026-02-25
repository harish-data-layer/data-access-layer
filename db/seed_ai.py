import os
import sys
from sqlalchemy import text

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import SessionLocal, engine, Base
from db.models.ai_layers import SemanticLayer, AiCuratedLayer, IntegrationPull, IntegrationPush, PublicCloudLayer

def seed_ai_layers():
    db = SessionLocal()
    print("\n--- Seeding AI Layer Metadata ---")
    
    try:
        # Step 0: Ensure AI Schema and Tables Exist
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai;"))
            conn.commit()
            
        print("Creating AI tables...")
        Base.metadata.create_all(bind=engine)
        
        # Step 1: Seed Semantic Layer
        print("Seeding Layer-1 (Semantic)...")
        semantic_data = [
            SemanticLayer(ENTITY="Vendor", ATTRIBUTE="Vendor Code", DESCRIPTION="Unique ID for vendor", RULE="Starts with V", DATA_TYPE="String", IS_MANDATORY="Y", SENSITIVITY="Public", OWNER="Procurement"),
            SemanticLayer(ENTITY="Invoice", ATTRIBUTE="Invoice Amount", DESCRIPTION="Total tax amount", RULE="Must be > 0", DATA_TYPE="Float", IS_MANDATORY="Y", SENSITIVITY="Internal", OWNER="Finance"),
            SemanticLayer(ENTITY="PurchaseOrder", ATTRIBUTE="PO Date", DESCRIPTION="Order creation date", RULE="Not in future", DATA_TYPE="Date", IS_MANDATORY="Y", SENSITIVITY="Public", OWNER="Procurement")
        ]
        db.add_all(semantic_data)
        
        # Step 2: Seed AI Curated Layer
        print("Seeding Layer-2 (AI-Curated)...")
        curated_data = [
            AiCuratedLayer(SEMANTIC_ATTR="Vendor Code", CURATED_COL="vnd_id", DATA_TYPE="String", TRANSFORM="Standardize format", QUALITY_RULE="Check master list", IS_AI_READY=True),
            AiCuratedLayer(SEMANTIC_ATTR="Invoice Amount", CURATED_COL="inv_total", DATA_TYPE="Float", TRANSFORM="Currency conversion", QUALITY_RULE="Bound check", IS_AI_READY=True)
        ]
        db.add_all(curated_data)
        
        # Step 3: Seed Integration Pull
        print("Seeding Layer-3A (Integration-Pull)...")
        pull_data = [
            IntegrationPull(CURATED_COL="vnd_id", SOURCE_SYS="SAP", SAP_OBJ="LFA1", FIELD="LIFNR", EXTRACTION="Daily Job", IS_INCREMENTAL=True, PURPOSE="Sync Vendor Master"),
            IntegrationPull(CURATED_COL="inv_total", SOURCE_SYS="SAP", SAP_OBJ="RBKP", FIELD="RMWWR", EXTRACTION="Real-time", IS_INCREMENTAL=True, PURPOSE="Financial analysis")
        ]
        db.add_all(pull_data)
        
        # Step 4: Seed Integration Push
        print("Seeding Layer-3B (Integration-Push)...")
        push_data = [
            IntegrationPush(CURATED_COL="vnd_id", TARGET_SYS="CRM", SAP_MODULE="FI", INTERFACE="REST API", FIELD="ExtVendorId", SAP_OBJ="LFA1", TRIGGER_COND="On Create", PURPOSE="Sync to sales"),
        ]
        db.add_all(push_data)

        # Step 5: Seed Public Cloud Layer
        print("Seeding Layer-3 (Public Cloud)...")
        cloud_data = [
            PublicCloudLayer(PROVIDER="AWS", SERVICE="S3", RESOURCE_NAME="tai-data-bucket", DATA_LOC="us-east-1", ACCESS_LEVEL="Admin"),
            PublicCloudLayer(PROVIDER="Azure", SERVICE="Blob Storage", RESOURCE_NAME="taidatastore", DATA_LOC="West US", ACCESS_LEVEL="Read-Write"),
        ]
        db.add_all(cloud_data)
        
        db.commit()
        print("--- AI Seeding Complete ---")
        
    except Exception as e:
        print(f"Error seeding AI data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_ai_layers()
