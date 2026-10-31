# Practice Projects — Arrowline Logistics

Two take-home projects for the agents course. Start with **[PRACTICE_PROJECTS.md](PRACTICE_PROJECTS.md)**.

| | Project | Stack |
|---|---|---|
| 1 | **Shipment Support Copilot** — an MCP server over the shipment systems, plus an agent that answers customer questions from it and from the policy documents | Your choice: OpenAI Agents SDK **or** LangChain. Building your own MCP server is required |
| 2 | **Claims Adjudication Workflow** — adjudicate 26 real claims against a written policy, with hard gates, parallel checks, human approval and a full audit trail | **LangGraph required** |

Project 2 uses the same company and dataset as Project 1, so the work carries forward.

## Data dictionary

### `data/shipments.csv` — 600 rows
| Column | Meaning |
|---|---|
| `shipment_id` | `ARW7xxxxx`, the waybill number |
| `customer_id` | joins to `customers.csv` |
| `origin_hub`, `destination_hub`, `destination_city` | three-letter hub codes, joins to `hubs.csv` |
| `service_level` | Express, Standard or Economy |
| `booked_at`, `promised_delivery` | `YYYY-MM-DD HH:MM`. The promise is printed on the waybill |
| `actual_delivery` | empty if the shipment is still in transit or was lost |
| `status` | DELIVERED, DAMAGED, LOST or IN_TRANSIT |
| `weight_kg`, `declared_value_inr`, `freight_charge_inr` | used by the liability rules |
| `contents_category` | Electronics, Apparel, Documents, Pharma (non-cold), Auto Parts, FMCG, Furniture, Lithium Batteries |
| `packaging_type` | Carton-Single, Carton-Double, Pallet, Envelope, Crate |
| `hazmat_declared` | Yes / No for declarable goods, `N/A` otherwise |

### `data/scan_events.csv` — 2,825 rows
One row per tracking scan: `shipment_id`, `timestamp`, `hub`, `event_code`, `notes`.
Event codes include `PICKED_UP`, `ARRIVED_HUB`, `DEPARTED_HUB`, `DELIVERY_ATTEMPTED`,
`DELIVERED`, and exceptions such as `EXCEPTION_HUB_CONGESTION`, `EXCEPTION_DAMAGE_REPORTED`
and `EXCEPTION_NOT_FOUND`.

### `data/customers.csv` — 60 rows
`customer_id`, `company_name`, `tier` (Gold / Silver / Bronze), `escalation_sla_hours`,
`monthly_volume`, `account_manager`.

### `data/claims_history.csv` — 43 rows
Claims already decided: `claim_id`, `shipment_id`, `customer_id`, `claim_type`,
`amount_claimed_inr`, `filed_at`, `status`, `settled_amount_inr`. Use this for the
repeat-claimant check — not as a model of correct decisions.

### `data/claims_inbox.csv` — 26 rows ← **Project 2 adjudicates these**
`claim_ref`, `shipment_id`, `customer_id`, `claim_type`, `amount_claimed_inr`, `filed_at`,
`documents_attached` (semicolon separated, may be empty), `customer_note`.

### `data/hubs.csv`, `data/service_catalog.json`
Hub master data, and the service-level transit promises in machine-readable form.

## Loading the data

```python
import pandas as pd
ship = pd.read_csv("data/shipments.csv", parse_dates=["booked_at","promised_delivery","actual_delivery"])
scans = pd.read_csv("data/scan_events.csv", parse_dates=["timestamp"])
inbox = pd.read_csv("data/claims_inbox.csv", parse_dates=["filed_at"])
```

Everything is synthetic and generated from a fixed seed, so the numbers are stable — if your
answer changes between runs, that is your system, not the data.

## The policies

The six documents in `policies/` are the specification for both projects. Read them first;
they are about 1,600 words in total and nearly every requirement in the brief traces back to
a specific clause.
