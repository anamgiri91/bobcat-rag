# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

what each professor actually tests, whether they curve, what office hours are worth, and which section to take to best fit your needs at Texas State University. This domain is really useful as someone looking at classes and professors ends up spending hours reading professor reviews, grading criteria and other things which are not normally described in course catalog. This process can be simplied by a RAG pipeline with all this data, which helps a student decide which professor to study with quickly.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Subreddit : r/txst |  This subreddit thread covers what students think are good professors for 3358 and 2318. | https://www.reddit.com/r/txstate/comments/1c0xw5d/advice_about_cs_professors_cs_33582318
| 2 | TXST official catalog website | This is the offcial course catalog for CS at TXST. It is useful for contrasting with what students say.|  https://mycatalog.txstate.edu/courses/cs/
| 3 | TXST CS faculty page|This gives an overview of what subject professors teach.|https://cs.txst.edu/people/faculty.html |
| 4 | Rate my professor| This gives professor Koh lee's rate my professor reviews for courses taught at TXST |https://www.ratemyprofessors.com/professor/56546 |
| 5 | Rate my professor| This gives professor Husain Gholoom rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1755852 |
| 6 | Rate my professor| This gives professor Martin Burtscher rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1508396 |
| 7 | Rate my professor| This gives professor Mina Guirguis rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1118377 |
| 8 | Rate my professor| This gives professor Oleg Komogortsev rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1132554 |
| 9 | Rate my professor| This gives professor Jill Seaman rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1828652 |
| 10 | Rate my professor| This gives professor Ted Lehr rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1909698 |
| 11 | Rate my professor| This gives professor Ted Lehr rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1909698 |
| 12 | Rate my professor| This gives professor Keshav Bhandari rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/2676876 |
| 13 | Rate my professor| This gives professor Apan Qasem rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/1071081 |
| 14 | Rate my professor| This gives professor Edwin Vargas rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/2494994 |
| 15 | Rate my professor| This gives professor Trevi Kelley rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/2922018 |
| 16 | Rate my professor| This gives professor Xiaomin Li rate my professor reviews for courses taught at TXST | https://www.ratemyprofessors.com/professor/2831104 |
---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
