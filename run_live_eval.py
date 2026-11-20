"""
Live Evaluation Script: Auditing sample_trap.pdf with Tavily Live Search + Gemini Evidence Judgment.
Compares actual observed results against answer_key.md.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

import factcheck as fc

load_dotenv()

EXPECTED_BENCHMARK = [
    {
        "claim_key": "Microsoft",
        "expected_verdict": "Verified",
        "expected_fact": "Closed transaction for $68.7B on Oct 13, 2023",
        "expected_sources": "SEC Form 8-K / Microsoft PR"
    },
    {
        "claim_key": "Python",
        "expected_verdict": "Verified",
        "expected_fact": "Released on Dec 3, 2008",
        "expected_sources": "Python Software Foundation (python.org)"
    },
    {
        "claim_key": "Anthropic",
        "expected_verdict": "False",
        "expected_fact": "Founded in 2021 by Dario Amodei, Daniela Amodei & team (not 1998 by Jobs & Gates)",
        "expected_sources": "Anthropic official about page / Crunchbase"
    },
    {
        "claim_key": "population",
        "expected_verdict": "Inaccurate",
        "expected_fact": "Surpassed 8.0B in Nov 2022; ~8.1-8.2B in 2024-2026 (7.2B was ~2013)",
        "expected_sources": "UN Population Division / US Census Bureau"
    },
    {
        "claim_key": "Apple",
        "expected_verdict": "Verified",
        "expected_fact": "$94.93B net sales in Q4 FY24 (ended Sep 28, 2024)",
        "expected_sources": "Apple Form 10-Q / Q4 Earnings Release"
    },
    {
        "claim_key": "Tesla",
        "expected_verdict": "Inaccurate",
        "expected_fact": "499,550 was FY2020 deliveries; FY2024 was ~1.79M deliveries",
        "expected_sources": "Tesla IR / SEC 10-K"
    },
    {
        "claim_key": "Shopify",
        "expected_verdict": "Inaccurate",
        "expected_fact": "$2.16B in Q3 2024 (not $4.8B)",
        "expected_sources": "Shopify Q3 2024 Earnings Release"
    },
    {
        "claim_key": "Spotify",
        "expected_verdict": "False",
        "expected_fact": "Never acquired; Spotify is an independent public company (SPOT)",
        "expected_sources": "Spotify IR / SEC EDGAR"
    },
    {
        "claim_key": "Eiffel",
        "expected_verdict": "Inaccurate",
        "expected_fact": "Total architectural height is 330 meters (not 150m)",
        "expected_sources": "SETE (Société d'Exploitation de la Tour Eiffel)"
    },
    {
        "claim_key": "Alphabet",
        "expected_verdict": "False",
        "expected_fact": "Full-year 2024 revenue exceeded $350B (not $10B)",
        "expected_sources": "Alphabet SEC 10-K / Investor Relations"
    }
]

def run_evaluation():
    gemini_key = fc.get_gemini_api_key()
    tavily_key = fc.get_tavily_api_key()
    model = fc.get_model_name()

    print(f"=== Starting Live Evaluation (Tavily + Gemini) ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Gemini API Key present: {bool(gemini_key)}")
    print(f"Tavily API Key present: {bool(tavily_key)}")
    print(f"Gemini Model configured: {model}")

    if not gemini_key or not tavily_key:
        print("ERROR: Both GEMINI_API_KEY and TAVILY_API_KEY must be set in .env.")
        sys.exit(1)

    genai_client = fc.get_genai_client(gemini_key)
    tavily_client = fc.get_tavily_client(tavily_key)

    # 1. Extract PDF Text
    print("\n[Step 1] Extracting text from sample_trap.pdf...")
    pages = fc.extract_pdf_pages("sample_trap.pdf")
    print(f"Extracted {len(pages)} pages.")
    tagged_text = fc.format_tagged_pdf_text(pages)

    # 2. Extract Claims & Search Queries
    print(f"\n[Step 2] Calling Gemini ({model}) to extract claims + search queries...")
    claims = []
    try:
        claims = fc.extract_claims(client=genai_client, tagged_pdf_text=tagged_text, model=model)
        print(f"Successfully extracted {len(claims)} claims:")
        for idx, c in enumerate(claims, 1):
            print(f"  {idx}. [P{c.page}] {c.claim}")
            print(f"      Search Query: '{c.search_query}'")
    except Exception as e:
        print(f"Claim extraction failed: {e}")
        return

    # 3. Verify Claims with Tavily + Gemini
    print(f"\n[Step 3] Running Tavily search + Gemini evidence verification (max 3 workers)...")
    results = fc.verify_all_claims(
        genai_client=genai_client,
        tavily_client=tavily_client,
        claims=claims,
        model=model,
        max_workers=3,
        progress_callback=lambda done, total, res: print(
            f"  Progress: {done}/{total} done - [{res.verdict if res else '?'}] {res.claim[:45] if res else ''}..."
        )
    )

    print("\n=== Live Verification Results ===")
    for idx, r in enumerate(results, 1):
        print(f"\n--- Claim {idx} ---")
        print(f"Claim: {r.claim}")
        print(f"Page: {r.page} | Quote: {r.quote}")
        print(f"Query: {r.search_query}")
        print(f"Verdict: {r.verdict} | Confidence: {r.confidence}")
        print(f"Real Fact: {r.real_fact}")
        print(f"Ref Date: {r.reference_date}")
        print(f"Explanation: {r.explanation}")
        print(f"Sources: {[s.url for s in r.sources]}")
        if r.error:
            print(f"Error: {r.error}")

    # Generate Evaluation Report Markdown
    report_path = "test_report.md"
    generate_markdown_report(results, report_path, model)
    print(f"\nEvaluation complete. Report generated at {report_path}")


def generate_markdown_report(results: list[fc.ClaimResult], output_path: str, model_used: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verdict_counts = {
        "Verified": sum(1 for r in results if r.verdict == "Verified"),
        "Inaccurate": sum(1 for r in results if r.verdict == "Inaccurate"),
        "False": sum(1 for r in results if r.verdict == "False"),
        "Unverifiable": sum(1 for r in results if r.verdict == "Unverifiable"),
    }

    tavily_calls = sum(1 for r in results if not r.tavily_cached)
    cache_hits = sum(1 for r in results if r.tavily_cached)

    lines = [
        "# Truth Layer Evaluation Report: Live Trap Document Audit",
        f"**Run Date:** {timestamp}  ",
        f"**Architecture:** Tavily Live Search + Google Gemini (`{model_used}`)  ",
        f"**Document Audited:** `sample_trap.pdf` (10 embedded trap claims)  ",
        f"**Search Usage:** {tavily_calls} Tavily web search call(s), {cache_hits} cache hit(s)  ",
        "",
        "## Executive Summary",
        f"- **Total Claims Audited:** {len(results)}",
        f"- **🟢 Verified:** {verdict_counts['Verified']}",
        f"- **🟡 Inaccurate:** {verdict_counts['Inaccurate']}",
        f"- **🔴 False:** {verdict_counts['False']}",
        f"- **⚪ Unverifiable:** {verdict_counts['Unverifiable']}",
        "",
        "## Claim-by-Claim Benchmark: Expected vs. Observed",
        "",
        "| # | Claim | Page | Expected Verdict | Observed Verdict | Expected Real Fact | Observed Real Fact | Cited Sources | Match Status |",
        "|---|---|---|---|---|---|---|---|---|"
    ]

    for idx, r in enumerate(results, 1):
        clean_claim = r.claim.replace("|", "/")
        sources_count = len(r.sources)
        clean_fact = (r.real_fact or "N/A").replace("|", "/")
        
        expected = EXPECTED_BENCHMARK[idx - 1] if idx <= len(EXPECTED_BENCHMARK) else None
        exp_verdict = expected["expected_verdict"] if expected else "N/A"
        exp_fact = expected["expected_fact"] if expected else "N/A"

        # Check match status
        match_status = "✅ Match" if r.verdict == exp_verdict else "⚠️ Divergence"
        # Inaccurate / False interchangeability when disproving fabricated vs inaccurate figure
        if r.verdict in ("Inaccurate", "False") and exp_verdict in ("Inaccurate", "False"):
            match_status = "✅ Flagged (Inaccurate/False)"

        lines.append(
            f"| {idx} | {clean_claim} | {r.page} | **{exp_verdict}** | **{r.verdict}** | {exp_fact} | {clean_fact} | {sources_count} source(s) | {match_status} |"
        )

    lines.extend([
        "",
        "## Detailed Claim Explanations & Primary Citations",
        ""
    ])

    for idx, r in enumerate(results, 1):
        expected = EXPECTED_BENCHMARK[idx - 1] if idx <= len(EXPECTED_BENCHMARK) else None
        lines.append(f"### Claim {idx} (Page {r.page}): {r.verdict.upper()}")
        lines.append(f"- **Extracted Claim:** \"{r.claim}\"")
        lines.append(f"- **Supporting Quote:** \"{r.quote}\"")
        lines.append(f"- **Targeted Search Query:** `{r.search_query}`")
        lines.append(f"- **Expected Benchmark:** `{expected['expected_verdict'] if expected else 'N/A'}`")
        lines.append(f"- **Observed Verdict:** `{r.verdict}` (Confidence: {int(r.confidence*100)}%)")
        if expected:
            lines.append(f"- **Authoritative Target Fact:** {expected['expected_fact']} *(Source: {expected['expected_sources']})*")
        if r.real_fact:
            lines.append(f"- **Correct Real Fact Found:** **{r.real_fact}** *(Reference Date: {r.reference_date or 'N/A'})*")
        lines.append(f"- **Evidence Analysis:** {r.explanation}")
        if r.sources:
            lines.append("- **Retrieved Sources Cited:**")
            for s in r.sources:
                lines.append(f"  - [{s.title}]({s.url})")
        else:
            lines.append("- **Retrieved Sources Cited:** None")
        if r.error:
            lines.append(f"- **Execution Note:** `{r.error}`")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    run_evaluation()
