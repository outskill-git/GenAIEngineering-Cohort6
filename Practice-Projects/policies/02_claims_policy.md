# Arrowline Logistics — Claims Policy
*Document ID: ARW-POL-002 · Version 7.0 · Effective 1 April 2026*

## 1. Claim types

| Type | Raised when |
|---|---|
| `SLA_BREACH` | Shipment delivered, or still undelivered, after the promised timestamp |
| `DAMAGE` | Damage recorded at delivery or reported within the claim window |
| `LOSS` | Shipment not traceable, or undelivered 10 days past the promised timestamp |

## 2. Claim window (hard requirement)

A claim must be filed within **15 calendar days**:

- for `DAMAGE` and `SLA_BREACH`: 15 days from **actual delivery**;
- for `LOSS`: 15 days from the **promised delivery** timestamp.

A claim filed after the window is rejected with reason `REJECTED_LATE_FILING`. This rule has
no exceptions and is not subject to agent discretion.

## 3. Liability limits

Arrowline's liability for loss or damage is the **lowest** of:

1. the declared value of the shipment;
2. ₹500 per kilogram of actual weight, subject to a minimum of ₹5,000;
3. an absolute cap of **₹50,000** per shipment.

For `DAMAGE` claims, **50% of the amount calculated above** is payable, unless an independent
surveyor's report is attached, in which case the assessed amount is payable up to the limit.

For `SLA_BREACH` claims, liability is calculated under ARW-POL-001 §3 (freight refund only).

## 4. Mandatory rejection reasons

A claim **must** be rejected, regardless of customer tier or relationship, where:

| Code | Condition |
|---|---|
| `REJECTED_LATE_FILING` | Filed outside the 15-day window (§2) |
| `REJECTED_UNDECLARED_GOODS` | Contents required a declaration that was not made (ARW-POL-004) |
| `REJECTED_PACKAGING` | `DAMAGE` claim where packaging did not meet ARW-POL-003 for that category |
| `REJECTED_FORCE_MAJEURE` | Delay or loss falls inside a declared force majeure window (ARW-POL-005) |
| `NOT_YET_ELIGIBLE` | `LOSS` claim filed before 10 days past the promised timestamp |

## 5. Approval authority

| Settlement amount | Approval required |
|---|---|
| Up to ₹10,000 | Auto-approved by the system |
| ₹10,001 – ₹25,000 | Claims supervisor |
| Above ₹25,000 | Claims manager — **human approval mandatory** |

**Repeat claimant rule.** Where the same customer has filed **two or more claims in the
preceding 90 days**, the claim must be routed for **human review regardless of amount**, and
the settlement note must record the customer's claim history.

## 6. Documents

| Claim type | Required |
|---|---|
| `SLA_BREACH` | None beyond the waybill |
| `DAMAGE` | Photographs of the packaging and contents; POD noting the damage |
| `LOSS` | Signed non-delivery declaration from the consignee |

Where a required document is missing, the claim is placed in `AWAITING_DOCUMENTS` and the
customer is asked once. If the document is still missing after **two requests**, the claim is
closed as `CLOSED_INCOMPLETE`. Claims are never settled on the assumption that a document
would have supported the claim.

## 7. Audit

Every claim decision must record: the rule applied, the computed amount, who or what approved
it, and the full sequence of checks performed. Decisions that cannot be reconstructed from the
audit trail are treated as invalid in the quarterly audit.
