# Truth Layer: Fact-Check Agent

A web app that audits marketing and sales PDFs. It extracts specific claims (statistics, dates, financial and technical figures), verifies each against live web evidence, and flags inaccuracies with the correct real facts and source links.

**Live app:** https://fact-checker-agent.streamlit.app/

## How it works

1. **Extract:** `pdfplumber` reads the PDF page by page. Gemini extracts the checkable claims, each with its page number, the exact supporting quote, and a targeted web search query.
2. **Search:** Tavily runs one live web search per claim and returns titles, URLs, snippets and dates.
3. **Verify:** Gemini compares each claim with the retrieved evidence only. It does not use its own memory to confirm a claim.
4. **Report:** Each claim gets a verdict, the corrected fact with a reference date, an explanation, a confidence level, and clickable sources. Results can be downloaded as CSV.

## Verdicts

| Verdict | Meaning |
|---|---|
| Verified | Current evidence supports the claim |
| Inaccurate | The claim is outdated, partly wrong, or numerically incorrect; the correct figure is shown |
| False | Evidence contradicts the claim, or it is a fabricated assertion with no support |
| Unverifiable | Search failed, or the evidence is missing, ambiguous or insufficient |

## Reliability safeguards

- A Verified verdict requires at least one cited evidence item; otherwise it is downgraded to Unverifiable.
- Source links shown to the user come only from the evidence the model cited, never from model-generated URLs.
- Evidence text is treated as data, not instructions, to reduce prompt-injection risk.
- API failures are shown as Unverifiable with the error and never silently converted into False. One failing claim does not stop the others.
- Retries use bounded exponential backoff. Verification runs with limited concurrency to respect free-tier quotas.

## Tech stack

Python, Streamlit, pdfplumber, Google Gemini (`google-genai`), Tavily Search API, pydantic, pandas.

## Run locally

```bash
git clone <your-repo-url>
cd <repo-folder>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your keys
streamlit run app.py
```

`.env`:
```
GEMINI_API_KEY=your-gemini-key
TAVILY_API_KEY=your-tavily-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

## Deploy (Streamlit Community Cloud)

1. Push the repo to GitHub.
2. At share.streamlit.io, create an app from the repo: branch `main`, main file `app.py`.
3. In Advanced settings → Secrets, add:
```toml
GEMINI_API_KEY = "..."
TAVILY_API_KEY = "..."
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

## Testing

- `pytest tests/` covers PDF extraction, JSON parsing, schema validation, search and evidence handling, the Verified-needs-evidence rule, failure isolation and CSV export.
- `sample_trap.pdf` is a 10-claim test document with true, outdated, incorrect and fabricated claims. It is reproducible with `generate_trap_pdf.py`.
- `answer_key.md` lists the expected verdict and real fact for each claim. `test_report.md` compares the observed live results against it (`run_live_eval.py`).
- Observed result: <e.g. all trap claims flagged with the correct real facts; one claim got Inaccurate where the key expected False>.

## Limitations

- Scanned (image-only) PDFs are not supported (no OCR).
- Results depend on the quality of search results; always check the cited sources.
- To stay within free-tier quotas, at most <40> claims are checked per document.
- Free API quotas (Gemini and Tavily) may limit heavy use.

## Repository structure

```
app.py                 Streamlit UI
factcheck.py           Extraction, search, verification pipeline
tests/                 Unit tests
generate_trap_pdf.py   Builds the sample trap document
run_live_eval.py       Runs the live evaluation on the trap PDF
sample_trap.pdf        Test document
answer_key.md          Expected results
test_report.md         Observed results
requirements.txt       Runtime dependencies
dev-requirements.txt   Test/dev dependencies
```