# Why LangGraph? — From Agent Loops to Graphs

**Week 13 · Session 1 · Study guide**

Companion to the notebook `01_why_langgraph.ipynb`. Read it before the session for the ideas,
after the session for the reference tables.

---

## Table of contents

1. [Where we are: two SDKs, one machine](#1-where-we-are-two-sdks-one-machine)
2. [Side-by-side reference](#2-side-by-side-reference)
3. [The limitation: who owns the control flow](#3-the-limitation-who-owns-the-control-flow)
4. [What the control knobs actually do](#4-what-the-control-knobs-actually-do)
5. [Python first: `TypedDict` and `Annotated`](#5-python-first-typeddict-and-annotated)
6. [The LangGraph mental model](#6-the-langgraph-mental-model)
7. [Your first graph](#7-your-first-graph)
8. [Conditional edges: branching you can test](#8-conditional-edges-branching-you-can-test)
9. [Cycles: loops with a budget](#9-cycles-loops-with-a-budget)
10. [Reducers: how updates merge](#10-reducers-how-updates-merge)
11. [The refund desk, rebuilt as a graph](#11-the-refund-desk-rebuilt-as-a-graph)
12. [Agent loop or graph? A decision guide](#12-agent-loop-or-graph-a-decision-guide)
13. [Cheat sheet](#13-cheat-sheet)
14. [Exercises](#14-exercises)

---

## 1. Where we are: two SDKs, one machine

You have built agents twice.

**Week 11 — OpenAI Agents SDK**

```python
from agents import Agent, Runner
agent = Agent(name="support", instructions="...", model="gpt-4.1-mini", tools=[...])
result = await Runner.run(agent, "Customer wants a refund for N104470.")
```

**Week 12 — LangChain v1**

```python
from langchain.agents import create_agent
agent = create_agent(llm, tools=[...], system_prompt="...")
out = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

Underneath, both run the same machine:

```
   goal ──▶ [ model decides ] ──▶ [ tool runs ] ──▶ observation
               ▲                                        │
               └────────────────────────────────────────┘
                        repeat until the model stops
```

This is the **agent loop**. Every arrow in it is chosen by the model, at run time, on every
request. That freedom is the feature. It is also the problem we're going to find.

---

## 2. Side-by-side reference

### The building blocks

| Idea | LangChain v1 | OpenAI Agents SDK |
|---|---|---|
| the model | `init_chat_model("openai:gpt-4.1-mini")` | `Agent(model="gpt-4.1-mini")` |
| system prompt | a message in `ChatPromptTemplate` | `instructions="..."` |
| run once | `.invoke(...)` | `await Runner.run(agent, ...)` |
| run many | `.batch([...])` — built in, concurrent | `asyncio.gather(...)` — you write it |
| stream tokens | `.stream(...)` | `Runner.run_streamed(...)` + event filter |
| async | `.ainvoke` / `.abatch` / `.astream` | async by default |
| compose steps | `prompt \| llm \| parser` (LCEL) | no composition — the agent is the unit |
| typed output | `llm.with_structured_output(Model)` | `output_type=Model` |
| define a tool | `@tool` | `@function_tool` |
| tool schema from | type hints + docstring | type hints + docstring |
| build an agent | `create_agent(model, tools, system_prompt)` | `Agent(model, instructions, tools)` |
| multi-agent | middleware / subgraphs | handoffs, `agent.as_tool()` |

### The control features

| You wanted to… | LangChain v1 | OpenAI Agents SDK |
|---|---|---|
| stop a runaway loop | `ModelCallLimitMiddleware(run_limit=…)` | `max_turns=` |
| cap one tool | `ToolCallLimitMiddleware(tool_name=…)` | write the check inside the tool |
| validate input / output | middleware (`PIIMiddleware`, summarisation…) | `@input_guardrail` / `@output_guardrail` |
| ask a human before a tool | `HumanInTheLoopMiddleware` | `needs_approval=True` on the tool |
| remember a conversation | a checkpointer + `thread_id` | `SQLiteSession` |
| handle a tool error | `ToolErrorMiddleware` (errors halt by default) | the error goes back to the model |

> **Two philosophies.** LangChain gives you *pieces that compose* — everything is a Runnable
> with the same four methods. The SDK gives you *one object that does the whole job*. Neither
> is wrong; they optimise for different things.

**The important thing:** nothing in either column changes **who decides the order of steps**.

---

## 3. The limitation: who owns the control flow

### The setup

A Nimbus refund desk with three tools:

| Tool | Does |
|---|---|
| `get_order(order_id)` | product, amount paid, days since delivery |
| `get_policy(topic)` | the returns policy, as text |
| `issue_refund(order_id, amount_inr)` | **moves real money** |

The policy: *full refund only if delivered within the last 7 days; outside that, offer a
warranty repair.*

Two orders:

| Order | Amount | Delivered | Eligible? |
|---|---|---|---|
| N104455 | ₹4,999 | 3 days ago | yes |
| N104470 | ₹2,499 | 20 days ago | **no** |

### One customer: both agents are correct

> *"Customer wants a refund for order N104470. Handle it."*

Both frameworks: `get_order` → `get_policy` → refuse politely, offer a warranty repair.
**No money moved.** This is the demo everyone shows, and where most tutorials stop.

### Two customers: both agents pay out

> *"Customers want refunds for orders N104455 and N104470. Handle both."*

Nothing else changed — same agent, same tools, same policy it quoted correctly one moment ago.

| | LangChain `create_agent` | OpenAI Agents SDK |
|---|---|---|
| tool order | order, order, policy, refund, refund | order, order, refund, refund |
| read the policy? | yes | **no — never called it** |
| N104455 (eligible, ₹4,999) | ₹4,999 ✓ | **₹2,499 ✗** |
| N104470 (**not** eligible) | **₹2,499 ✗** | **₹4,999 ✗** |

The SDK run swapped the amounts *and* paid out the larger sum on the order that wasn't
eligible. Across four rehearsal runs each, **both frameworks refunded the ineligible order in
4 out of 4 runs**; the SDK skipped the policy lookup in 2 of 4 and got amounts wrong in 2 of 4.

Your runs will differ in the details. **That variation is the finding.**

### The diagnosis

| What you wrote | What the model decided |
|---|---|
| a goal | which tool to call |
| three tools | in what order |
| some advice in a prompt | how many times |
| | when to stop |

The model did not forget the policy — the policy was in its context. It simply **isn't bound
by it**, because the policy was a *suggestion in a prompt*, not a *gate in the code*.

### "Just write a stricter prompt"

It genuinely helps: four failures in four might become one in ten. Two problems remain.

1. **One in ten is still real money**, every day, forever.
2. **You cannot prove it.** There is no test you can write that says "this agent can never
   refund outside the window". The only evidence available is *"it didn't last time"*.

A prompt shifts the odds. It never gives you a guarantee.

---

## 4. What the control knobs actually do

| Control | What it really does | What it cannot do |
|---|---|---|
| `max_turns` · `ModelCallLimitMiddleware` | stops a runaway loop | make the right call happen |
| `ToolCallLimitMiddleware` | caps how often a tool runs | decide *which* call was allowed |
| guardrails · middleware | check input and output at the edges | reorder the steps in between |
| `needs_approval` · HITL middleware | pause for a human | automate the rule |
| a stricter prompt | shift the odds | give you a guarantee |

Run the live example in the notebook: `ToolCallLimitMiddleware(tool_name="issue_refund",
run_limit=1)` does fire — exactly one refund goes out instead of two. But it blocked **the
second** call, not the **wrong** one. Had the model refunded the ineligible order first, the
limit would have blocked the legitimate refund instead.

**Every control in both SDKs is a fence around the loop. None of them is the path through it.**

---

## 5. Python first: `TypedDict` and `Annotated`

LangGraph carries your data in a **state** object, and state is a `TypedDict`.

### A plain dict doesn't protect you

```python
order = {"order_id": "N104455", "amount_inr": 4999}
order["amount_inr"] = "four thousand nine hundred"   # a string now. Python does not care.
order["amuont_inr"] = 4999                           # typo → brand new key. Python does not care.
```

Both are bugs that surface three functions later as something unrelated.

### A TypedDict declares the shape

```python
from typing import TypedDict

class RefundState(TypedDict):
    order_id: str
    amount_inr: int
    days_since_delivery: int
    eligible: bool
    reply: str
```

| | plain `dict` | `TypedDict` |
|---|---|---|
| the shape is | in your head | in the code |
| a typo | silently adds a key | flagged by your editor / type checker |
| wrong type | silently stored | flagged by your editor / type checker |
| autocomplete | nothing | every field |
| at runtime | a dict | **the same dict — zero cost** |

> `TypedDict` is documentation your editor can check. In a graph where fifteen nodes share one
> state object, that is the difference between a readable system and a haunted one.

**Note:** `TypedDict` is *not* validation. Nothing raises at runtime if you put a string in an
`int` field. If you want enforcement, use a Pydantic model as your state instead — LangGraph
accepts either.

### `Annotated`: attaching an instruction to a field

```python
from typing import Annotated
import operator

class State(TypedDict):
    log: Annotated[list[str], operator.add]   # "when two nodes write log, ADD, don't overwrite"
```

`Annotated[T, something]` means "the type is `T`, and here is extra information for whoever
cares". LangGraph reads that second element as the **reducer** for the field. See §10.

---

## 6. The LangGraph mental model

Stop thinking **loop**. Start thinking **map**.

| Word | What it is |
|---|---|
| **State** | one typed dict that travels through the whole run |
| **Node** | a plain Python function: state in, *partial update* out |
| **Edge** | an arrow from one node to the next — **you** draw it, so **you** own the order |
| **Conditional edge** | an arrow with a question: a function that reads state and returns the next node's name |

Two more you'll meet next session: **checkpointer** (save state after every step) and
**interrupt** (pause mid-run for a human).

Three things that trip people up early:

1. **A node returns only what it changes**, not the whole state. LangGraph merges it.
2. **A graph is control flow, not AI.** An LLM is one kind of node. In a good design, usually
   the minority.
3. **A compiled graph is a Runnable** — `.invoke()`, `.batch()`, `.stream()` — exactly like a
   LangChain chain. Everything from Week 12 still applies.

---

## 7. Your first graph

Four steps, every time: **blueprint → nodes → edges → compile.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class Greeting(TypedDict):
    name: str
    greeting: str
    length: int

def make_greeting(state: Greeting) -> dict:        # a NODE
    return {"greeting": f"Namaste, {state['name']}!"}

def measure(state: Greeting) -> dict:
    return {"length": len(state["greeting"])}

b = StateGraph(Greeting)                           # 1. blueprint, typed by the state
b.add_node("make_greeting", make_greeting)         # 2. nodes
b.add_node("measure", measure)
b.add_edge(START, "make_greeting")                 # 3. edges — the order is yours
b.add_edge("make_greeting", "measure")
b.add_edge("measure", END)
graph = b.compile()                                # 4. compile → a runnable graph

graph.invoke({"name": "Priya"})
# {'name': 'Priya', 'greeting': 'Namaste, Priya!', 'length': 15}
```

`START` and `END` are built-in markers, not nodes you write. `compile()` validates the map —
unreachable nodes, dangling edges — and fails loudly if it doesn't hold together.

### Seeing the graph

```python
from IPython.display import Image, display
display(Image(graph.get_graph().draw_mermaid_png()))   # needs internet
print(graph.get_graph().draw_mermaid())                # offline fallback: Mermaid text
```

That picture is **generated from the code**, so it can never drift from what actually runs.
Ask yourself how you'd produce the same picture for an agent loop. You can't — the path only
exists at run time, inside the model.

---

## 8. Conditional edges: branching you can test

```python
def choose_lane(t: Ticket) -> Literal["auto_reply", "escalate"]:
    return "escalate" if t["severity"] >= 4 else "auto_reply"

b.add_conditional_edges("triage", choose_lane)
```

The router is a plain function. It receives the state and returns the **name** of the next
node. No model, no prompt, no API call.

```
                        ┌─ severity ≥ 4 ─▶ escalate
  triage (LLM) ──▶ ? ───┤
                        └─ otherwise  ───▶ auto_reply
```

Notice the division of labour:

- the **model** reads messy human text and scores it — judgement;
- the **router** applies the threshold identically every time — a rule.

And now the rule is testable:

```python
assert choose_lane({"severity": 5}) == "escalate"
assert choose_lane({"severity": 3}) == "auto_reply"
```

No API key, no flakiness, runs in CI. **You cannot write that test against an agent loop.**
That is the whole pitch.

---

## 9. Cycles: loops with a budget

Point an edge at a node you've already visited and you have a loop — retries, refinement,
re-planning.

```python
def short_enough(d: Draft) -> Literal["write", "__end__"]:
    if len(d["text"].split()) <= 12:
        return END              # exit 1: the goal
    if d["attempts"] >= MAX_ATTEMPTS:
        return END              # exit 2: the budget
    return "write"              # the back-edge
```

> **Every loop you draw needs two exits: the goal and the budget.**

That's Week 10's `max_steps`, drawn as an edge instead of buried in a `while`. If you forget
both, LangGraph still catches you: `recursion_limit` (default **25** steps) raises
`GraphRecursionError` rather than spinning forever.

```python
graph.invoke(state, {"recursion_limit": 50})   # raise it deliberately when you need to
```

---

## 10. Reducers: how updates merge

By default, a node's update **replaces** the value of a key:

```python
history: list[str]
# node A returns {"history": ["a"]},  node B returns {"history": ["b"]}
# final state: {"history": ["b"]}          ← A's work is gone
```

A **reducer** says how to combine instead:

```python
history: Annotated[list[str], operator.add]
# final state: {"history": ["a", "b"]}     ← appended
```

| Reducer | An update… | Use it for |
|---|---|---|
| *(none)* | replaces the value | one value: a draft, a flag, an outcome |
| `operator.add` | appends to the list | a log, a path, collected results |
| `add_messages` | appends, or replaces a message with the same id | chat history (`MessagesState`) |

> **A list that mysteriously loses items is almost always a missing reducer.** It is the most
> common LangGraph bug, and it is silent.

Reducers also matter when two branches run **in parallel** and both write the same key — without
one, LangGraph raises an error rather than guessing. (More on that in session 3.)

---

## 11. The refund desk, rebuilt as a graph

### The design decision

Before any code, decide who owns each step:

| Step | Owner | Why |
|---|---|---|
| read the order | code | it's a lookup |
| is it within 7 days? | **code** | it's a rule, not a judgement |
| how much to refund | **code** | it's in the order record |
| write the customer's reply | **model** | that's language, and models are good at it |

> **Model where you need judgement. Code where you need a guarantee.**

### The graph

```python
class Refund(TypedDict):
    order_id: str
    order: dict
    eligible: bool
    reason: str
    refunded_inr: int
    reply: str

WINDOW_DAYS = 7

def fetch_order(s):
    return {"order": ORDERS.get(s["order_id"], {})}

def check_eligibility(s):              # the node that makes the guarantee
    o = s["order"]
    if not o:
        return {"eligible": False, "reason": "unknown order"}
    days = o["delivered_days_ago"]
    return {"eligible": days <= WINDOW_DAYS,
            "reason": f"delivered {days} days ago, window is {WINDOW_DAYS}"}

def refund(s):
    o = s["order"]
    issue_refund(s["order_id"], o["amount_inr"])      # amount from the RECORD, not the model
    return {"refunded_inr": o["amount_inr"]}

def write_reply(s):                    # the only LLM: it writes, it does not decide
    ...

def eligible_or_not(s) -> Literal["refund", "write_reply"]:
    return "refund" if s["eligible"] else "write_reply"

b.add_edge(START, "fetch_order")
b.add_edge("fetch_order", "check_eligibility")
b.add_conditional_edges("check_eligibility", eligible_or_not)
b.add_edge("refund", "write_reply")
b.add_edge("write_reply", END)
```

```
  fetch_order ──▶ check_eligibility ──┬── eligible ─────▶ refund ──┐
                                      │                            ▼
                                      └── not eligible ───▶ write_reply ──▶ END
```

**There is no path from `check_eligibility` to `refund` unless `eligible` is `True`.** Not "the
model was told not to" — there is no arrow.

### The result

```
N104455  eligible=True   refunded=4999   (delivered 3 days ago, window is 7)
N104470  eligible=False  refunded=0      (delivered 20 days ago, window is 7)
```

The amount comes from the order record, so it cannot be swapped or zeroed. And the policy is
now a unit test:

```python
assert check_eligibility({"order": {"delivered_days_ago": 3}})["eligible"] is True
assert check_eligibility({"order": {"delivered_days_ago": 7}})["eligible"] is True    # boundary
assert check_eligibility({"order": {"delivered_days_ago": 8}})["eligible"] is False   # boundary
assert check_eligibility({"order": {}})["eligible"] is False                          # unknown
```

Milliseconds, offline, on every commit. **"Predictable" isn't a feeling — it's a test.**

### Seeing inside a run

```python
for step in graph.stream({"order_id": "N104470"}, stream_mode="updates"):
    for node, update in step.items():
        print(node, "→", update)

# fetch_order        → {'order': {...}}
# check_eligibility  → {'eligible': False, 'reason': 'delivered 20 days ago, window is 7'}
# write_reply        → {'reply': '...'}
```

Every node, in order, with exactly what it changed. No guessing about what the model "decided".

---

## 12. Agent loop or graph? A decision guide

| | **Agent loop** (SDK / `create_agent`) | **Graph** (LangGraph) |
|---|---|---|
| who picks the next step | the model | your edges |
| best for | open-ended research, Q&A, exploration | rules, approvals, audit trails, pipelines |
| when the path is | discovered | known, or policy |
| cost and latency | variable | predictable |
| testing | run it and hope | assert on the path |
| debugging | read a transcript | read state after each node |
| failure mode | silent wrong action | a loud, visible branch |
| example | *"why did Orbit's rating drop in March?"* | *"never refund outside 7 days"* |

**It is not either/or.** Most production systems are a graph on the outside with a model
deciding inside one node — the shape you'll build for the rest of this week.

Reach for a graph when a wrong step costs money, trust, or an audit finding. Reach for an agent
loop when the whole point is that you don't know the steps.

---

## 13. Cheat sheet

```python
from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, START, END

# 1. state
class S(TypedDict):
    question: str
    answer: str
    attempts: int
    log: Annotated[list[str], operator.add]     # reducer: append instead of replace

# 2. nodes — plain functions, return PARTIAL updates
def node_a(s: S) -> dict:
    return {"answer": "...", "log": ["node_a ran"]}

# 3. router — returns the NAME of the next node
def route(s: S) -> Literal["node_a", "__end__"]:
    return "node_a" if s["attempts"] < 3 else END

# 4. wire it
b = StateGraph(S)
b.add_node("node_a", node_a)
b.add_edge(START, "node_a")
b.add_conditional_edges("node_a", route)
graph = b.compile()

# 5. run it
graph.invoke({"question": "...", "attempts": 0, "log": []})
for step in graph.stream({...}, stream_mode="updates"):   # watch each node
    print(step)
print(graph.get_graph().draw_mermaid())                   # see the map
```

**Rules of thumb**

- A node returns only the keys it changes.
- A list that loses items is a missing reducer.
- Every loop gets a goal exit *and* a budget exit.
- Put the model where you need judgement; put code where you need a guarantee.
- If you can't draw it on paper, don't build it yet.

---

## 14. Exercises

1. **Break it yourself.** Rerun the two-order cell three times. Record the tool order and the
   money each time. How many runs break the policy?
2. **Try to fix it with a prompt.** Rewrite the system prompt to be as strict as you can, then
   rerun five times. How close to zero do you get — and can you ever be *sure*?
3. **Add a node.** Put a `fraud_check` between `fetch_order` and `check_eligibility` that
   declines anything over ₹10,000 without a manager. Where does the edge go, and what new state
   field do you need?
4. **Add a cycle.** If `write_reply` produces more than 60 words, send it back to be rewritten —
   at most twice.
5. **Reducer hunt.** Remove `Annotated[list[str], operator.add]` from the draft loop and rerun.
   Explain in one sentence what you see and why.

---

## What's next

- **Session 2 —** `create_agent` rebuilt by hand as a graph you can modify; checkpoints and
  memory; time travel (rewind a run, change one fact, watch the decision flip).
- **Session 3 —** humans in the loop with `interrupt()`, persistence that survives a restart,
  and an agent that repairs its own code against hidden tests.
- **Session 4 —** teams of agents: parallel fan-out with `Send`, subgraphs, and a supervisor.

**Reference:** [LangGraph docs](https://langchain-ai.github.io/langgraph/) ·
versions used here: `langgraph 1.2.11`, `langchain 1.4.2`, `openai-agents 0.22.3`.
