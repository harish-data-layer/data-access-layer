import openpyxl
import os
import re

file_path = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api\db\20260108 - VIM DataDictionary (1).xlsx"
output_file = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api\db\models\ai_layers.py"

def clean_header(header):
    if not header: return None
    # Remove newlines and non-alphanumeric chars
    h = str(header).replace('\n', ' ').replace('\r', ' ')
    h = re.sub(r'[^a-zA-Z0-9 ]', '', h)
    # Convert to snake case
    h = h.strip().replace(' ', '_').upper()
    return h if h else None

def generate_models():
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    sheets_to_process = {
        'Layer-1(Semantic)': 'SemanticLayer',
        'Layer-2(AI-Curated)': 'AiCuratedLayer',
        'Layer-3A(Integration-Pull)': 'IntegrationPull',
        'Layer-3B(Integration-Push)': 'IntegrationPush',
        'Layer-3(PublicCloud)': 'PublicCloudLayer'
    }

    model_content = """from sqlalchemy import Column, String, Integer, Text, func, DateTime
from db.base import Base

"""

    for sheet_name, class_name in sheets_to_process.items():
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            
            # Find the header row (sometimes row 1 is just title, but let's assume row 1 for now)
            headers = []
            for cell in sheet[1]:
                h = clean_header(cell.value)
                if h:
                    headers.append(h)
            
            print(f"Sheet: {sheet_name} | Found Headers: {headers}")
            
            table_name = sheet_name.lower().replace('-', '_').replace('(', '_').replace(')', '')
            
            model_content += f"class {class_name}(Base):\n"
            model_content += f"    \"\"\"{sheet_name} converted from Excel\"\"\"\n"
            model_content += f"    __tablename__ = \"{table_name}\"\n"
            model_content += f"    __table_args__ = {{\"schema\": \"ai\"}}\n\n"
            model_content += f"    id = Column(Integer, primary_key=True, autoincrement=True)\n"
            
            for h in headers:
                model_content += f"    {h} = Column(Text)\n"
            
            model_content += f"    created_at = Column(DateTime, default=func.now())\n\n"

    with open(output_file, 'w') as f:
        f.write(model_content)
    print(f"Generated {output_file} based on Excel headers.")

if __name__ == "__main__":
    generate_models()
