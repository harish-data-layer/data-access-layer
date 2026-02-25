import openpyxl

file_path = r"c:\Users\haris\Downloads\harish folder\main reepo\tai-data-api\db\20260108 - VIM DataDictionary (1).xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
sheet = wb['Layer-1(Semantic)']

print("First 5 rows of Layer-1(Semantic):")
for i, row in enumerate(sheet.iter_rows(max_row=5, values_only=True), 1):
    print(f"Row {i}: {row}")
