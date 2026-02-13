# 🏭 TranAI DAL - Production Integration Guide

This application is now **Production Ready** for SAP Integration.
To go live, follow these exact steps to connect to your real SAP ECC or S/4HANA system.

## 1. 🔑 SAP Credentials & Access (Phase 1)
You must obtain a **Service Account** from your SAP BASIS team.
Do NOT use your personal user.

### Required Permissions
| Access Type | Authorization Object | Activity |
|-------------|----------------------|----------|
| **RFC**     | `S_RFC`              | Execute (`16`) |
| **OData**   | `S_SERVICE`          | Start (`16`) |
| **Tables**  | `S_TABU_DIS`         | Display (`03`) |

## 2. ⚙️ Configuration (Phase 2)
Update your `.env` file with the real credentials.

```bash
# S/4HANA OData (Gateway)
SAP_ODATA_URL="https://sap-prod.company.com/sap/opu/odata/sap/"
SAP_ODATA_USER="SRV_TRANAI_DAL"
SAP_ODATA_PASSWORD="COMPLEX_PASSWORD_HERE"
SAP_CLIENT="100"

# ECC NetWeaver RFC
SAP_ASHOST="sap-prod.company.com"
SAP_SYSNR="00"
SAP_SYSID="PRD"
SAP_USER="SRV_TRANAI_RFC"
SAP_PASSWD="COMPLEX_PASSWORD_HERE"
```

## 3. 📦 Installing Real RFC Drivers (Phase 3)
The current RFC connector is using a **Mock Client** because the SAP NetWeaver SDK is proprietary and cannot be pre-installed.

1.  **Download SAP NW RFC SDK 7.50** from [SAP Launchpad](https://launchpad.support.sap.com/).
2.  Extract it to `C:\nwrfcsdk` (Windows) or `/usr/local/sap/nwrfcsdk` (Linux).
3.  Add the `lib` folder to your `PATH` or `LD_LIBRARY_PATH`.
4.  Install the Node.js wrapper:
    ```bash
    npm install node-rfc
    ```
5.  **Edit `src/connectors/sap/rfc.ts`**:
    Uncomment the real import and remove the mock class.
    ```typescript
    import { Client } from 'node-rfc';
    // Remove the mock implementation
    ```

## 4. 🚀 Features Enabled
We have implemented the following Enterprise Integration Patterns:

### ✅ 1. Delta Sync (Vendors)
- **Endpoint**: `POST /api/v1/sync/vendors`
- **Logic**: Uses `LastChangeDate` to fetch only modified records from SAP.
- **Service**: `src/services/vendor.service.ts`

### ✅ 2. Transactional Posting (Invoices)
- **Endpoint**: `POST /api/v1/invoices`
- **Logic**:
    1.  Validates data.
    2.  Calls `BAPI_INCOMINGINVOICE_CREATE`.
    3.  Checks for `BAPIRET2` errors.
    4.  Executes `BAPI_TRANSACTION_COMMIT` if successful.
    5.  Executes `BAPI_TRANSACTION_ROLLBACK` on failure.
- **Service**: `src/services/invoice.service.ts`

### ✅ 3. CSRF Protection (Writes)
- **Connector**: `src/connectors/sap/odata.ts`
- **Logic**: Automatically fetches `x-csrf-token` before performing any POST/PUT/PATCH operations.

## 5. 🛡️ Production Checklist
- [ ] **Network**: Ensure firewall allows traffic from this server to SAP (Port 3300 for RFC, 443 for OData).
- [ ] **Security**: Enable TLS/SSL for all SAP connections.
- [ ] **Monitoring**: Check `http://localhost:3001/metrics` for sync lag and error rates.

## 6. 🧪 Verification
Run a test sync:
```bash
curl -X POST http://localhost:3001/api/v1/sync/vendors -H "Content-Type: application/json" -d '{"full": true}'
```
