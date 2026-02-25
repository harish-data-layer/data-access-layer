# RFC Pipeline - SAP to PostgreSQL (via RFC/ABAP Function Module)

## How It Works
```
Your PC --> RFC/TCP port 3240 --> SAP App Server --> RFC_READ_TABLE --> Data
                                                                          |
                                                                   PostgreSQL
```

## Speed vs GUI
| Method | Speed | 10,000 rows |
|--------|-------|-------------|
| GUI Script | ~1 min / 200 rows | ~50 minutes |
| **RFC (this)** | ~5 sec / 50,000 rows | **~1 minute** |

## Setup (One-time)

### Step 1: Download SAP NW RFC SDK
1. Go to https://support.sap.com
2. Search "SAP NW RFC SDK"
3. Download version for Windows 64-bit
4. Extract to `C:\nwrfcsdk\`

### Step 2: Add to PATH
```
System Properties > Environment Variables > PATH > Add: C:\nwrfcsdk\lib
```

### Step 3: Install pyrfc
```bash
pip install pyrfc
```

## Usage
```bash
# Test connection first
python rfc_client.py

# Pull tables
python rfc_pull.py MARA               # All materials
python rfc_pull.py LFA1               # All vendors  
python rfc_pull.py EKKO               # Purchase orders
python rfc_pull.py VBAK               # Sales orders
python rfc_pull.py MARA 10000         # MARA, max 10000 rows
python rfc_pull.py EKKO "BUKRS='1000'"  # Filter by company code
```

## Connection Details (from Anna)
- **SAP Router String:** `/H/s1.mncinfosys.com/S/3240`
- **Host:** s1.mncinfosys.com
- **System Number:** 40 (port 3240 = 3200 + 40)
- **Client:** 100

## Files
| File | Purpose |
|------|---------|
| `config.py` | SAP RFC + PostgreSQL connection settings |
| `rfc_client.py` | RFC client (connect, read_table, call_fm) |
| `rfc_pull.py` | Main script: pull SAP table → PostgreSQL |
