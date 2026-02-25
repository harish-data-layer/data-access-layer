import os
import sys
import re

# Add the project root to the path so it can find the 'db' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
from db.config import TABLE_CONFIGS

load_dotenv()

def sync_db_and_models():
    """
    Magic script to:
    1. Add missing columns to the Cloud DB based on config.py
    2. Update SQLAlchemy models (sap_tables.py) to match config.py
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    inspector = inspect(engine)
    
    print("\n--- Starting Auto-Sync ---")
    
    # 1. UPDATE DATABASE SCHEMA
    with engine.connect() as conn:
        for table_name, columns in TABLE_CONFIGS.items():
            db_cols = [c["name"].lower() for c in inspector.get_columns(table_name, schema="sap")]
            
            for col in columns:
                col_name = col["name"]
                if col_name.lower() not in db_cols:
                    print(f"Adding new column [{col_name}] to table [sap.{table_name}]...")
                    # Map config types to Postgres types
                    pg_type = "VARCHAR(255)"
                    if "Integer" in col["type"]: pg_type = "INTEGER"
                    if "Float" in col["type"]: pg_type = "DOUBLE PRECISION"
                    if "Date" in col["type"]: pg_type = "DATE"
                    
                    try:
                        conn.execute(text(f"ALTER TABLE sap.{table_name} ADD COLUMN {col_name} {pg_type};"))
                        conn.commit()
                        print(f"✅ Database updated: sap.{table_name}.{col_name}")
                    except Exception as e:
                        print(f"❌ Error adding column: {e}")

    # 2. UPDATE MODELS (sap_tables.py)
    # This part updates the Python code itself!
    model_path = os.path.join("db", "models", "sap_tables.py")
    with open(model_path, "r") as f:
        content = f.read()

    for table_name, columns in TABLE_CONFIGS.items():
        class_name = table_name.upper()
        # Find the class block
        class_pattern = rf"class {class_name}\(Base\):.*?(?=class|\Z)"
        match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            existing_block = match.group(0)
            new_cols_code = ""
            for col in columns:
                if f"{col['name']} = Column" not in existing_block:
                    type_str = col["type"]
                    new_cols_code += f"    {col['name']} = Column({type_str})\n"
            
            if new_cols_code:
                # Insert before the first relationship or at the end of the class
                if "relationship(" in existing_block:
                    updated_block = existing_block.replace("    company_codes", new_cols_code + "    company_codes")
                    updated_block = updated_block.replace("    purchase_orders", new_cols_code + "    purchase_orders")
                    updated_block = updated_block.replace("    line_items", new_cols_code + "    line_items")
                else:
                    updated_block = existing_block + new_cols_code
                
                content = content.replace(existing_block, updated_block)

    with open(model_path, "w") as f:
        f.write(content)
    
    print("--- Auto-Sync Complete: DB and Models are perfectly matched! ---\n")

if __name__ == "__main__":
    sync_db_and_models()
