# Arrowline Logistics — Service Levels and SLA Policy
*Document ID: ARW-POL-001 · Version 4.2 · Effective 1 April 2026*

## 1. Service levels

| Service level | Promised transit time | Cut-off | Notes |
|---|---|---|---|
| Express | 24–48 hours | 18:00 pickup | Metro-to-metro only; other lanes quoted as Standard |
| Standard | 48–96 hours | 16:00 pickup | Default service |
| Economy | 96–168 hours | 14:00 pickup | Surface movement, lowest cost |

The **promised delivery timestamp** printed on the waybill is calculated as the booking
timestamp plus the **upper bound** of the transit range for that service level.

**North-east surcharge window.** For shipments destined to north-east hubs (currently GAU –
Guwahati), an additional **24 hours** is added to the promised delivery timestamp, and freight
is charged at a 20% premium.

## 2. What counts as an SLA breach

A shipment is in breach when `actual_delivery > promised_delivery`.

Delay is measured in whole hours beyond the promised timestamp. A shipment that is still in
transit past its promised timestamp is in breach from the moment the promise lapses; it does
not need to be delivered first for the customer to raise a ticket.

## 3. SLA breach compensation

Compensation for a pure delay is a **refund of freight charges only**. The declared value of
the goods is not relevant to an SLA breach claim.

| Delay beyond promised delivery | Freight refunded |
|---|---|
| 1–24 hours | 25% |
| 25–72 hours | 50% |
| More than 72 hours | 100% |

Compensation is capped at the freight charge for that shipment. Arrowline does not pay
consequential loss, loss of profit, or penalties levied on the customer by their own buyer.

## 4. Exclusions

An SLA breach claim is **not** payable where the delay is attributable to:

1. A **declared force majeure event** (see ARW-POL-005). Events must be formally declared by
   the Network Operations head; a general statement that "it was raining" is not sufficient.
2. Incorrect or incomplete delivery address supplied by the shipper.
3. Consignee unavailable at the delivery address, evidenced by a `DELIVERY_ATTEMPTED` scan.
4. Customs, regulatory or law-enforcement hold.
5. Goods held because a required declaration was missing (see ARW-POL-004).

## 5. Escalation

Any shipment in breach by more than 48 hours must be escalated to the destination hub manager
and the account manager within the customer's contractual escalation SLA. Contractual
escalation SLAs by tier: **Gold 24 hours, Silver 48 hours, Bronze 72 hours.**
