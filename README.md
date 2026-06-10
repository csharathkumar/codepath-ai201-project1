# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system covers the Rutgers University CS undergraduate program — specifically courses and professors, from the perspective of students who have taken them. This knowledge is valuable because the official department website only provides course synopses and faculty bios, which say nothing about actual student experience: which professors explain concepts clearly, which courses have brutal exams, how workload compares across sections, or which electives are worth taking. Students currently piece this together from scattered Reddit threads, RateMyProfessors reviews, and word of mouth. This guide centralizes that unofficial peer-sourced knowledge into a single queryable system.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Reddit r/rutgers — CS professors | Reddit posts + comments | https://www.reddit.com/r/rutgers/ |
| 2 | Reddit r/rutgers — CS112/CS213 core courses | Reddit posts + comments | https://www.reddit.com/r/rutgers/ |
| 3 | Reddit r/rutgers — CS electives | Reddit posts + comments | https://www.reddit.com/r/rutgers/ |
| 4 | Reddit r/rutgers — CS314/CS336 upper courses | Reddit posts + comments | https://www.reddit.com/r/rutgers/ |
| 5 | RateMyProfessors — Rutgers CS professors | Student reviews (manual export) | https://www.ratemyprofessors.com/search/professors/826?q=* |
| 6 | USACS Resources page | Student org resource list | https://usacs.rutgers.edu/resources |
| 7 | Rutgers CS Course Synopses (official) | Official course descriptions | https://www.cs.rutgers.edu/academics/undergraduate/course-synopses |
| 8 | Rutgers CS Course Structure (official) | Program requirements | https://www.cs.rutgers.edu/academics/undergraduate/computer-science-course-structure |
| 9 | vverma.net — Succeeding in Rutgers CS | Student blog post | http://www.vverma.net/succeeding-in-rutgers-cs.html |
| 10 | USACS Medium — CS Electives Review | Student-written course guide | https://medium.com/@rutgersusacs/rutgers-cs-electives-review-4b5ee979de2 |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Why these choices fit your documents:** The source documents are short-form by nature — Reddit comments, RateMyProfessors reviews, and blog paragraphs are typically 1–4 sentences. Using large chunks (1000+ characters) would bundle multiple professors or courses into a single chunk, making retrieval imprecise: a query about CS213 would return a chunk that's mostly about CS111. At 400 characters, each chunk typically covers one review or one course description, keeping the semantic signal focused. The 50-character overlap preserves sentence continuity at chunk boundaries so that a subject (like a professor's name) at the end of one chunk reappears at the start of the next, preventing broken attribution.

**Final chunk count:** approximately 250–300 chunks across 8 loaded documents (2 source files were manual-only and stored locally).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Production tradeoff reflection:** `all-MiniLM-L6-v2` was chosen because it runs entirely locally with no API key or rate limits, has a 256-token context window that fits the short chunks well, and produces embeddings quickly even on a laptop CPU. For a production deployment where cost was not a constraint, I would evaluate several tradeoffs. First, accuracy on domain-specific slang: this corpus uses informal language ("weed-out course", professor nicknames like "Uli", abbreviations like "RMP") that a general-purpose model may not handle as well as a fine-tuned academic or forum-domain model. Second, context length: OpenAI's `text-embedding-3-small` supports much longer inputs, which would allow larger chunks and potentially cleaner semantic signals for longer Reddit threads. Third, latency: for a real-time web interface with many concurrent users, a locally hosted model creates a bottleneck; an API-hosted model with caching would scale better. Multilingual support would matter if serving international students.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt enforces grounding through explicit prohibition rather than suggestion:

```
STRICT RULES — you must follow these exactly:
1. Answer ONLY using information from the CONTEXT section provided below.
2. Do NOT use any knowledge from your training data about Rutgers, professors, or courses.
3. Do NOT make up or infer opinions, ratings, or facts not present in the context.
4. If the context contains partial information, use it and note that coverage is limited.
5. Only say "I don't have enough information on that in my documents." if the context
   contains zero relevant information about the topic.
6. Keep your answer concise and specific — quote or closely paraphrase the source material.
7. Do not add a sources section — sources will be appended separately.
```

The temperature is set to 0.2 to reduce creative generation and keep responses close to the retrieved text. Chunks with a cosine distance above 0.85 are filtered out before being sent to the LLM — if no chunks pass that threshold, the system returns a hardcoded "I don't have enough information" without calling the LLM at all.

**How source attribution is surfaced in the response:**

Source attribution is handled programmatically, not by the LLM. After generation, the code extracts the `source` metadata field from each retrieved chunk (stored in ChromaDB at embed time), deduplicates the filenames, and appends them to the response as a separate "Sources" field. This guarantees attribution is always present and always accurate — the LLM cannot fabricate or omit sources.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about CS213 Software Methodology? | Hard course, heavy Java, multiple projects, varies by professor | "The context only provides a brief overview stating it 'Deep dives into other aspects of Java and builds multiple projects.' No additional student feedback." | Partially relevant — CS213 content was in retrieved chunks but mixed with CS336 content, diluting the signal | Partially accurate — correct description but lacks student opinion depth |
| 2 | Which CS professors at Rutgers are known for being good teachers? | Names like Tjang, Cowan cited as clear and helpful | Named Professors Zhang, Cowan, and Michmizos with specific descriptions: Zhang's lectures are "easy to follow," Cowan "makes complex topics understandable," Michmizos has "engaging lectures" | Relevant — RMP chunks with professor reviews retrieved correctly | Accurate — specific names and reasons drawn directly from source reviews |
| 3 | Is CS336 Databases worth taking? | Generally recommended, practical SQL skills, some professors better than others | "CS336 covers ER diagrams, SQL queries, and functional dependencies. It's straightforward and can be a GPA booster, especially with Professor Miranda Garcia." | Relevant — top chunks at distance 0.46 and 0.48 directly about CS336 | Accurate — matches student consensus in the source documents |
| 4 | What are the easiest CS electives at Rutgers? | Electives review should surface lower-difficulty options like CS210 | "I don't have enough information on that in my documents." | Off-target — retrieved chunks were from USACS resources and course structure pages rather than the electives review | Inaccurate — relevant content exists in reddit_cs_electives.txt but was not retrieved for this query phrasing |
| 5 | How hard is CS112 Data Structures? | Known as a weed-out course; exams are the primary challenge | "I don't have enough information on that in my documents." | Partially relevant — chunks from reddit_cs_core_courses.txt were retrieved at distance 0.59–0.60 and contained CS112 advice, but chunks also included RTF artifacts and mixed CS112/CS213 content | Inaccurate — the LLM declined to synthesize from the noisy partial context |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "How hard is CS112 Data Structures?"

**What the system returned:** "I don't have enough information on that in my documents."

**Root cause (tied to a specific pipeline stage):** The failure occurs across two pipeline stages. First, in the **chunking stage**: the Reddit documents that discuss CS112 also discuss CS213 in the same sections ("General Tips for CS112 and CS213"). Because the chunker splits on fixed character boundaries rather than topic boundaries, the retrieved chunks contain advice about both courses merged together, diluting the CS112-specific signal in each chunk. Second, in the **cleaning stage**: one of the most relevant CS112 chunks (from `reddit_cs_core_courses.txt`) began with RTF font metadata artifacts (`HelveticaNeue-Bold; HelveticaNeue; ; ; ; ;`) that the `strip_rtf()` function did not fully remove. The LLM received this noisy preamble ahead of the actual CS112 advice and, given the strict grounding instruction requiring it to answer only from clear source material, chose to refuse rather than synthesize from content it could not reliably parse as substantive.

**What you would change to fix it:** Two targeted fixes would address this. First, improve the RTF stripping to catch font name artifacts — specifically, add a regex to remove lines matching `FontName; FontName; ; ; ;` patterns before chunking. Second, use a paragraph-based or sentence-based splitter for the Reddit documents instead of fixed character splitting, so that a section titled "Specific Advice for CS112" stays in its own chunk rather than sharing space with CS213 tips. This would produce a cleaner, higher-signal chunk that the LLM could answer from confidently.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The planning.md chunking strategy section forced me to commit to a chunk size (400 characters) and justify it before writing any code. This turned out to be directly useful during Milestone 3 debugging — when I saw chunks that mixed multiple courses together, I had a concrete spec to compare against and a documented rationale to reason from. Without that pre-commitment, I might have kept adjusting the chunk size arbitrarily based on vibes rather than reasoning about document structure.

**One way your implementation diverged from the spec, and why:**

The spec called for a single fixed chunk size across all documents. During implementation I discovered that the RateMyProfessors file had been saved in RTF format, which produced chunks full of formatting codes that the cleaner only partially resolved. Rather than handling this at the chunking stage (by using a different chunk size for that file), I added RTF stripping as a pre-processing step in `clean_text()`. This diverged from the spec by adding a cleaning stage that wasn't planned, but it was the right call — the alternative would have been to require all source files to be manually converted before ingestion, which doesn't scale.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Domain, Documents, Chunking Strategy, Retrieval Approach, and Architecture sections from `planning.md`, plus the milestone instructions for Milestone 3.
- *What it produced:* A complete `ingest.py` with `load_documents()`, `clean_text()`, and `chunk_text()` functions matching the specified 400-character chunk size and 50-character overlap, plus an inspection function that printed 5 random chunks and chunk statistics.
- *What I changed or overrode:* The initial `clean_text()` function handled HTML but not RTF. After running the script and seeing RTF formatting codes in the chunks from `rmp_rutgers_cs.txt`, I asked the AI to add an `strip_rtf()` function that detects RTF by checking for `{\rtf` or `\pard` near the start of the file and strips control words before the HTML cleaning runs. I also added a directory check in `load_documents()` after encountering an `IsADirectoryError` on a folder that had been incorrectly created with a `.txt` name.

**Instance 2**

- *What I gave the AI:* The Retrieval Approach section from `planning.md` (embedding model, top-k=5, ChromaDB with cosine similarity), the pipeline diagram, and the Milestone 4 instructions.
- *What it produced:* `embed.py` with `embed_and_store()` using `SentenceTransformer("all-MiniLM-L6-v2")`, ChromaDB upsert with source metadata, and a `retrieve()` function returning chunks with distance scores. It also added color-coded distance quality labels (strong/ok/weak) in the test output.
- *What I changed or overrode:* The initial system prompt in `generate.py` was too strict — it caused the LLM to return "I don't have enough information" even when relevant chunks were retrieved, because it interpreted "answer only from context" as requiring a complete, dedicated answer rather than a partial one. I directed the AI to add a rule permitting partial answers when the context contains limited but relevant information, while still prohibiting training-data fallback. I also changed the distance filter threshold from 0.7 to 0.85 after observing that valid CS112 and CS213 chunks were being excluded at 0.7.
