import pandas as pd

excel_path = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api\demo\AI DEMO FILE.xlsx"

try:
    xls = pd.ExcelFile(excel_path)
    
    with open("c:/Users/haris/Downloads/harish folder/main reepo/tai-data-api/demo/columns_out.txt", "w", encoding="utf-8") as f:
        for sheet_name in xls.sheet_names:
            f.write(f"\n--- Sheet: {sheet_name} ---\n")
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, nrows=6)
            f.write(df.to_string())
            f.write("\n")
                
except Exception as e:
    with open("c:/Users/haris/Downloads/harish folder/main reepo/tai-data-api/demo/columns_out.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {str(e)}\n")
