# Arrowline Logistics — Prohibited and Declarable Goods
*Document ID: ARW-POL-004 · Version 3.1 · Effective 1 February 2026*

## 1. Prohibited outright
Currency and bullion, live animals, human remains, firearms and ammunition, narcotics,
corrosive acids, compressed gas cylinders, and any item prohibited under applicable law.

## 2. Declarable goods
Some goods may be carried **only when declared at booking** so that the shipment is routed on
a compliant lane and handled correctly.

| Category | Requirement |
|---|---|
| Lithium Batteries | Must be declared (`hazmat_declared = Yes`), packed per UN3480/UN3481 and crated |

## 3. Consequence of non-declaration
Where goods requiring a declaration were carried **without** one:

- Arrowline accepts **no liability** for loss or damage to that shipment;
- any claim is rejected with `REJECTED_UNDECLARED_GOODS`;
- repeat non-declaration is referred to the compliance team.

This applies even where the handling failure appears unrelated to the undeclared nature of the
goods. The rule exists because undeclared goods are routed on lanes that are not rated for them.
