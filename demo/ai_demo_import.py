import os
import sys
import pandas as pd

# Add parent directory to path to import hybrid_orm module
project_root = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from hybrid_orm.config_db import engine, Base
from sqlalchemy import text

excel_path = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api\demo\AI DEMO FILE.xlsx"

def run_demo_import():
    print(f"Loading data from {excel_path}...")
    
    # 1. Read the Detailed Order Book sheet. 
    # Use header=1 to skip the first row (the title "DETAILED ORDER BOOK")
    df = pd.read_excel(excel_path, sheet_name="DETAILED ORDER BOOK", header=1)
    
    # Optional: Fill empty cells. For order book we might just want to forward fill certain columns like Sales Order No or just handle NaNs
    # For now, replacing NaNs with None so it translates to NULL in postgres
    df = df.where(pd.notnull(df), None)
    
    # 2. Clean column names to be database friendly
    # e.g. "Sales Order No" -> "sales_order_no", "Weight Per Piece (Kg)" -> "weight_per_piece_kg"
    clean_columns = []
    for col in df.columns:
        clean = str(col).strip().lower()
        clean = clean.replace(' ', '_')
        clean = clean.replace('(', '').replace(')', '')
        clean = clean.replace('-', '_')
        clean_columns.append(clean)
    
    df.columns = clean_columns
    
    # Total records to import
    total_records = len(df)
    print(f"Found {total_records} records to insert.")
    print("Columns:", df.columns.tolist())
    
    # 3. Store in PostgreSQL using Pandas to_sql mapping it to hybrid_orm schema
    # chunksize=100 ensures we load 100 records at a time per batch
    table_name = "ai_demo"
    schema_name = "hybrid_orm"
    
    print(f"Storing into {schema_name}.{table_name} table in batches of 100...")
    
    with engine.begin() as conn:
        # Create schema if it somehow doesn't exist
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        
    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema_name,
        if_exists='replace', # For demo purposes, we replace the table
        index=False,
        chunksize=100
    )
    
    print("Data successfully loaded!")
    
    # 4. Verify the insertion
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{table_name}"))
        count = result.scalar()
        print(f"Verified! Database contains {count} rows in {schema_name}.{table_name}.")

if __name__ == "__main__":
    run_demo_import()
