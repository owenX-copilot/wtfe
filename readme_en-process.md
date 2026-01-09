# WTFE — Why The Folder Exists

WTFE is an analysis toolchain for automatically making sense of unfamiliar code and system structure.

Its goal is not to "understand all code," but to answer, with minimal context and human intervention (and even without AI), a recurring engineering question that seldom has a systematic answer:

> "What does this piece of code / this file / this folder / this process actually do?"

---

## Vision

In real projects we often encounter:

- filenames that badly mismatch their contents
- highly abstract, poetic, or intentionally confusing naming
- missing or out-of-date READMEs
- incidents where you only have a `pid` / `port` / `service name`
- AI-generated code that runs but nobody knows what it does

WTFE aims to build an automated path from observed system facts to understandable descriptions.

---

## Core Principles

WTFE does not start from semantic understanding; it uses a layered, incremental, and verifiable analysis model:

### 1) Fact-first

- code structure
- language features
- imported libraries
- concurrency / IO / networking signals
- process and port relationships

Conclusions must be derivable from static or runtime facts.

---

### 2) Rules before AI

AI is not a prerequisite for WTFE.

Baseline capabilities should work without calling any AI, including:

- file structure extraction
- responsibility signal detection
- suspicious complexity tagging
- project-level partitioning

AI is optional and best suited as a final summarization or expression layer.

---

### 3) Bottom-up aggregation

WTFE analyzes at layers rather than jumping straight to "project":

File → Folder → Project → Runtime / Service

Each layer yields independent, reusable, and runnable analysis artifacts.

---

## Logical Modules

WTFE is an analysis framework rather than a single tool. Typical submodules include:

### `wtfe_file`
Single-file analyzer

- Input: a source file
- Output: a structured "file fact" description
- No project context required
- Language-extensible (Python / Java / JS / Go / Rust …)

Key question: *Why does this file exist?*

---

### `wtfe_folder`
Folder-level aggregation

- aggregate file analyses
- infer module responsibilities
- identify utility code / core logic / experimental scraps
- ignore .gitignored and noisy build outputs

Key question: *Why does this folder exist?*

---

### `wtfe_project`
Project-level understanding

- identify project type (service / library / tool / hybrid)
- infer tech stack and runtime patterns
- produce a project-level description (README draft)

Key question: *What kind of project is this?*

---

### `wtfe_runtime` (planned)
Runtime reverse-mapping

- Input: `pid` / `port` / `service name`
- locate the executable
- infer the project root
- combine with static analysis to reconstruct service structure

Key question: *What is actually running and where did it come from?*

---

## Outputs

All WTFE intermediate results are machine-readable JSON artifacts, for example:

- file structure descriptions
- signal and feature summaries
- aggregated statistics

These artifacts can be:

- read by humans
- summarized by AI
- consumed by CI / ops systems
- fed into documentation generators

---

## Relationship with AI

WTFE does not depend on AI, but it pairs naturally with it:

- WTFE handles denoising, trimming, and structuring
- AI handles summarization and expression

This reduces prompt size, context overflow risk, API costs, and hallucination.

---

## What WTFE does not do

- ❌ it does not guarantee business-level semantic correctness
- ❌ it does not replace manual code review
- ❌ it does not perform security vulnerability scanning
- ❌ it does not attempt to read the author's mind

WTFE focuses on engineering reality rather than author intent.

---

## Who benefits

- developers facing large volumes of unfamiliar code
- operators / SREs / systems engineers
- researchers in explainability for AI-generated code
- anyone needing a quick judgment about whether a code area is worth deeper inspection

---

## One-line summary

> WTFE is an engineering approach for extracting the "reason this code exists" from chaos.

It does not promise instant comprehension, but it prevents you from staring at a set of files and not knowing where to start.
