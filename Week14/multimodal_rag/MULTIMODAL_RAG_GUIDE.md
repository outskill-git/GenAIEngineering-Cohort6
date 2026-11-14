# Multimodal RAG — a practical guide

Companion to the deck *Multimodal RAG — images and video* and the notebook
`notebooks/01_multimodal_rag.ipynb`. Read it before the session to get the ideas, after the
session as a reference.

Everything here was run. The numbers, the failures and the CLIP results come from the saved
notebook run, not from a blog post.

---

## Contents

1. [The problem in one sentence](#1-the-problem-in-one-sentence)
2. [Why text RAG cannot see a figure](#2-why-text-rag-cannot-see-a-figure)
3. [Strategy A — caption and index](#3-strategy-a--caption-and-index)
4. [Strategy B — joint embedding with CLIP](#4-strategy-b--joint-embedding-with-clip)
5. [Strategy C — retrieve, then look](#5-strategy-c--retrieve-then-look)
6. [Video](#6-video)
7. [Evaluation](#7-evaluation)
8. [Choosing, costing and scaling](#8-choosing-costing-and-scaling)
9. [Pitfalls](#9-pitfalls)
10. [What we did not cover](#10-what-we-did-not-cover)
11. [Reading](#11-reading)

---

## 1. The problem in one sentence

> Retrieval is similarity search in a vector space, and in ordinary RAG everything in that
> space is text — so a fact that exists only in a picture is not in the index at all.

That is the whole session. Everything else is the three ways to fix it.

It matters because real knowledge bases are not text. They are scanned manuals, screenshots,
dashboards, invoices, product photographs, wiring diagrams, slide decks, recorded training.
In our corpus — four text pages, ten images, one video — **four of the most useful facts exist
nowhere in the text**:

| The technician asks | Where the answer actually lives |
|---|---|
| What does fault code E-27 mean? | a photograph of a sticker inside the inverter cover |
| What torque for the DC terminals? | a callout inside wiring figure 4.2 |
| When did PUN-114's yield collapse? | a bar chart |
| How long to wait after isolating? | spoken at 00:22 in a training video |

---

## 2. Why text RAG cannot see a figure

Run ordinary RAG over the text documents and ask those four questions. It answers none of them.

The important detail is **how** it fails. It does not hallucinate — it says the context does not
contain the answer. Retrieval is working correctly; the information was simply never indexed.
That tells you this is not a prompting problem and no amount of prompt tuning will fix it.

It is an **indexing** problem, and there are exactly three ways to put a picture into an index.

---

## 3. Strategy A — caption and index

**Idea:** at indexing time, show each image to a vision model and store what it says. You are
converting pictures into text once, then reusing the entire text pipeline you already own.

```python
CAPTION_PROMPT = """Describe this image for a search index used by solar field technicians.

Write one dense paragraph. State what kind of asset it is (chart, wiring diagram, equipment
label, specification page, photograph). Then transcribe EVERY number, code, label and unit you
can read, exactly as printed — fault codes, torque values, voltages, dates, site ids, axis
values. If it is a chart, say what it shows and name the notable values. Do not speculate about
anything you cannot see."""

caption = ask_with_image(CAPTION_PROMPT, image_path)

doc = Document(page_content=f"{name}\n{caption}",
               metadata={"source": name, "modality": "image", "path": str(image_path)})
```

Index those documents next to your text chunks. One store, one embedding model, no new
infrastructure. The image path rides along in the metadata so you can show or re-read the
original later.

### The captioning prompt is the whole ballgame

This is the part people get wrong. "Describe this image" produces *"a chart showing daily
energy output for a solar site"* — which makes the chart findable by topic and useless for any
specific question.

Our prompt demands numbers, codes and labels **verbatim**. That is the only reason the string
`E-27` ends up in the index, and therefore the only reason the question is answerable.

> **The caption is the ceiling.** Anything it omits is invisible for ever — not degraded,
> invisible. You cannot retrieve what you did not write down.

Exercise 1 in the notebook has you re-caption with a lazy prompt and watch which questions
break first. Do it; it makes the point better than any explanation.

### Where it shines, and where it does not

Excellent for documents, charts, labels, screenshots, spec sheets — anything where the meaning
is carried by text and structure. That is most enterprise content.

It cannot do visual similarity. If a technician photographs a burnt connector and asks "have we
seen this before", you would have to caption the query image first, and a caption is a lossy
description of a picture. Which leads to the next strategy.

---

## 4. Strategy B — joint embedding with CLIP

**Idea:** use a model trained to put an image and its caption in the **same** vector space, so
you can compare a picture with a sentence directly.

CLIP (Contrastive Language–Image Pre-training, OpenAI 2021) was trained on hundreds of millions
of image–text pairs with one objective: pull matching pairs together and push non-matching pairs
apart. The result is a space where *"a burnt electrical connector"* and a photograph of one are
neighbours.

```python
from sentence_transformers import SentenceTransformer, util

clip = SentenceTransformer("clip-ViT-B-32")          # ~600 MB, runs locally, free
image_vectors = clip.encode(images, convert_to_tensor=True, normalize_embeddings=True)

q = clip.encode(["a burnt electrical connector"], convert_to_tensor=True, normalize_embeddings=True)
scores = util.cos_sim(q, image_vectors)[0]            # one score per image
```

The same `encode` call accepts a PIL image, which is what makes **image-as-query** possible —
the only strategy of the three that can do it.

### What it actually did on our corpus

| Query | Top result | Verdict |
|---|---|---|
| "a photograph of solar panels on a roof" | `photo_rooftop_array.png` | correct |
| "a burnt electrical connector" | `photo_mc4_connector_burnt.png` | correct |
| "a bar chart of daily energy output" | *a* chart | cannot tell which one |
| "an electrical wiring diagram" | often the warning label | wrong |
| "a photograph of a dog" | returns three images anyway | there are no dogs |

Two honest failures worth sitting with:

**It does not read text reliably.** Our two yield charts differ only in the printed numbers.
CLIP sees two bar charts. For "which chart shows the collapse", it cannot help.

**It has no concept of "no match".** Cosine similarity always returns a ranking. Ask for a dog
in a corpus of solar equipment and you get three confident results. In production this is a
*silent* failure, and worse than a text one because an image looks like an answer.

> If you retrieve with CLIP, set a score threshold and handle the empty case explicitly.
> Exercise 2 asks you to find the threshold that separates the dog query from the real ones.

### Where it shines

Photographs, scenes, objects, conditions, and anything where the user's query *is* a picture.
In the notebook we crop and shrink the burnt-connector photo to simulate a fresh field photo;
CLIP still retrieves the right asset first. A caption index cannot do that without an extra
vision call on the query.

---

## 5. Strategy C — retrieve, then look

**Idea:** retrieve as usual, then attach the retrieved image to the answering prompt and let the
vision model read it at answer time.

```python
content = [{"type": "text", "text": prompt_with_text_context}]
for path in retrieved_image_paths[:3]:                 # cap it — images are expensive
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    content.append({"type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}})

answer = llm.invoke([{"role": "user", "content": content}]).content
```

The retriever decides *which* picture; the vision model extracts the *detail*. This recovers
anything the caption left out — a value on an axis, the third row of a table, a small label in
a corner.

The cost moves from indexing to query time: an image in every prompt, rather than one vision
call per asset ever.

### The combination that works in production

> **Index captions. Attach images.**

Captions make retrieval cheap, searchable and compatible with your existing stack. Attaching the
retrieved image makes the answer accurate. That single line is most of production multimodal
RAG, and it is what `multimodal_rag()` in the notebook does.

---

## 6. Video

A video is not one object. It is **two aligned streams** — what was said, and what was shown —
and the unit of retrieval is a **time range**, not a file.

### The transcript does the retrieving

Speech is usually the higher-signal stream for "where is this discussed". Get a transcript
(Whisper, or a managed speech-to-text service; ours ships with the corpus), then window it:

```python
def window_transcript(segments, size=3, stride=2):
    windows = []
    for i in range(0, len(segments), stride):
        group = segments[i:i + size]
        windows.append(Document(
            page_content=" ".join(s["text"] for s in group),
            metadata={"start_s": group[0]["start_s"], "end_s": group[-1]["start_s"]}))
    return windows
```

Individual transcript segments are too short to embed well — too little context. Overlapping
windows fix that, and carrying the start time is what lets you cite.

**The chunking trade-off:** narrow windows cite precisely and retrieve poorly; wide windows
retrieve well and cite vaguely. Ours are three segments wide, so the citation points at
`00:14–00:32` for a sentence spoken at `00:22`. Exercise 5 explores the trade-off.

### The frames support the answer

Sample stills (one per scene, or every N seconds) and attach the frame nearest the retrieved
timestamp. The viewer gets to see what was on screen, and the vision model can read anything
written there.

If the question is *visual* — "find the part where the torque driver appears" — embed the frames
with CLIP and retrieve over those instead. Same idea as §4, applied to a sequence of stills.

### Cite the timestamp

```
best segment: 00:14   frame: t014.png
"You must wait five minutes after isolating before opening the inverter lid, because the
 capacitors inside stay charged. (00:14-00:32)"
```

A timestamp is checkable. A file name is not.

---

## 7. Evaluation

Score **retrieval** and **answering** separately. They fail for different reasons and have
different fixes:

| What is wrong | What to fix |
|---|---|
| the right asset never came back | the index: captioning prompt, chunking, embedding model |
| right asset, wrong answer | the prompt: attach the image, demand the value be read off |

> Fixing the wrong one of those two is the most common way to waste a week.

Our eight-question evaluation, run end to end:

| | Text-only | Multimodal |
|---|---|---|
| retrieved the right asset | 2 / 8 | **8 / 8** |
| answered correctly | 2 / 8 | **8 / 8** |

Same retriever, same model, same questions. The only difference is what was put in the index.

One nuance that showed up while building this: an early version of the rubric failed a *correct*
answer because the model read "4.3 kWh" off a chart where the rubric said "4.2". Reading a value
off a chart is approximate — write rubrics that accept a range, or you will spend your time
debugging the judge rather than the system.

---

## 8. Choosing, costing and scaling

| | Caption + index | CLIP | Retrieve then look |
|---|---|---|---|
| indexing cost | one vision call per image | cheap, local | none |
| query cost | normal text RAG | very cheap | an image per question |
| reads text in images | as well as the captioner did | no | yes, in full |
| query can be an image | no | **yes** | no |
| visual similarity | no | **yes** | no |
| new infrastructure | none | an image embedding model | none |
| best for | documents, charts, labels | photographs | detail questions |

**Default:** caption for retrieval, attach the image for the answer. Add CLIP when users will
search with pictures or by visual similarity.

### At 10,000 images

- Captioning is a one-off batch job — parallelise it, cache by file hash, and re-run only for
  new or changed assets. Budget one cheap vision call per image.
- Store the caption, the embedding, and the path. Never re-caption at query time.
- CLIP embedding of 10,000 images is minutes on a laptop and costs nothing.
- The recurring cost is query-time images. Cap how many you attach (we cap at three) and
  attach only when the retrieved asset is actually an image.
- Consider a cheap captioner and an expensive answerer. Captions are bulk; answers are few.

---

## 9. Pitfalls

1. **The caption is the ceiling.** Demand numbers, codes and labels verbatim in the captioning
   prompt, or they are unfindable.
2. **Similarity has no zero.** CLIP and text search always return something. Threshold the score
   and handle "no good match" explicitly.
3. **Images dominate the context budget.** One image can cost as much as a page of text. Cap the
   number you attach.
4. **Charts are read, not recalled.** A model asked about a value it cannot see will invent a
   plausible one. Attach the chart and ask it to state the value it read.
5. **Resolution matters.** Downscaling a dense page to save tokens is the usual cause of
   "the model misread the table".
6. **Video needs both streams.** Transcript to find it, frame to show it, timestamp to cite it.
7. **Keep the pointer.** Always store the path to the original asset in metadata. Retrieval
   gives you a caption; your user wants the picture.

---

## 10. What we did not cover

Worth knowing these exist, if you take this further:

- **Document-image retrieval (ColPali / ColQwen).** Instead of extracting text from a PDF,
  embed each *page image* directly with a multi-vector model. Strong on complex layouts where
  text extraction mangles the structure. The current state of the art for PDF RAG.
- **Dedicated multimodal embedding APIs** (for example Cohere Embed v3 multimodal, Voyage
  multimodal) — CLIP-style joint spaces, hosted, usually better than open CLIP on documents.
- **Audio beyond transcripts** — speaker diarisation, non-speech events.
- **Video understanding models** that take a video natively rather than sampled frames.
- **Re-ranking** a shortlist with a cross-encoder or a vision model, which usually buys more
  accuracy than a better embedding model.

---

## 11. Reading

- OpenAI, [the CLIP repository](https://github.com/openai/CLIP) — the original model and card
- Radford et al., [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) — the CLIP paper
- [SentenceTransformers image–text documentation](https://sbert.net/examples/applications/image-search/README.html) — the library used here
- [ColPali: Efficient Document Retrieval with Vision Language Models](https://arxiv.org/abs/2407.01449) — page-image retrieval
- OpenAI, [Vision guide](https://platform.openai.com/docs/guides/vision) — how images are passed and priced
- [LangChain multimodal documentation](https://python.langchain.com/docs/how_to/multimodal_inputs/) — message format for images

---

## Self-test

1. Why does text RAG fail on a fact in a figure, and why is that not a prompting problem?
2. What is the single most important line in a captioning prompt, and why?
3. Name one thing CLIP does that captioning cannot, and one thing captioning does that CLIP cannot.
4. Why does CLIP return results for a query about a dog in a corpus with no dogs?
5. When would you attach the image to the prompt rather than trust the caption?
6. What is the unit of retrieval for video, and what should the citation be?
7. Your system retrieves the right chart but states the wrong value. Which half do you fix?
