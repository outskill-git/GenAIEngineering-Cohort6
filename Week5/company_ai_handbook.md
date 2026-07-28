# Northstar Retail AI Handbook

## 1. Retrieval Augmented Generation Overview

Northstar Retail uses retrieval augmented generation to answer employee questions about store operations, product availability, loyalty rules, and support procedures. The application first retrieves trusted internal passages and then asks a language model to answer using that context. Answers must cite the policy section that supplied the evidence.

The retrieval layer is intentionally split into semantic search and keyword search. Semantic search handles paraphrases such as "late package" matching "delayed shipment." Keyword search handles exact terms such as product codes, policy IDs, and region names. The final result list merges both signals.

## 2. Customer Support Escalation Policy

Support agents should resolve standard delivery questions directly when the order status is available in the order management system. If an order has no carrier scan for more than forty-eight hours, the agent should open a logistics escalation. If the customer is a loyalty plus member, the agent may also offer a shipping credit up to fifteen dollars.

Refund requests for damaged items require a photo, the order number, and a short description of the damage. Items over two hundred dollars require supervisor approval before a replacement is sent. Perishable items may be replaced without return shipping.

## 3. Loyalty Program Rules

Customers earn ten points for every dollar spent on eligible merchandise. Points expire after twelve months of account inactivity. Loyalty plus members receive free standard shipping, early access to seasonal sales, and a birthday reward during the month of their birthday.

Points cannot be redeemed for gift cards, marketplace items, or services. If a customer returns an item, the points earned from that item are removed from the account after the refund is completed.

## 4. Inventory And Store Operations

Store associates update shelf counts at the end of each shift. If the local count differs from the warehouse count by more than five units, the inventory team should run a cycle count. High-value electronics are counted every morning before opening.

The store pickup desk holds paid orders for five calendar days. After five days, the order is cancelled and the item is returned to available inventory. Customers receive reminder messages after forty-eight hours and after four days.

## 5. Responsible AI Controls

The assistant must not reveal private customer information unless the authenticated employee is authorized to view that account. The assistant should refuse requests to export full customer lists, payment tokens, or raw support transcripts. Aggregated metrics may be shared with store managers when individual customers cannot be identified.

When retrieved passages disagree, the assistant should prefer the most recent policy section and state that an ambiguity exists. The assistant should never invent refund rules, loyalty benefits, or escalation thresholds that are not present in the retrieved context.

## 6. Chunking Notes For The Demo

Fixed-size chunking is simple but may split a refund rule across two chunks. Overlapping chunks reduce that risk by repeating nearby words. Document-aware chunking follows headings, bullet lists, pages, or tables. Recursive chunking tries large boundaries first, such as headings and paragraphs, before falling back to sentences and words.

Semantic chunking groups adjacent sentences when their meaning is similar and starts a new chunk when the topic changes.
