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

**Truth Layer** operates strictly as an evidence-first system:
1. **Never trusts internal model memory** for verification.
2. Injects today's date into every verification prompt to accurately distinguish current facts from outdated numbers.
3. Uses **Gemini with Google Search Grounding** (`types.Tool(google_search=types.GoogleSearch())`) to discover live authoritative evidence.
4. Requires primary sources (SEC filings, company investor relations, government registries) over secondary blogs.
5. Surfaces audited claims with color-coded verdict badges, supporting quotes, real-world corrections, and clickable source links.

```
┌───────────────────────┐
│ Upload PDF Document   │
└──────────┬────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: Claim Extraction (No Search)                   │
│ - pdfplumber extracts digital page text                │
│ - Gemini identifies empirical claims (max 25)         │
│ - Generates {claim, page, quote} structured JSON       │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Parallel Search Grounding (ThreadPoolExecutor) │
│ - Max 4 concurrent verification workers (temp=0.0)    │
│ - Injects dynamic current date into prompt             │
│ - Live Google Search Grounding via google-genai        │
│ - Extracts grounding metadata chunks (URLs & titles)   │
│ - Validates schema with Pydantic                       │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Auditable Reporting & CSV Export               │
│ - Summary metrics count per verdict                    │
│ - Color-coded claim cards with corrected real facts    │
│ - Escaped, auditable CSV download via session state    │
└────────────────────────────────────────────────────────┘
```

---

## Verdict Definitions

| Verdict | Definition | Required Action |
|---|---|---|
| **🟢 Verified** | Current, authoritative search evidence directly corroborates the claim. | Citation links provided; claim confirmed. |
| **🟡 Inaccurate** | Reliable evidence demonstrates the claim is outdated, partially wrong, or numerically inaccurate. | Real corrected figure and effective reference date provided. |
| **🔴 False** | Reliable contradictory evidence disproves the claim, OR exhaustive search finds zero evidence for an implausible/fabricated statistic. | Debunking explanation and real facts provided. |
| **⚪ Unverifiable** | Search tool failed, grounding chunks were missing, evidence is ambiguous, or no defensible conclusion can be drawn. | Explicit technical or evidential reason recorded. |

> [!IMPORTANT]
> **Prompt-Injection Safe & Strict Corrections:**
> Search snippets and URLs are treated strictly as evidence, never as instructions. If an inaccurate or false claim cannot have its real figure reliably established, the system explicitly reports *"No reliable correction could be confirmed"* rather than inventing a number.

---

## Key Resolution Hierarchy

API keys are resolved securely without hardcoding or committing credentials:
1. `st.secrets["GEMINI_API_KEY"]` (Streamlit Cloud Secrets)
2. `GEMINI_API_KEY` environment variable (loaded from `.env` via `python-dotenv`)
3. Interactive user password input in the Streamlit sidebar

The model name is configurable via `GEMINI_MODEL` (default: `gemini-3.5-flash`).

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
Create a `.env` file in the project root (or `.streamlit/secrets.toml`):
```bash
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env
echo "GEMINI_MODEL=gemini-3.5-flash" >> .env
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
All 12 unit and integration tests cover:
- PDF digital text extraction, page tagging, empty PDF detection, and scanned/image-only PDF detection.
- Markdown fence stripping and JSON regex parsing fallbacks.
- Pydantic schema validation for claims, verifications, and results.
- Grounding metadata deduplication and extraction.
- CSV export formatting and special-character escaping.
- Parallel worker execution with partial failures handled gracefully.

### The Trap Document Benchmark
A reproducible benchmark trap document (`sample_trap.pdf`) was generated using `generate_trap_pdf.py` containing 10 intentional claims across 4 categories:
1. **Verified Facts:** Microsoft Activision acquisition ($69B, Oct 2023), Python 3.0 release (Dec 2008), Apple Q4 FY24 revenue ($94.9B).
2. **Outdated Figures:** Global human population (7.2B presented as 2026 stat; actually surpassed 8.0B in 2022 and ~8.1B in 2024–2026), Tesla deliveries (499,550 presented as 2024; actually 2020 figure, 2024 was ~1.79M).
3. **Numerically Incorrect Numbers:** Shopify Q3 2024 revenue ($4.8B claimed vs $2.16B actual), Eiffel Tower height (150m claimed vs 330m actual).
4. **Fabricated Claims:** Stripe acquiring Spotify in March 2024 for $45B (completely fabricated), Anthropic founded in 1998 by Steve Jobs and Bill Gates (founded in 2021 by Dario/Daniela Amodei).

See [`answer_key.md`](answer_key.md) for the human-verified ground-truth answers.

### Observed Live Evaluation Results
Running `python run_live_eval.py` on `sample_trap.pdf`:
- **Claim Extraction:** 10/10 claims extracted with 100% precision, matching quotes and page numbers.
- **Search Grounding Behavior:** On accounts with free/unbilled Gemini API keys, Google Search grounding returns `429 RESOURCE_EXHAUSTED` (search grounding requires billing enabled in Google AI Studio). The application catches this cleanly, applies bounded exponential retries, preserves all extracted records, marks verdicts as `Unverifiable` with the exact error details, and writes the complete auditable log to [`test_report.md`](test_report.md).

---

## Deployment to Streamlit Community Cloud

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Truth Layer Fact-Check Agent"
   git remote add origin https://github.com/<your-username>/truth-layer-factcheck.git
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
     GEMINI_MODEL = "gemini-3.5-flash"
     ```
   - Click **"Deploy!"**.

---

## Design Notes & Limitations

- **No Scanned OCR:** Truth Layer uses `pdfplumber` to extract digital text directly. Image-only or scanned PDFs without text layers are detected and rejected with a friendly message instructing the user to upload a digital PDF.
- **Claim Cap:** Extraction is capped at 25 claims per document to guarantee fast interactive turnaround and avoid rate limits.
- **Search Grounding Quota:** Live search verification requires a Google AI Studio API key with search grounding quota enabled (paid/tier 1+).
- **Session State Persistence:** Results and downloaded CSVs persist in `st.session_state` so interacting with filters or controls does not trigger expensive re-runs.

---

## 30-Second Demo Video Checklist

1. **Upload:** Drag & drop `sample_trap.pdf` into the PDF uploader.
2. **Launch:** Click **"🚀 Run Fact-Check"**.
3. **Extraction Progress:** Observe status expander reading pages and extracting claims.
4. **Verification Progress:** Observe progress bar updating in real-time as workers verify claims.
5. **Audit Results:**
   - Point out summary metrics cards (Total, Verified, Inaccurate, False, Unverifiable).
   - Filter by "Inaccurate & False (Flagged)".
   - Expand a flagged claim card: highlight the original quote, the color-coded badge, the **Correct Real Fact**, and the clickable source links.
6. **Export:** Click **"📥 Download Audit Report (CSV)"** to demonstrate full auditable export.
