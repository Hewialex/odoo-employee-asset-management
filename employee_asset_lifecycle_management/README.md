# Employee Asset Lifecycle Management

## Odoo Module — Technical Name: `employee_asset_lifecycle_management`
**Target Version:** Odoo 15+  
**Dependency:** `hr`, `mail`, `base_setup`

---

## Overview

A complete module to manage the **full lifecycle of physical assets assigned to employees** — from procurement tracking through assignment, repair, depreciation, and disposal.

---

## Module Structure

```
employee_asset_lifecycle_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── asset_asset.py          # Core asset model
│   ├── asset_assignment.py     # Employee assignment model
│   ├── asset_repair.py         # Repair request model
│   └── hr_employee.py          # hr.employee extension (smart buttons)
├── wizard/
│   ├── __init__.py
│   ├── asset_dispose_wizard.py         # Disposal workflow
│   ├── asset_dispose_wizard_views.xml
│   ├── asset_depreciation_wizard.py    # Manual depreciation trigger
│   └── asset_depreciation_wizard_views.xml
├── views/
│   ├── asset_asset_views.xml       # Asset: form, tree, kanban, graph, pivot
│   ├── asset_assignment_views.xml  # Assignment: form, tree
│   ├── asset_repair_views.xml      # Repair: form, tree, kanban, graph
│   ├── hr_employee_views.xml       # Smart buttons on employee
│   └── asset_menu.xml              # All menus
├── security/
│   ├── asset_security.xml          # Groups & record rules
│   └── ir.model.access.csv         # ACL
├── data/
│   ├── asset_sequence.xml          # AST/YYYY/##### sequence
│   ├── asset_cron.xml              # Monthly depreciation scheduler
│   └── asset_demo.xml              # 6 demo assets
├── report/
│   ├── asset_report_templates.xml  # QWeb PDF templates
│   └── asset_report_actions.xml    # Report actions
└── static/description/
    └── icon.svg
```

---

## Models

### `asset.asset`
| Field | Type | Notes |
|---|---|---|
| `name` | Char | Required |
| `asset_ref` | Char | Auto-sequence `AST/YYYY/#####` |
| `asset_tag` | Char | Unique (SQL constraint) |
| `asset_type` | Selection | Laptop, Phone, ID Card, Vehicle, Monitor, … |
| `serial_number` | Char | |
| `purchase_date` | Date | |
| `warranty_expiry_date` | Date | |
| `value` | Float | Original purchase value |
| `depreciation_rate` | Float | % per month |
| `current_value` | Float | **Computed** — `value - (months * rate/100 * value)` |
| `status` | Selection | Available / Assigned / Under Repair / Returned / Lost / Disposed |
| `condition` | Selection | New / Good / Fair / Poor / Damaged |

### `asset.assignment`
| Field | Type | Notes |
|---|---|---|
| `employee_id` | Many2one → `hr.employee` | |
| `asset_id` | Many2one → `asset.asset` | Auto-sets asset status |
| `assigned_by` | Many2one → `res.users` | Defaults to current user |
| `assignment_date` | Date | |
| `expected_return_date` | Date | Highlighted red when overdue |
| `actual_return_date` | Date | Setting this returns the asset |
| `condition_on_return` | Selection | Updates asset condition on return |
| `remarks` | Text | |

### `asset.repair`
| Field | Type | Notes |
|---|---|---|
| `asset_id` | Many2one → `asset.asset` | |
| `requested_by` | Many2one → `hr.employee` | |
| `request_date` | Date | |
| `issue_description` | Text | Required |
| `repair_cost` | Float | |
| `status` | Selection | New / In Progress / Done / Rejected |

---

## Access Control

| Group | Create | Read | Write | Delete |
|---|---|---|---|---|
| HR Manager | ✅ | ✅ | ✅ | ✅ |
| Asset Manager | ✅ | ✅ | ✅ | ❌ |
| Employee | Own only | ✅ | Own repairs | ❌ |

---

## Depreciation Formula

```
current_value = value - ((months_passed × depreciation_rate / 100) × value)
```

- Runs automatically monthly via scheduled action (`ir.cron`)
- Can be triggered manually via **Configuration → Compute Depreciation**

---

## Installation

1. Copy the `employee_asset_lifecycle_management` folder to your Odoo `addons` directory
2. Restart Odoo server
3. Go to **Apps**, update the app list, search `employee_asset_lifecycle_management`
4. Click **Install**

---

## Demo Data

6 pre-loaded demo assets (Laptop, Phone, Vehicle, ID Card, Monitor) with realistic values and depreciation rates.

