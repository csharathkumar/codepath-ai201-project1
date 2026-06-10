# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Rutgers University CS program — specifically courses and professors. This knowledge is valuable because the official department website only lists course synopses and faculty bios. It does not reflect actual student experience: which professors explain concepts clearly, which courses have brutal exams, how workload compares across sections, or which electives are worth taking. Students currently piece this together from scattered Reddit threads, RateMyProfessors reviews, and word of mouth. This guide centralizes that unofficial knowledge.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit r/rutgers | Threads about CS course advice, professor recommendations, and major tips | https://www.reddit.com/r/rutgers/ |
| 2 | RateMyProfessors — Rutgers CS | Student reviews of Rutgers CS professors | https://www.ratemyprofessors.com/search/professors/826?q=* |
| 3 | USACS Medium — CS Electives Review | Student-written review of popular CS elective courses | https://medium.com/@rutgersusacs/rutgers-cs-electives-review-4b5ee979de2 |
| 4 | USACS Medium — Succeeding in Rutgers CS | Guest post with patterns of success/failure in the Rutgers CS program | https://medium.com/@rutgersusacs/guest-post-succeeding-in-rutgers-computer-science-by-v-48e6a5b75efb |
| 5 | vverma.net — Succeeding in Rutgers CS | Original blog post with detailed course and professor advice | http://www.vverma.net/succeeding-in-rutgers-cs.html |
| 6 | Rutgers CS Course Synopses (official) | Official descriptions used as baseline for comparison with student opinions | https://www.cs.rutgers.edu/academics/undergraduate/course-synopses |
| 7 | Rutgers CS Course Structure (official) | Program requirements and course sequencing | https://www.cs.rutgers.edu/academics/undergraduate/computer-science-course-structure |
| 8 | USACS Resources page | Student-curated list of guides and resources for CS majors | https://usacs.rutgers.edu/resources |
| 9 | Uloop — Rutgers CS Course Notes | Student-submitted notes and Q&As for CS courses including CS336 | https://rutgers.uloop.com/course-notes/3244-CS |
| 10 | CourseHero — Rutgers CS | Student-uploaded study materials and reviews for core CS courses | https://www.coursehero.com/sitemap/schools/22-Rutgers-University/departments/3244-CS/ |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 50 characters

**Reasoning:** The source documents are mostly short-form: Reddit posts, professor reviews (1–3 sentences each), and blog paragraphs. Long chunks (1000+ characters) would bundle multiple professors or courses into one chunk, making retrieval imprecise — a query about CS213 would return a chunk that's 80% about CS111. Small chunks (400 characters) keep each chunk focused on one professor or one course. A 50-character overlap preserves sentence continuity at chunk boundaries without significant redundancy.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:** `all-MiniLM-L6-v2` is fast and free but has a 256-token context limit, which fits our short chunks well. For production, I would evaluate `text-embedding-3-small` (OpenAI) for higher accuracy on domain-specific academic slang (e.g., "weed-out course", professor nicknames) and longer context. I would also consider a multilingual model if serving international students. Latency matters less than accuracy for this use case since queries are ad-hoc, not real-time.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about CS213 (Systems Programming)? | Hard course, heavy C programming, varies a lot by professor, important to take seriously |
| 2 | Which CS professors at Rutgers are known for being good teachers? | Names like Andrew Tjang, Wesley Cowan cited as clear and helpful |
| 3 | Is CS336 (Databases) worth taking? | Generally recommended, practical, some professors better than others |
| 4 | What are the easiest CS electives at Rutgers? | Electives review should surface lower-difficulty options |
| 5 | How hard is CS112 (Data Structures)? | Known as a weed-out course; exams are the primary challenge; important to nail early |

---

## Anticipated Challenges

1. **Professor nickname mismatch:** Students often refer to professors by nickname or last name only (e.g., "Tjang", "Uli") while source documents may use full names. The embedding model may not link "Uli" to "Ulrich Kremer" without exact overlap, causing missed retrievals.

2. **Chunk boundary splits:** A Reddit comment might discuss two courses in the same post. If chunked at a fixed character boundary, one chunk might end mid-sentence about CS213 and begin mid-thought about CS314, making neither chunk retrieval-accurate for either course.

---

## Architecture

```
Documents (Reddit posts, RMP reviews, blog posts, official pages)
        |
        v
[Milestone 3] Document Ingestion
  - Load .txt files from documents/ folder
  - Strip HTML/markdown formatting
        |
        v
[Milestone 3] Chunking
  - Split by 400 characters, 50-character overlap
  - Library: Python string slicing or LangChain CharacterTextSplitter
        |
        v
[Milestone 4] Embedding
  - Model: all-MiniLM-L6-v2 (sentence-transformers)
  - Embed each chunk into a vector
        |
        v
[Milestone 4] Vector Store
  - Store vectors + chunk text + source metadata in ChromaDB
        |
        v
[Milestone 4] Retrieval
  - Embed user query, cosine similarity search, return top-5 chunks
        |
        v
[Milestone 5] Grounded Generation
  - Pass top-5 chunks as context to Groq LLM
  - System prompt enforces: answer only from context, cite sources
        |
        v
[Milestone 5] Query Interface
  - Gradio or Streamlit UI for user to type questions and see answers
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I will give Claude this Chunking Strategy section and ask it to implement `ingest.py` with a `load_documents(folder_path)` function that reads all `.txt` files and a `chunk_text(text, chunk_size=400, overlap=50)` function. I will verify the output by printing chunk counts and spot-checking that no chunk exceeds 400 characters.

**Milestone 4 — Embedding and retrieval:**
I will give Claude the Retrieval Approach section and ask it to implement `embed.py` with functions to embed chunks using `all-MiniLM-L6-v2` and store them in ChromaDB, and `retrieve.py` with a `query(question, top_k=5)` function. I will verify by running a test query and checking that returned chunks are topically relevant.

**Milestone 5 — Generation and interface:**
I will give Claude the Grounded Generation section of README.md (once drafted) and ask it to implement `generate.py` using the Groq API with a system prompt that enforces grounding. I will then ask it to wrap this in a Gradio interface. I will verify by running my 5 evaluation questions and checking that the model does not hallucinate beyond the retrieved context.
