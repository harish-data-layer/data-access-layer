import os
import sys

# Map of friendly names to file paths and class names
MODELS = {
    "1": {"name": "Vendors (Curated)", "file": "db/models/curated_vendor.py", "class": "CuratedVendor"},
    "2": {"name": "Invoices (Curated)", "file": "db/models/curated_invoice.py", "class": "CuratedInvoice"},
    "3": {"name": "Entities (Semantic)", "file": "db/models/entity.py", "class": "Entity"},
    "4": {"name": "Attributes (Semantic)", "file": "db/models/attribute.py", "class": "Attribute"},
    "5": {"name": "Business Rules", "file": "db/models/business_rule.py", "class": "BusinessRule"},
    "6": {"name": "DQ Scores", "file": "db/models/dq_score.py", "class": "DqScore"},
    "7": {"name": "Audit Logs", "file": "db/models/audit_log.py", "class": "DataAccessLog"},
}

TYPES = {
    "1": "String",
    "2": "Integer",
    "3": "Float",
    "4": "Boolean",
    "5": "DateTime"
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("=========================================")
    print("   TAI DATA API - EASY TABLE EDITOR")
    print("=========================================")
    print("Select a table to modify:")
    for key, val in MODELS.items():
        print(f"{key}. {val['name']}")
    
    choice = input("\nEnter number (e.g., 1): ")
    model = MODELS.get(choice)
    
    if not model:
        print("Invalid choice.")
        return

    print(f"\nEditing: {model['name']}")
    print("1. Add a new Column")
    # print("2. Remove a Column (Advanced - Edit file directly)") 
    action = input("Choose action (1): ")
    
    if action == "1" or action == "":
        col_name = input("Enter new column name (e.g., phone_number): ").strip()
        if not col_name:
            print("Invalid name.")
            return
            
        print("\nSelect Data Type:")
        print("1. Text (String)")
        print("2. Number (Integer)")
        print("3. Decimal (Float)")
        print("4. True/False (Boolean)")
        print("5. Date/Time")
        
        type_choice = input("Enter number (1): ") or "1"
        col_type = TYPES.get(type_choice, "String")
        
        # Construct the line to add
        # indent = "    "
        new_line = f"    {col_name} = Column({col_type}, nullable=True)\n"
        
        # Read file
        with open(model["file"], "r") as f:
            lines = f.readlines()
            
        # Insert before the last line (usually empty or internal usage)
        # or better, find the class definition and append at the end of it
        # Simple heuristic: Insert before the last "updatedAt" or at end of file
        # Creating a safe insertion point is tricky without AST.
        # Let's simple insert after 'id' if possible, or at the end of imports?
        # Best strategy: Find "class ClassName(Base):" and scroll down to last attribute.
        
        # Safer strategy for this specific codebase:
        # All models look like:
        # class Foo(Base):
        #    ...
        #    last_col = ...
        
        # We will iterate and find the class start, then look for the indentation end?
        # Let's just append before the last line if it's typically empty?
        # Or look for `    updatedAt = ...` and append before that? Most models have metadata fields at bottom.
        
        insert_idx = -1
        for i, line in enumerate(lines):
            if "updatedAt =" in line:
                insert_idx = i
                break
        
        if insert_idx == -1:
            # If no updatedAt, looking for createdAt
            for i, line in enumerate(lines):
                if "createdAt =" in line:
                    insert_idx = i
                    break
        
        if insert_idx == -1:
            # meaningful fallback: append to end of file, but indented
             insert_idx = len(lines)
             
        lines.insert(insert_idx, new_line)
        
        with open(model["file"], "w") as f:
            f.writelines(lines)
            
        print(f"\nSUCCESS: Added '{col_name}' to {model['file']}")
        print("Now running schema update...")
        
        # Call the update script
        import subprocess
        subprocess.call(["update_schema.bat", f"added {col_name} to {model['name']}"])

    else:
        print("Feature not implemented in wizard. Please edit file manually.")

if __name__ == "__main__":
    main()
