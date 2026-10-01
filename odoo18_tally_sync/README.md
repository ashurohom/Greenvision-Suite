# Odoo 18 Tally Sync

A comprehensive, production-ready framework to synchronize data between Odoo 18 Enterprise and Tally.

## Features
- Tally Configuration & 5-Second Test Connection Notification
- 5-Second Auto-Closing Popup Notifications for both Success and Failure
- Customer & Vendor Import / Export with Status Tracking
- Product (Stock Item) Export
- Automatic Unique Record Identifiers (ir.sequence) for Customers, Vendors, Invoices, Bills, Credit Notes, Debit Notes, and Payments
- Accounting Voucher Export: Invoices, Vendor Bills, Credit Notes, Debit Notes
- Payment & Receipt Voucher Export (Single, Bulk, & From Invoices)
- Manual Batch Sync Wizard
- Detailed Audit Logs & Server Actions for List Views
- Reusable Provider-based Service Architecture

## Architecture

This module implements a **Provider Pattern**.
The Odoo models do not contain API logic. They call the service layer which handles API communication and XML parsing/generation.

- `services/tally_client.py`: Abstract Base Class for API communication.
- `services/xml_parser.py`: Logic to parse Tally XML responses.
- `services/xml_generator.py`: Logic to generate Tally-compliant XML.
- `services/customer_service.py` & `vendor_service.py`: Business logic for mapping and orchestration.

## How to replace generic API
If a specific Tally API or middleware is introduced:
1. Subclass `TallyClient` or replace its `send_request` logic.
2. Update the `customer_service.py` and `vendor_service.py` mapping functions if required by the middleware.

## Installation
Just place the `odoo18_tally_sync` folder in your addons path and install it from the Apps menu.

## How to Use

### 1. Configure the API Connection
1. In the **Tally Integration** app, click on **Configuration** -> **Tally Configurations**.
2. Click **New** to create a new configuration record.
3. Fill in the details (Server URL, Company Name, Authentication Type, Credentials).
4. Make sure **Active** is checked.
5. Click **Test Connection** to verify connectivity.

### 2. Export / Import Data to Tally
1. **Contacts**: In **Contacts**, click **Export to Tally** (or bulk select in list view -> **Action** -> **Export to Tally**).
2. **Invoices & Bills**: In **Invoicing / Accounting**, open any posted Invoice, Bill, Credit Note, or Debit Note and click **Export to Tally** (or bulk select in list view).
3. **Payments**: Open any validated Payment and click **Export to Tally**, or click **Export Payment to Tally** directly from an invoice.
4. **Products**: In **Inventory / Sales**, open any Product and click **Export to Tally** (or bulk select in list view).
5. **Popup Notification**: Whenever an export is triggered, a **5-second popup notification** automatically appears on the top-right indicating whether the export **Succeeded** (green) or **Failed** (red with error details), and auto-dismisses after 5 seconds while refreshing the view.

### 3. Run a Bulk Manual Sync
1. In the **Tally Integration** app, click the **Manual Sync** menu.
2. Select the model (Customers, Vendors, Products, Payments, Credit Notes, Debit Notes).
3. Select **Import from Tally** or **Export to Tally**.
4. Click **Start Sync** to process the batch. A 5-second popup summary will be displayed upon completion.

### 4. Check the Sync Logs
1. Click the **Sync Logs** menu to see a history of all API requests.
2. Open any log to see the exact XML request sent, response received, and errors (if any).

### 5. Automatic Unique Record Identifiers (Odoo)
The module automatically assigns standard, sequence-based unique IDs upon creation of records in Odoo:
| Record Type | Model | Technical Field | Sequence Code | Format Example |
| :--- | :--- | :--- | :--- | :--- |
| **Customer** | `res.partner` | `tally_customer_id` | `tally.customer.id` | `CUST-00001` |
| **Vendor** | `res.partner` | `tally_vendor_id` | `tally.vendor.id` | `VEND-00001` |
| **Customer Invoice** | `account.move` | `tally_invoice_id` | `tally.invoice.id` | `INV-00001` |
| **Vendor Bill / Purchase** | `account.move` | `tally_purchase_id` | `tally.purchase.id` | `PUR-00001` |
| **Customer Payment** | `account.payment` | `tally_customer_payment_id` | `tally.customer.payment.id` | `CPAY-00001` |
| **Vendor Payment** | `account.payment` | `tally_vendor_payment_id` | `tally.vendor.payment.id` | `VPAY-00001` |
| **Customer Credit Note** | `account.move` | `tally_credit_note_id` | `tally.credit.note.id` | `CCN-00001` |
| **Vendor Debit Note** | `account.move` | `tally_debit_note_id` | `tally.debit.note.id` | `DBN-00001` |

Key Characteristics:
- Generated automatically upon creation using Odoo 18 standard `ir.sequence`.
- Readonly and non-editable by users.
- Database (`_sql_constraints`) and model (`@api.constrains`) uniqueness protection.
- Duplicating a record automatically assigns a fresh unique ID to the copy.
- Displayed on form views (main sheet and Tally Integration notebook page).
- Searchable and filterable in list and search views.
- Dedicated modular implementation in `models/tally_unique_id.py`, `data/tally_sequence_data.xml`, and `views/tally_unique_id_views.xml`.

