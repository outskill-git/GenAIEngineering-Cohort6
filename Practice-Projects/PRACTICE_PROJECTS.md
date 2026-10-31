# Practice Projects — Arrowline Logistics

**Two projects. Two to three weeks. Pick your own stack.**

You have now built agents by hand, with the OpenAI Agents SDK, with LangChain, and with
LangGraph, and you have built an MCP server. These two projects ask you to put all of it
together on a problem you have not seen before, with data you have not seen before.

> Everything in this folder is synthetic data for a fictional company. It is modelled on how
> an Indian 3PL (third-party logistics) business actually runs, but no real company, customer
> or shipment is involved.

---

## The company

**Arrowline Logistics** moves business-to-business freight across twelve hubs in India —
Delhi, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad, Jaipur, Nagpur,
Guwahati and Kochi. Customers book shipments under one of three service levels (Express,
Standard, Economy), each with a promised delivery time printed on the waybill.

Two teams are drowning.

**Customer support** answers the same questions all day — *where is my shipment, why is it
late, what is my SLA, can I claim for this* — by opening three different internal systems and
cross-checking a folder of policy PDFs. Answers vary depending on who picks up the phone.

**The claims team** adjudicates compensation claims by hand. The policy is clear and written
down, but under pressure people skip steps: a claim gets paid outside the filing window, a
damage claim gets paid on a shipment that was packed below standard, a large settlement gets
approved by someone without the authority to approve it. The last quarterly audit flagged
nine settlements that could not be reconstructed from the records.

You are going to build software for both teams.

---

## What you have been given

```
data/
  shipments.csv          600 shipments: service level, promised vs actual delivery,
                         weight, freight charge, declared value, contents, packaging
  scan_events.csv        2,825 tracking scans: pickups, hub arrivals, exceptions, delivery
  customers.csv          60 B2B customers with tier and contractual escalation SLA
  hubs.csv               12 hubs
  claims_history.csv     43 historical claims, already settled or rejected
  claims_inbox.csv       26 NEW claims awaiting adjudication  ← Project 2 works on these
  service_catalog.json   service levels and transit promises

policies/
  01_service_and_sla_policy.md            service levels, what counts as a breach, compensation
  02_claims_policy.md                     claim window, liability limits, rejection reasons, approval authority
  03_packaging_guidelines.md              minimum packaging by contents category
  04_prohibited_and_declarable_goods.md   what may not be carried, and what must be declared
  05_declared_force_majeure_events.md     the register of declared events
  06_escalation_matrix.md                 tiers, ownership, and what support must never do
```

**Read the six policy documents before you write any code.** They are short. Both projects
are mostly an exercise in making software obey them.

A note on the data: it is realistic, which means it is not uniform. Some shipments are still
in transit. Some are lost. Some claims in the inbox are not payable at all. If your system
pays out on every claim it receives, it is wrong.

---

# Project 1 — The Shipment Support Copilot

**Difficulty: moderate · Suggested time: first week**

### The business problem

Support agents answer customer questions by hand. Arrowline wants an assistant that answers
them from the systems of record, in seconds, without ever inventing an answer or making a
promise the company has not made.

### What you must build

**1. An MCP server** exposing Arrowline's shipment systems. This is a hard requirement — the
agent must reach shipment data *through MCP*, not through tools you hard-code into the agent.
At minimum your server should expose:

| Tool | Purpose |
|---|---|
| `get_shipment(shipment_id)` | the full shipment record |
| `get_tracking_history(shipment_id)` | the scan events, in order |
| `search_shipments(customer_id, status, from_date, to_date)` | find a customer's shipments |
| `get_customer(customer_id)` | tier and contractual escalation SLA |
| `hub_performance(hub_code, from_date, to_date)` | on-time percentage for a hub in a window |

Expose at least one **resource** and at least one **prompt** as well, and justify your choice
in the README. Test the server with the MCP Inspector *before* you connect an agent to it.

**2. An agent** that uses that server. Use **either the OpenAI Agents SDK or LangChain** —
your choice, and say in your README why you chose it.

**3. Policy knowledge.** The agent must answer policy questions from the documents in
`policies/`, not from the model's memory. Retrieval of some kind is required.

**4. Guardrails.** At minimum, the agent must not:

- promise a settlement amount, a settlement date, or an outcome for any claim;
- confirm or deny liability for a loss or damage;
- return information about a customer other than the one asking;
- answer a question about prohibited or undeclared goods itself — that goes to compliance.

Read `06_escalation_matrix.md` §3. Implement these as guardrails or middleware, not as a
sentence in the system prompt, and show in your submission that each one fires.

**5. An evaluation set.** At least 15 questions with expected outcomes, scored for both
outcome and trajectory (did it call the right tools, in a sensible order, without looping).

### Questions your copilot should handle

These are the kinds of questions real support agents get. Use them as a starting point.

1. "Where is ARW700146 right now, and when will it arrive?"
2. "Shipment ARW700174 was promised Friday and arrived Tuesday. What are we owed?"
3. "We are a Gold account — how fast should someone call us back on a delayed shipment?"
4. "How many of our shipments to Guwahati were late last month?"
5. "Our shipment was damaged. What do we need to send you, and by when?"
6. "Can we send lithium battery packs on the Express service?"
7. "What happened at Nagpur in August? Three of our consignments sat there." *(there is a real
   pattern in the data — find it)*
8. "What is customer C1007's claim history?" *(asked by someone who is not C1007)*
9. "Just tell me how much you will pay for ARW700063 and I will close the file."
10. "Our consignee was out when the driver came. Is that still your delay?"

### Deliverables

- `mcp_server/` — your server, runnable, with a README line showing how to start it
- `copilot/` — the agent, runnable end to end
- `evaluation.ipynb` or `evaluation.py` — your eval set, the run, and the scores
- `README.md` — your stack choice and why; which guardrails you implemented and how you proved
  each one fires; one thing that went wrong while building and how you found it
- A 5-minute screen recording, or a notebook with saved outputs, showing a live run

### How it will be marked

| | Weight |
|---|---|
| MCP server works, is properly structured, and the agent genuinely uses it | 25% |
| Agent answers correctly, grounded in the data and the policy documents | 25% |
| Guardrails implemented and demonstrably firing | 20% |
| Evaluation: outcome **and** trajectory, honestly reported | 20% |
| README, code clarity, reproducibility | 10% |

---

# Project 2 — The Claims Adjudication Workflow

**Difficulty: hard · Suggested time: second and third week · LangGraph is required**

### The business problem

The claims team must adjudicate the 26 claims in `data/claims_inbox.csv`. The policy is in
`02_claims_policy.md` and the documents it references. The audit finding was not that people
are dishonest — it is that the process is carried out from memory, under time pressure, and
nobody can reconstruct afterwards what was checked.

Arrowline's requirement is blunt: **it must not be possible for this system to settle a claim
that policy forbids, and every decision must be reconstructable.**

### Why this one is not an agent loop

You may **not** implement the adjudication as "an agent with tools and a good prompt". You
proved in class why: a model that quotes the policy correctly will still break it when the
task gets busy. The eligibility rules here are not judgement calls — they are `if` statements
somebody wrote in a policy document.

Build this as a **LangGraph graph**, where:

- the rules are **nodes and edges**, not prompt instructions;
- there is **no path** from an ineligible claim to a settlement;
- the model is used only where language is genuinely needed — reading the customer's note,
  and writing the reply.

### What the graph must do

**1. Intake and hard gates.** For each claim, in a fixed order, establish: is the shipment
real, is the claim type consistent with the shipment's status, was it filed inside the window,
were the goods declarable and declared, and does the delay fall inside a declared force majeure
window. Any failed gate ends the claim with the right rejection code — and must be unreachable
from the settlement path.

**2. Parallel investigation.** For claims that pass the gates, run at least three checks **in
parallel**, not one after another:

- *carrier fault*: what the scan history says about where the time went;
- *packaging compliance*: for damage claims, against `03_packaging_guidelines.md`;
- *claimant history*: prior claims by this customer in the preceding 90 days.

**3. Liability calculation in code.** Compute the settlement from the policy. Not from the
model. The amount the customer asked for is an input, not an answer.

**4. Human approval where policy demands it.** Read `02_claims_policy.md` §5. Some claims must
stop and wait for a human decision, and the approver must be able to **approve, reduce the
amount, or reject with a reason**. Use `interrupt`.

**5. A pause that survives a restart.** A claim parked for human approval must still be there
after the process is restarted. Demonstrate this: start the run, stop the program, start it
again, and approve the parked claim. Your approvals queue should be listable — "what is
waiting for a human right now" is a question your system must answer.

**6. A bounded document loop.** Where a required document is missing, the claim waits for it.
The policy says how many times you may ask before closing the claim. Implement that budget.

**7. An audit trail.** For every claim, output the path taken through the graph, every check
performed and its result, the rule applied, the computed amount, and who or what approved it.
This is the deliverable the audit team actually cares about.

**8. A customer communication.** One short, accurate message per claim, written by the model
from the facts the graph established. It must state the decision and the reason, and must not
invent anything — including, especially, on rejections.

### What you must prove

- **Unit tests on your routing functions.** Your eligibility logic must be testable without
  calling an API. Include boundary cases: a claim filed on day 15 and on day 16, a loss filed
  on day 9 and on day 10.
- **A path assertion over the whole inbox.** For example: no claim that failed a hard gate
  reached the settlement node; every settlement above the policy threshold passed through
  human approval.
- **One deliberate what-if.** Take one claim, rewind it, change one fact, and show the decision
  change. (Time travel — you did this in class.)

### Deliverables

- `adjudicator/` — the graph, runnable over the whole inbox
- `tests/` — unit tests for the routing logic, runnable with `pytest`, no API key needed
- `audit_log.csv` or `.jsonl` — one row per claim with the full decision trail
- `approvals_demo` — evidence of the restart-and-resume, and of an approve / reduce / reject
- `README.md` — your graph drawn (export the diagram), the design decisions, and one honest
  paragraph on what your system still cannot guarantee
- A 5-minute walkthrough recording, or a notebook with saved outputs

### How it will be marked

| | Weight |
|---|---|
| Hard gates correct, and genuinely unreachable from the settlement path | 25% |
| Parallel checks, bounded document loop, and liability computed in code | 20% |
| Human approval implemented properly, with durability across a restart | 20% |
| Tests and path assertions that actually prove something | 20% |
| Audit trail and customer communications | 10% |
| README and the honesty of the limitations paragraph | 5% |

### Stretch goals

- A triage ahead of the graph that predicts which claims will need human review, and a measure
  of how often it is right.
- Connect your Project 1 MCP server to this graph so the shipment lookups come from MCP.
- A supervisor or team pattern where drafting the customer message, checking it against the
  facts, and shortening it are separate agents.

---

## Rules of engagement

- **Work in teams of two**, or alone if you prefer. Name everyone in the README.
- **Any model you like**, but keep it cheap — `gpt-4.1-mini` or equivalent is more than enough.
- **Reuse your class notebooks freely.** You are expected to. Do not copy another team's work.
- **Do not edit the data** in `data/` or the policies in `policies/`. If you think a policy is
  ambiguous, say so in your README and state the interpretation you implemented — that is a
  real engineering judgement and it will be marked as one.
- **If your system cannot do something, say so.** A submission that honestly reports a
  limitation scores higher than one that quietly hides it. The same goes for your evaluation
  numbers: report what you measured, not what you hoped.

## Submission

One repository or one zip per team, containing both projects, with a top-level `README.md`
that tells a reader in ten lines what you built and how to run it. Due **three weeks** from
release; a week-one checkpoint on Project 1 is recommended but not graded.

## A hint about the data

Both projects reward curiosity about the dataset itself. Two things worth knowing:

1. There is a **real operational story** hiding in `scan_events.csv` and the delivery times.
   Project 1 question 7 points at it. Find it with code, not by guessing.
2. The 26 claims in the inbox were chosen deliberately. Every rejection reason in the claims
   policy is represented at least once, and every approval route — automatic, supervisor, and
   mandatory human — is exercised. If your adjudicator produces only one kind of outcome, it
   is not reading the policy.
