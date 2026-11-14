# The Transformer — a component-by-component guide

Companion to the deck *Transformers — Architecture Deep Dive*. Read it before the session for
the ideas, after the session as a reference while you read the code.

**The code:** [`notebooks/01_transformer_from_scratch.ipynb`](notebooks/01_transformer_from_scratch.ipynb)
builds every component in this guide from bare PyTorch and trains it to translate
English → French from 73 sentence pairs. Each section of the notebook maps onto a
section here. It runs on a laptop CPU in well under a minute and needs no API key.

This follows the same order as Jay Alammar's **[The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)**,
which you should read alongside it — the diagrams there are the best in the field.

---

## Contents

1. [Why the transformer exists](#1-why-the-transformer-exists)
2. [The shape of the whole model](#2-the-shape-of-the-whole-model)
3. [Tokens and embeddings](#3-tokens-and-embeddings)
4. [Positional encoding](#4-positional-encoding)
5. [Self-attention: the idea](#5-self-attention-the-idea)
6. [Self-attention: the maths](#6-self-attention-the-maths)
7. [A worked numeric example](#7-a-worked-numeric-example)
8. [Multi-head attention](#8-multi-head-attention)
9. [The rest of the block: FFN, residual, layer norm](#9-the-rest-of-the-block)
10. [The decoder: masking and cross-attention](#10-the-decoder)
11. [The output head, training and generation](#11-the-output-head-training-and-generation)
12. [Counting the parameters](#12-counting-the-parameters)
13. [What came after](#13-what-came-after)
14. [Reading list](#14-reading-list)

> **Guide section → notebook section:** 3 → §1–2 · 4 → §2 · 5–7 → §3 · 8 → §4 ·
> 9 → §6 · 10 → §5, §7 · 11 → §10, §13 · 12 → §6, §8

---

## 1. Why the transformer exists

Before 2017, sequence models were recurrent. An RNN or LSTM reads a sentence one token at a
time, carrying a hidden state forward:

```
h₁ = f(x₁, h₀)  →  h₂ = f(x₂, h₁)  →  h₃ = f(x₃, h₂)  →  …
```

Two consequences, and both are fatal at scale:

**It cannot be parallelised.** Step *t* needs the output of step *t−1*. A 500-token sequence is
500 sequential operations no matter how many GPUs you own.

**Distant words are far apart.** For word 1 to influence word 50, its information passes
through 49 transformations. Gradients shrink along that path, so long-range relationships are
learned poorly — the vanishing gradient problem that LSTMs reduced but never removed.

The transformer's claim was that the recurrence was the bottleneck, not the modelling. Replace
it with **attention**, where every position can read every other position directly — one hop,
in parallel — and the architecture both trains faster *and* models long-range structure better.

> The paper's title is a statement of the result: *Attention Is All You Need* (Vaswani et al.,
> 2017). They removed recurrence entirely and the model got better.

---

## 2. The shape of the whole model

The original transformer is an **encoder–decoder** model, built for translation.

```
  "je suis étudiant"                                        "I am a student"
         │                                                          ▲
         ▼                                                          │
   ┌───────────┐                                           ┌───────────┐
   │ Encoder 1 │                                           │ Decoder 1 │
   │ Encoder 2 │ ──── memory: keys and values ───────────▶ │ Decoder 2 │
   │    ...    │                                           │    ...    │
   │ Encoder 6 │                                           │ Decoder 6 │
   └───────────┘                                           └───────────┘
```

- The **encoder** reads the whole source sentence at once and produces one vector per source
  token — a contextualised representation.
- The **decoder** produces the translation one token at a time. At each step it looks at what
  it has written so far, *and* at the encoder's output.
- The bridge is **cross-attention**, in every decoder layer.

Three things to notice:

1. **The layers are identical in structure** and identical in shape. Input and output of every
   layer are `(sequence_length, d_model)`. Nothing narrows or widens. This is why "make it
   deeper" is a configuration change, and a large part of why scaling worked.
2. **Six is not magic.** The paper used 6; GPT-3 used 96; small models use 4. It is a knob.
3. **Both halves are optional.** Keep only the encoder and you get BERT. Keep only the decoder
   and you get GPT. The full pair is for sequence-to-sequence tasks like translation.

---

## 3. Tokens and embeddings

### Tokenisation

Models do not see characters or words; they see **token ids** from a fixed vocabulary
(typically 30k–100k entries). Tokens are **sub-words**, learned with an algorithm such as BPE
or WordPiece:

```
"students are learning"  →  ["stud", "##ents", "are", "learn", "##ing"]
                         →  [7204, 2015, 2024, 4299, 3070]
```

Why sub-words? A word-level vocabulary cannot spell words it has never seen; a character-level
vocabulary makes sequences far too long. Sub-words give a fixed vocabulary that can spell
anything, keeping common words whole and splitting rare ones.

This is also why token counts never match word counts in your API bills, and why unusual names
and non-English text cost more tokens.

### Embeddings

The embedding layer is a learned lookup table of shape `(vocab_size, d_model)`. Token id 7204
selects row 7204.

```python
embedding = nn.Embedding(vocab_size, d_model)   # e.g. (37000, 512)
x = embedding(token_ids)                        # (seq_len,) -> (seq_len, 512)
```

`d_model` is the width of the entire model; the paper used 512.

**The key limitation at this stage:** the vector for a token is the same every time, regardless
of context. "bank" in *river bank* and in *bank loan* start identical. Giving a token a
representation that depends on its neighbours is precisely the job of attention.

---

## 4. Positional encoding

Self-attention computes a **weighted sum over all positions**. A sum does not care about order,
so without help the model would treat *"dog bites man"* and *"man bites dog"* as the same input.

The fix is to add a position-dependent vector to each token embedding:

```
input_to_layer_1 = token_embedding + positional_encoding      # both (seq_len, d_model)
```

The original paper used fixed sinusoids:

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

Each dimension is a sine wave of a different frequency, so every position gets a distinct
pattern, the values stay bounded, and the encoding extrapolates beyond the training length.
A useful property: the encoding of position *pos + k* is a linear function of the encoding of
*pos*, which makes relative offsets learnable.

**Addition, not concatenation.** Concatenating would widen the model. Adding keeps the width at
`d_model` and leaves it to training to keep the two signals separable — which it does, because
the position signal occupies predictable frequency bands.

**What modern models do:** learned absolute positions (BERT, GPT-2), or **rotary embeddings
(RoPE)**, which rotate the query and key vectors inside attention by an angle that depends on
position. RoPE is what most current open models use; it handles long contexts better.

---

## 5. Self-attention: the idea

Take the sentence:

> The animal didn't cross the street because **it** was tired.

To represent *"it"* well, the model must know *it* refers to *the animal*. Self-attention lets
the representation of *"it"* be built partly from the representation of *"animal"*.

Every token produces three different vectors, each from its own learned projection:

| Vector | Intuition |
|---|---|
| **Query (Q)** | what I am looking for |
| **Key (K)** | what I advertise about myself to anyone searching |
| **Value (V)** | what I hand over if you attend to me |

```
Q = X·W_Q      K = X·W_K      V = X·W_V
```

A useful analogy is a library search. Your **query** is the request you type. Each book's
**key** is its spine label. The **value** is the book's contents. You do not read one book —
you read a blend of all of them, weighted by how well each spine matched your request. That
blend is the output of attention.

The crucial point: Q, K and V are three *views of the same token*, produced by three different
learned matrices. That is the only reason a token can simultaneously ask a question and answer
someone else's.

---

## 6. Self-attention: the maths

The whole operation is one line:

```
Attention(Q, K, V) = softmax( Q·Kᵀ / √d_k ) · V
```

Four steps:

**1 — Score.** `Q·Kᵀ` compares every query with every key. For *n* tokens, the result is an
`n × n` matrix; cell (i, j) is how much token *i* should attend to token *j*.

**2 — Scale.** Divide by `√d_k`. Dot products of `d_k`-dimensional vectors grow with `d_k`;
large values push softmax into a flat region where gradients vanish. This is a numerical fix,
not a modelling idea.

**3 — Weight.** `softmax` over each row turns the scores into a probability distribution: each
token's attention over all tokens sums to 1.

**4 — Mix.** Multiply by `V`. Each output row is a weighted average of all value vectors.

### Shapes

For one head, a 10-token sentence, `d_model = 512`, `d_k = 64`:

| Tensor | Shape |
|---|---|
| `X` (input) | (10, 512) |
| `W_Q`, `W_K`, `W_V` | (512, 64) |
| `Q`, `K`, `V` | (10, 64) |
| `Q·Kᵀ` | (10, 10) |
| `softmax(...)` | (10, 10), rows sum to 1 |
| output | (10, 64) |

If you can explain why `Q·Kᵀ` is 10×10 and what one cell of it means, you understand attention.

```python
import torch, math

def attention(Q, K, V, mask=None):
    scores = Q @ K.transpose(-2, -1) / math.sqrt(Q.size(-1))   # (n, n)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float("-inf"))
    weights = scores.softmax(dim=-1)                           # rows sum to 1
    return weights @ V, weights
```

---

## 7. A worked numeric example

Three tokens, `d_k = 2`, numbers chosen to be readable.

```
Q = [[1, 0],      K = [[1, 0],      V = [[10,  0],
     [0, 1],           [0, 1],           [ 0, 10],
     [1, 1]]           [1, 1]]           [ 5,  5]]
```

**Scores** `Q·Kᵀ`:

```
          k₁   k₂   k₃
   q₁ →  [ 1    0    1 ]
   q₂ →  [ 0    1    1 ]
   q₃ →  [ 1    1    2 ]
```

**Scale** by `√2 ≈ 1.414`:

```
   q₁ →  [0.71  0.00  0.71]
   q₂ →  [0.00  0.71  0.71]
   q₃ →  [0.71  0.71  1.41]
```

**Softmax** each row:

```
   q₁ →  [0.42  0.21  0.42]      (ties between token 1 and token 3)
   q₂ →  [0.21  0.42  0.42]
   q₃ →  [0.25  0.25  0.50]      (token 3 attends mostly to itself)
```

**Mix** with `V` — row 3, for instance:

```
0.25·[10,0] + 0.25·[0,10] + 0.50·[5,5]  =  [2.5, 0] + [0, 2.5] + [2.5, 2.5]  =  [5.0, 5.0]
```

Token 3's new representation blends all three values, dominated by its own. Run the same
arithmetic with your own numbers once; it removes most of the mystery.

---

## 8. Multi-head attention

One attention produces one weighted average — a single blurred summary. A sentence usually has
several relationships worth tracking at once: syntax, coreference, the previous token, the
topic.

So run **h attentions in parallel**, each on a slice of the width:

```
d_model = 512,  h = 8  →  d_k = d_v = 512 / 8 = 64

head_i  = Attention(X·W_Qⁱ, X·W_Kⁱ, X·W_Vⁱ)        # each (n, 64)
MultiHead = Concat(head_1 … head_8) · W_O          # (n, 512) · (512, 512) → (n, 512)
```

Two things worth saying out loud:

- **It is free.** Eight heads of width 64 cost the same FLOPs as one head of width 512.
- **Heads specialise on their own.** Interpretability work finds heads that track
  subject–verb agreement, heads that attend to the previous token, heads that resolve
  pronouns. Nobody designed those roles; they emerge from training.

---

## 9. The rest of the block

Each encoder layer is two sublayers, each wrapped the same way:

```
x → multi-head self-attention → add & norm → feed-forward → add & norm → out
```

### Feed-forward network

```
FFN(x) = max(0, x·W₁ + b₁)·W₂ + b₂          # 512 → 2048 → 512
```

Applied **to each position separately and identically**. Attention mixes information *across*
positions; the FFN then processes each position on its own. A reasonable mental model: attention
decides what to look at, the FFN decides what to make of it.

Note the width: it expands 4× and comes back. This is where most of the parameters live — see
§12 — and recent interpretability work treats it as the model's key–value memory of facts.

### Residual connections

```
output = LayerNorm(x + Sublayer(x))
```

The `x +` is a **residual**: it gives gradients a path straight back to earlier layers that does
not pass through the sublayer. Without residuals, stacks beyond a handful of layers do not
train. This single trick (from ResNet, 2015) is what makes depth possible.

### Layer normalisation

Normalises each vector to zero mean and unit variance across its features, then rescales with
learned parameters. It keeps activations in a stable range layer after layer.

The paper put the norm *after* the residual add (post-norm). Most modern implementations put it
*before* the sublayer (pre-norm), which trains more stably at depth. You will see both.

---

## 10. The decoder

The decoder layer has **three** sublayers rather than two, and one extra rule.

### Masked self-attention

While generating, position *t* may attend only to positions 1…*t*. The future does not exist
yet. During training the whole target sentence is present, so we must hide it explicitly:

```
scores = scores.masked_fill(future_positions, float("-inf"))   # -inf → softmax gives 0
```

Visually, the allowed region is a lower triangle:

```
         I   am   a   stu
  I    [ ✓    ·   ·    ·  ]
  am   [ ✓    ✓   ·    ·  ]
  a    [ ✓    ✓   ✓    ·  ]
  stu  [ ✓    ✓   ✓    ✓  ]
```

Without the mask the model can see the answer it is being asked to predict. It would reach
near-perfect training loss and produce nonsense at inference — a bug that looks like success.

### Cross-attention

The second sublayer uses the same attention formula, with a different wiring:

- **Queries** come from the decoder (what I am trying to write next)
- **Keys and values** come from the **encoder output** (what the source sentence says)

This is the only place the source enters the output path. In translation, this is where
*étudiant* influences *student*.

Decoder-only models such as GPT drop this sublayer entirely and keep the mask — there is no
separate source to attend to.

---

## 11. The output head, training and generation

The top of the decoder produces a vector per position. To turn it into a word:

```
logits = decoder_output · W_vocab        # (n, 512) · (512, 37000) → (n, 37000)
probs  = softmax(logits)
```

### Training

All positions are predicted **in parallel**, each compared with the true next token using
cross-entropy loss. One forward pass teaches the model about the entire sentence. This is why
training parallelises so well.

### Generation

Inference is sequential: predict a token, append it, run the model again. This asymmetry —
parallel training, sequential generation — is why text generation is slow even though
transformers are "parallel", and why KV caching (reusing the keys and values already computed)
matters so much in serving.

Everything you have tuned through an API acts on that final distribution:

| Setting | What it does to `probs` |
|---|---|
| greedy | take the argmax |
| temperature | divide the logits before softmax — higher flattens, lower sharpens |
| top-k | keep the k most likely, renormalise, sample |
| top-p (nucleus) | keep the smallest set whose probability sums to p, renormalise, sample |

**The model never outputs a word. It outputs a distribution; the sampler chooses.**

---

## 12. Counting the parameters

Worth doing once, for `d_model = 512`, `d_ff = 2048`, one encoder layer:

| Component | Parameters |
|---|---|
| W_Q, W_K, W_V (all heads together) | 3 × 512 × 512 = 786,432 |
| W_O | 512 × 512 = 262,144 |
| **Attention total** | **~1.05 M** |
| FFN W₁ (512 × 2048) | 1,048,576 |
| FFN W₂ (2048 × 512) | 1,048,576 |
| **FFN total** | **~2.10 M** |

So **two-thirds of each layer's parameters are in the feed-forward network**, not in attention.
Most people guess the other way round. It reframes the question of where a model's knowledge
is stored.

The embedding matrix (37,000 × 512 ≈ 19 M) is often the single largest tensor in a small model,
which is why input and output embeddings are frequently tied.

---

## 13. What came after

| Model | Change | Why it mattered |
|---|---|---|
| **BERT** (2018) | encoder only, masked-token training | strong representations for classification and retrieval |
| **GPT** (2018→) | decoder only, next-token training | generation; scaled to today's LLMs |
| **T5** (2019) | full encoder–decoder, every task as text-to-text | one architecture for everything |
| **ViT** (2020) | image patches as tokens | transformers stopped being about language |
| **RoPE, FlashAttention, GQA** | positional and efficiency changes | long contexts and cheaper serving |

The architecture in this guide is still recognisable in all of them. What changed is scale,
position handling, normalisation placement, and attention efficiency — not the core idea.

---

## 14. Reading list

**Start here**
- Jay Alammar, [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) — the diagrams this session follows
- Jay Alammar, [The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/) — decoder-only models and masking
- Jay Alammar, [Visualizing Attention](https://jalammar.github.io/visualizing-neural-machine-translation-mechanics-of-seq2seq-models-with-attention/) — attention before transformers, useful context

**Then**
- [The Annotated Transformer](https://nlp.seas.harvard.edu/annotated-transformer/) (Harvard NLP) — the paper as runnable code, line by line
- Vaswani et al., [Attention Is All You Need](https://arxiv.org/abs/1706.03762) — short, readable, worth the hour
- Andrej Karpathy, [Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY) — two hours, builds the whole thing live

**Going deeper**
- [The Illustrated Retrieval Transformer](https://jalammar.github.io/illustrated-retrieval-transformer/)
- Elhage et al., [A Mathematical Framework for Transformer Circuits](https://transformer-circuits.pub/2021/framework/index.html) — what heads actually learn

---

## A short self-test

If you can answer these without looking, you have it:

1. Why does `Q·Kᵀ` have shape *n × n*, and what does one cell mean?
2. Why divide by `√d_k`?
3. What would break if positional encodings were removed?
4. Why is multi-head attention not more expensive than single-head?
5. Where do most of the parameters in a layer live?
6. What exactly does the decoder mask prevent, and what would training look like without it?
7. In cross-attention, where do Q, K and V each come from?
8. Why is training parallel but generation sequential?
