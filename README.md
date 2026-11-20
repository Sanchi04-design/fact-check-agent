# Truth Layer: Marketing & Sales PDF Fact-Check Agent

> **An evidence-first fact-checking web application that audits marketing decks, press releases, and whitepapers against live web data to flag hallucinations, outdated statistics, and fabricated claims—providing verified real facts with primary citations.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Live Application

- **Production URL:** *[Deploying to Streamlit Community Cloud — see deployment section below]*
- **Repository:** https://github.com/sanchit-sharma/truth-layer-factcheck-agent *(or user-configured remote)*

---

## Overview & Architecture

Marketing and sales collateral frequently contain outdated metrics, hallucinated benchmark figures, or outright fabricated claims. Traditional LLM-based fact-checkers rely on internal model weights, causing hallucinations or stale verifications. 

**Truth Layer** operates strictly as an evidence-first system combining **Tavily Live Web Search** with **Google Gemini** for impartial evidence judgment:
1. **Never trusts internal model memory** for verification.
2. Injects today's date into every verification prompt to accurately distinguish current facts from outdated numbers.
3. Uses **Tavily Search** to discover live authoritative web evidence, saving API credits with targeted queries and in-memory caching.
4. Uses **Gemini** (WITHOUT search tools) solely to judge the retrieved evidence snippets and assign rigorous verdicts.
5. Surfaces audited claims with color-coded verdict badges, supporting quotes, real-world corrections, and clickable source links strictly mapped from cited evidence.

```
┌───────────────────────┐
│ Upload PDF Document   │
└──────────┬────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: Claim Extraction (Gemini + pdfplumber)         │
│ - pdfplumber extracts digital page text                │
│ - Gemini extracts empirical claims (max 25)            │
│ - Generates {claim, page, quote, search_query}         │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Live Web Search (Tavily)                       │
│ - Targeted search query per claim                      │
│ - Basic search depth to conserve free credits          │
│ - In-memory query caching prevents redundant calls     │
│ - Extracts title, URL, published date, and snippets    │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Evidence-First Judgment (Gemini)               │
│ - Max 3 concurrent verification workers (temp=0.0)     │
│ - Evaluates claim strictly against numbered snippets   │
│ - Requires cited evidence for Verified verdicts        │
│ - Maps cited evidence back to verified primary sources │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 4: Auditable Reporting & CSV Export               │
│ - Summary metrics count per verdict                    │
│ - Color-coded claim cards with corrected real facts    │
│ - Escaped, auditable CSV download via session state    │
└────────────────────────────────────────────────────────┘
```

---

## Verdict Definitions

| Verdict | Definition | Required Action |
|---|---|---|
| **🟢 Verified** | Retrieved authoritative search evidence directly corroborates the claim. | Citation links provided; claim confirmed. (Must cite evidence). |
| **🟡 Inaccurate** | Reliable evidence demonstrates the claim is outdated, partially wrong, or numerically inaccurate. | Real corrected figure and effective reference date provided. |
| **🔴 False** | Reliable evidence contradicts the claim, OR exhaustive search finds zero evidence for an implausible/fabricated assertion. | Debunking explanation and real facts provided. |
| **⚪ Unverifiable** | Search failed, evidence was insufficient/ambiguous, or a technical failure occurred. | Explicit technical or evidential reason recorded. |

> [!IMPORTANT]
> **Prompt-Injection Safe & Strict Corrections:**
> Search snippets and URLs are treated strictly as evidence, never as instructions. If an inaccurate or false claim cannot have its real figure reliably established, the system explicitly reports *"No reliable correction could be confirmed from the retrieved sources."* rather than inventing a number.

---

## API Keys & Setup

Truth Layer requires two free API keys:
1. **Google Gemini API Key:** Obtain from [Google AI Studio](https://aistudio.google.com/).
2. **Tavily Search API Key:** Obtain 1,000 free searches/month from [app.tavily.com](https://app.tavily.com/).

### Key Resolution Hierarchy
Keys are resolved securely without hardcoding:
1. `st.secrets["GEMINI_API_KEY"]` & `st.secrets["TAVILY_API_KEY"]` (Streamlit Secrets)
2. Environment variables via `.env` (loaded with `python-dotenv`)
3. Interactive user password inputs in the Streamlit sidebar

The model is configured via `GEMINI_MODEL` (default: `gemini-3.5-flash-lite`).

---

## Local Development & Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone and Setup Environment
```bash
git clone <repo-url>
cd cog_culture_fact\ agent

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### 3. Configure API Credentials
Create a `.env` file in the project root:
```bash
cp .env.example .env
# Edit .env with your keys:
# GEMINI_API_KEY="your-gemini-api-key"
# TAVILY_API_KEY="tvly-your-tavily-api-key"
# GEMINI_MODEL="gemini-3.5-flash-lite"
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Test Suite & Trap Document Evaluation

### Running Automated Tests
```bash
PYTHONPATH=. pytest tests/ -v
```
All unit tests cover:
- PDF digital text extraction, page tagging, empty PDF detection, and scanned/image-only PDF detection.
- Markdown fence stripping and JSON regex parsing fallbacks.
- Pydantic schema validation for claims, verifications, and results.
- Tavily search result parsing, snippet truncation, and query caching.
- Client-side verdict enforcement: Verified requires cited evidence; otherwise downgrades to Unverifiable.
- Evidence index mapping strictly back to Tavily source URLs and titles.
- CSV export formatting and special-character escaping.
- Parallel worker execution with partial failures handled gracefully.

### The Trap Document Benchmark
A reproducible benchmark trap document (`sample_trap.pdf`) was generated using `generate_trap_pdf.py` containing 10 intentional claims across 4 categories:
1. **Verified Facts:** Microsoft Activision acquisition ($69B, Oct 2023), Python 3.0 release (Dec 2008), Apple Q4 FY24 revenue ($94.9B).
2. **Outdated Figures:** Global human population (7.2B presented as 2026 stat; actually surpassed 8.0B in 2022 and ~8.1B in 2024–2026), Tesla deliveries (499,550 presented as 2024; actually 2020 figure, 2024 was ~1.79M).
3. **Numerically Incorrect Numbers:** Shopify Q3 2024 revenue ($4.8B claimed vs $2.16B actual), Eiffel Tower height (150m claimed vs 330m actual).
4. **Fabricated Claims:** Stripe acquiring Spotify in March 2024 for $45B (completely fabricated), Anthropic founded in 1998 by Steve Jobs and Bill Gates (founded in 2021 by Dario/Daniela Amodei).

See [`answer_key.md`](answer_key.md) for the human-verified ground-truth answers.

---

## Deployment to Streamlit Community Cloud

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy Truth Layer Fact-Check Agent"
   git push -u origin main
   ```
2. **Deploy on Streamlit Community Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **"New app"**.
   - Select your repository, branch (`main`), and set the main file path to `app.py`.
   - Click **"Advanced settings..."** -> **Secrets**.
   - Paste your configuration:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     TAVILY_API_KEY = "tvly-..."
     GEMINI_MODEL = "gemini-3.5-flash-lite"
     ```
   - Click **"Deploy!"**.

---

## Design Notes & Limitations

- **No Scanned OCR:** Truth Layer uses `pdfplumber` to extract digital text directly. Image-only or scanned PDFs without text layers are detected and rejected with a friendly message instructing the user to upload a digital PDF.
- **Claim Cap:** Extraction is capped at 25 claims per document to guarantee fast interactive turnaround and avoid rate limits.
- **Credit Conservation:** Search depth is set to `"basic"` by default, queries are deduplicated with an in-memory cache, and claims are limited to 1 Tavily call per claim.
- **Session State Persistence:** Results and downloaded CSVs persist in `st.session_state` so interacting with filters or controls does not trigger expensive re-runs.
- **Worker Concurrency:** Limited to 3 concurrent workers to respect free-tier rate limits for both Gemini and Tavily.
