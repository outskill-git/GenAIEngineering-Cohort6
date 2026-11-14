# Week 14 — Transformers from scratch · Multimodal RAG

Two sessions. Both notebooks ship **with their outputs saved**, so you can read them
start to finish without running anything.

```
pip install -r requirements.txt
cp .env.example .env        # session 2 only — put your OpenAI key in it
```

---

## Session 1 — The transformer, built from bare PyTorch

`transformers/01_transformer_from_scratch.ipynb`

6 encoder layers + 6 decoder layers, 8 heads, 510,316 parameters, written with nothing
but `nn.Linear`, `nn.LayerNorm` and `softmax` — no `nn.Transformer`, no pretrained
weights, **no API key and no internet**. It learns English → French from 73 sentence
pairs (67 trained on, 6 held back) and trains in about 40 seconds on a laptop CPU.

Twenty labelled sections, one per box in the architecture diagram:

| | |
|---|---|
| 1–2 | tokenizer, teacher forcing, embeddings, positional encoding |
| 3–5 | scaled dot-product attention, multi-head, the padding and causal masks |
| 6–8 | feed-forward, residual, LayerNorm, the encoder and decoder layers, the full stack |
| 9–12 | a shape tour of one sentence, greedy decoding, and the model **before** training |
| 13–14 | the training loop, and how to read the loss curves |
| 15–19 | after training, generalisation, the embedding table, and experiments to try |

Things worth stopping on:

- **Epoch 11 prints `elle aime le elle aime`** — the repetition loop everyone has seen
  an LLM produce, in miniature. Structure is learned before vocabulary.
- **Train loss keeps falling for 1,100 epochs after the output stops changing.** By the
  last epoch it is 171× lower than held-out loss. Loss is not accuracy.
- **5 of the 6 unseen sentences are translated correctly.** The one that fails
  (`you drink the water`) fails for lack of *evidence*, not lack of architecture —
  `tu bois` never appears in training. That one row is the whole case for scale.
- **Cross-attention is offset by one row**, because position *t* predicts word *t+1*.

Companion: `transformers/TRANSFORMERS_GUIDE.md`, which follows Jay Alammar's
*Illustrated Transformer* section by section and maps onto the notebook.

---

## Session 2 — Multimodal RAG over images and video

`multimodal_rag/notebooks/01_multimodal_rag.ipynb` (run it from the `notebooks/`
folder — it looks for `../corpus`)

A field-support corpus for a fictional solar company: 4 manual pages, 10 images and one
82-second training video. **Four critical facts exist only inside an image or the
video** — a fault-code sticker, a torque callout in a wiring figure, a yield-collapse
chart, and a spoken "wait five minutes".

The session is built around one measurement, run live in the notebook:

| over 8 evaluation questions | text-only RAG | multimodal |
|---|---|---|
| retrieved the right source | 2/8 | 8/8 |
| answered correctly | 2/8 | 8/8 |

Covered in order: why text RAG fails here → **caption and index** → **CLIP joint
embeddings** → **retrieve then look** (sending the image itself to a vision model) →
video as transcript windows + keyframes with timestamp citations → evaluating
retrieval and answering separately.

Two honest results kept in the notebook because they teach better than the successes:
CLIP **mis-ranks the wiring diagram** and cannot tell the two yield charts apart (it
does not read text), and asked for "a photograph of a dog" in a corpus with no dogs it
**confidently returns three images** — similarity search has no zero.

Companion: `multimodal_rag/MULTIMODAL_RAG_GUIDE.md`.
`generate_corpus.py` rebuilds the dataset from scratch if you want to change it
(needs `ffmpeg` on your PATH for the video).

> **Before class:** Part 3 downloads a ~600 MB CLIP model on first run. Install
> `sentence-transformers` and run that cell once at home, not on the venue wifi. The
> notebook degrades gracefully and skips Part 3 if the package is missing.
