"""
Truth Layer - Fact-Checking Web App for Marketing & Sales Documents
Audits marketing PDFs, extracts checkable claims, verifies them against live Tavily Search data,
and highlights inaccuracies with verified real facts using Gemini.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

import factcheck as fc

load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="Truth Layer | Fact-Check Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, clean, auditable styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    .badge-verified {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-inaccurate {
        background-color: #fff3cd;
        color: #664d03;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-false {
        background-color: #f8d7da;
        color: #842029;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-unverifiable {
        background-color: #e2e3e5;
        color: #41464b;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .claim-box {
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 18px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .correction-box {
        background-color: #f0f7ff;
        border-left: 4px solid #0d6efd;
        padding: 10px 14px;
        margin: 10px 0;
        border-radius: 0 6px 6px 0;
        color: #000000 !important;
    }
    .correction-box strong, .correction-box span, .correction-box em, .correction-box div {
        color: #000000 !important;
    }
    .quote-box {
        background-color: #f8f9fa;
        border-left: 3px solid #6c757d;
        padding: 6px 12px;
        font-style: italic;
        color: #495057;
        margin: 6px 0;
        font-size: 0.9rem;
    }
    .query-tag {
        background-color: #e9ecef;
        color: #495057;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize persistent session state variables."""
    if "results" not in st.session_state:
        st.session_state["results"] = None
    if "claims" not in st.session_state:
        st.session_state["claims"] = None
    if "pdf_filename" not in st.session_state:
        st.session_state["pdf_filename"] = ""
    if "error_message" not in st.session_state:
        st.session_state["error_message"] = None
    if "tavily_searches_count" not in st.session_state:
        st.session_state["tavily_searches_count"] = 0
    if "tavily_cache_hits" not in st.session_state:
        st.session_state["tavily_cache_hits"] = 0


init_session_state()

# ---------------------------------------------------------------------------
# Sidebar: Credentials, Model Config, and Reference Guide
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🛡️ Truth Layer Settings")
    st.caption("AI-powered fact auditing: Tavily Live Search + Gemini Evidence Judgment.")

    st.markdown("---")
    st.subheader("1. API Configuration")

    # A. Gemini Key
    gemini_from_secrets = False
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            gemini_from_secrets = True
    except Exception:
        pass

    # B. Tavily Key
    tavily_from_secrets = False
    try:
        if hasattr(st, "secrets") and "TAVILY_API_KEY" in st.secrets and st.secrets["TAVILY_API_KEY"]:
            tavily_from_secrets = True
    except Exception:
        pass

    gemini_from_env = bool(os.getenv("GEMINI_API_KEY"))
    tavily_from_env = bool(os.getenv("TAVILY_API_KEY"))
    sidebar_gemini_key = ""
    sidebar_tavily_key = ""

    # If keys come from secrets (deployed app), hide key fields entirely
    if gemini_from_secrets and tavily_from_secrets:
        st.success("API Keys: Configured via Secrets")
    else:
        # Gemini Key
        if gemini_from_secrets:
            st.success("Gemini Key: Active (Secrets)")
        elif gemini_from_env:
            st.info("Gemini Key: Active (.env)")
        else:
            sidebar_gemini_key = st.text_input(
                "Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
                help="Gemini evaluates claims against retrieved search evidence."
            )

        # Tavily Key
        if tavily_from_secrets:
            st.success("Tavily Key: Active (Secrets)")
        elif tavily_from_env:
            st.info("Tavily Key: Active (.env)")
        else:
            sidebar_tavily_key = st.text_input(
                "Tavily API Key",
                type="password",
                placeholder="tvly-...",
                help="Tavily executes live web search for current authoritative data."
            )

        # Optional manual key override for local development with .env
        if gemini_from_env or tavily_from_env:
            with st.expander("Override API Keys", expanded=False):
                override_gemini = st.text_input("Custom Gemini Key", type="password")
                if override_gemini:
                    sidebar_gemini_key = override_gemini
                override_tavily = st.text_input("Custom Tavily Key", type="password")
                if override_tavily:
                    sidebar_tavily_key = override_tavily

    # Model configuration (read-only, fixed to single configured model)
    model_choice = fc.get_model_name()
    st.markdown(f"**Model:** `{model_choice}`")

    st.markdown("---")
    st.subheader("2. Verdict Taxonomy")
    st.markdown("""
    - <span class="badge-verified">Verified</span>: Retrieved authoritative evidence confirms the claim.
    - <span class="badge-inaccurate">Inaccurate</span>: Evidence demonstrates claim is outdated or numerically inaccurate.
    - <span class="badge-false">False</span>: Evidence contradicts claim or disproves a fabricated claim.
    - <span class="badge-unverifiable">Unverifiable</span>: No relevant evidence, ambiguous sources, or API error.
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"System Date: {datetime.now().strftime('%Y-%m-%d')}")


# ---------------------------------------------------------------------------
# Main App Header & File Upload
# ---------------------------------------------------------------------------

st.title("Truth Layer: Marketing & Sales Fact-Checker")
st.markdown(
    "Upload a marketing deck, whitepaper, or press release PDF. "
    "Truth Layer extracts specific statistical, financial, and product claims, "
    "retrieves live web evidence via **Tavily Search**, and audits each claim using **Gemini**."
)

uploaded_file = st.file_uploader(
    "Upload PDF Document",
    type=["pdf"],
    help="Select a digital text PDF (scanned image-only PDFs without OCR are not supported)."
)

# Active keys resolution
resolved_gemini_key = fc.get_gemini_api_key(sidebar_gemini_key)
resolved_tavily_key = fc.get_tavily_api_key(sidebar_tavily_key)

col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_button = st.button("🚀 Run Fact-Check", type="primary", disabled=(uploaded_file is None))

with col_info:
    missing_keys = []
    if not resolved_gemini_key:
        missing_keys.append("Gemini API Key")
    if not resolved_tavily_key:
        missing_keys.append("Tavily API Key")
    if missing_keys:
        st.warning(f"⚠️ Missing: {', '.join(missing_keys)}. Please provide in sidebar or .env.")


# ---------------------------------------------------------------------------
# Execution Pipeline
# ---------------------------------------------------------------------------

if run_button and uploaded_file:
    if not resolved_gemini_key or not resolved_tavily_key:
        st.error("Cannot proceed: Both Gemini API Key and Tavily API Key are required.")
    else:
        st.session_state["pdf_filename"] = uploaded_file.name
        st.session_state["error_message"] = None

        try:
            genai_client = fc.get_genai_client(resolved_gemini_key)
            tavily_client = fc.get_tavily_client(resolved_tavily_key)
        except Exception as e:
            st.error(f"Client initialization error: {e}")
            st.stop()

        # Step 1: PDF Extraction
        with st.status("📄 Processing PDF & Extracting Claims...", expanded=True) as status:
            try:
                st.write("Reading PDF text and page structure...")
                pdf_bytes = uploaded_file.getvalue()
                pages_data = fc.extract_pdf_pages(pdf_bytes)
                st.write(f"Extracted {len(pages_data)} pages of digital text.")

                tagged_text = fc.format_tagged_pdf_text(pages_data)

                st.write("Extracting empirical claims and targeted web search queries...")
                extracted_claims = fc.extract_claims(
                    client=genai_client,
                    tagged_pdf_text=tagged_text,
                    model=model_choice
                )

                if not extracted_claims:
                    st.warning("No specific empirical or numeric claims found in this document.")
                    status.update(label="No claims found", state="complete")
                    st.stop()

                st.session_state["claims"] = extracted_claims
                st.write(f"Identified **{len(extracted_claims)}** claims with search queries.")

            except fc.EmptyPDFError as e:
                st.error(f"Empty PDF Error: {e}")
                status.update(label="Failed: Empty PDF", state="error")
                st.stop()
            except fc.ScannedPDFError as e:
                st.error(f"Scanned Document Detected: {e}")
                status.update(label="Failed: Scanned PDF", state="error")
                st.stop()
            except Exception as e:
                st.error(f"Error during claim extraction: {e}")
                status.update(label="Extraction Error", state="error")
                st.stop()

            # Step 2: Verification with Tavily Search + Gemini Evidence Judgment
            status.update(label="🔍 Searching live web (Tavily) & judging evidence (Gemini)...", state="running")
            st.write("Initiating parallel verification (max 3 concurrent workers, depth: basic)...")

            progress_bar = st.progress(0.0)
            progress_text = st.empty()

            def update_progress(done_count: int, total_count: int, last_res: Optional[fc.ClaimResult]):
                frac = done_count / total_count
                progress_bar.progress(frac)
                if last_res:
                    cache_str = " (cached)" if last_res.tavily_cached else ""
                    progress_text.text(f"Verified {done_count}/{total_count}: [{last_res.verdict}] {last_res.claim[:50]}...{cache_str}")

            verification_results = fc.verify_all_claims(
                genai_client=genai_client,
                tavily_client=tavily_client,
                claims=extracted_claims,
                model=model_choice,
                max_workers=3,
                progress_callback=update_progress
            )

            st.session_state["results"] = verification_results
            st.session_state["tavily_searches_count"] = sum(1 for r in verification_results if not r.tavily_cached)
            st.session_state["tavily_cache_hits"] = sum(1 for r in verification_results if r.tavily_cached)

            progress_bar.progress(1.0)
            progress_text.text(f"Completed verification of {len(verification_results)} claims.")
            status.update(label="✅ Fact-Check Complete!", state="complete")


# ---------------------------------------------------------------------------
# Results Display
# ---------------------------------------------------------------------------

results: Optional[List[fc.ClaimResult]] = st.session_state.get("results")

if results:
    st.markdown("---")
    st.subheader(f"📊 Audit Results: {st.session_state.get('pdf_filename', 'Document')}")

    # Metrics Summary
    total_claims = len(results)
    verified_count = sum(1 for r in results if r.verdict == "Verified")
    inaccurate_count = sum(1 for r in results if r.verdict == "Inaccurate")
    false_count = sum(1 for r in results if r.verdict == "False")
    unverifiable_count = sum(1 for r in results if r.verdict == "Unverifiable")

    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.metric("Total Claims", total_claims)
    with m_col2:
        st.metric("🟢 Verified", verified_count)
    with m_col3:
        st.metric("🟡 Inaccurate", inaccurate_count)
    with m_col4:
        st.metric("🔴 False", false_count)
    with m_col5:
        st.metric("⚪ Unverifiable", unverifiable_count)

    # Note on Tavily credit usage and caching
    searches_used = st.session_state.get("tavily_searches_count", 0)
    cache_hits = st.session_state.get("tavily_cache_hits", 0)
    st.info(f"🌐 **Search Usage:** Used {searches_used} Tavily live search(es) ({cache_hits} query cache hits).")

    # Check for quota exhaustion errors across results
    quota_errors = [r for r in results if r.error and ("quota" in r.error.lower() or "429" in r.error)]
    if quota_errors:
        st.warning("⚠️ **Daily/monthly free quota reached on search or model API.** Some claims were marked Unverifiable due to rate limits.")

    # CSV Download Button
    csv_bytes = fc.results_to_csv_bytes(results)
    doc_stem = os.path.splitext(st.session_state.get("pdf_filename", "audit"))[0]
    st.download_button(
        label="📥 Download Audit Report (CSV)",
        data=csv_bytes,
        file_name=f"factcheck_report_{doc_stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_csv_btn"
    )

    # Filter selector
    filter_choice = st.radio(
        "Filter by Verdict",
        options=["All", "Inaccurate & False (Flagged)", "Verified", "Inaccurate", "False", "Unverifiable"],
        horizontal=True
    )

    filtered_results = []
    for r in results:
        if filter_choice == "All":
            filtered_results.append(r)
        elif filter_choice == "Inaccurate & False (Flagged)" and r.verdict in ("Inaccurate", "False"):
            filtered_results.append(r)
        elif r.verdict == filter_choice:
            filtered_results.append(r)

    st.write(f"Showing **{len(filtered_results)}** of **{total_claims}** claims")

    # Claim Cards
    for idx, r in enumerate(filtered_results, start=1):
        badge_class = {
            "Verified": "badge-verified",
            "Inaccurate": "badge-inaccurate",
            "False": "badge-false",
            "Unverifiable": "badge-unverifiable"
        }.get(r.verdict, "badge-unverifiable")

        with st.container():
            st.markdown(f"""
            <div class="claim-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span class="{badge_class}">{r.verdict.upper()}</span>
                        <span style="margin-left: 10px; color: #6c757d; font-size: 0.85rem;">Page {r.page}</span>
                    </div>
                    <div style="color: #6c757d; font-size: 0.85rem;">
                        Confidence: <strong>{int(r.confidence * 100)}%</strong>
                    </div>
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; margin: 8px 0; color: #212529;">
                    "{r.claim}"
                </div>
                <div class="quote-box">
                    "{r.quote}"
                </div>
                <div style="margin-top: 8px; font-size: 0.85rem; color: #6c757d;">
                    Search Query: <span class="query-tag">{r.search_query}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Highlighted correction for Inaccurate / False
            if r.verdict in ("Inaccurate", "False") or (r.real_fact and not r.real_fact.startswith("No reliable")):
                ref_date_badge = f" <em style='color: #222222 !important;'>(Effective: {r.reference_date})</em>" if r.reference_date else ""
                st.markdown(f"""
                <div class="correction-box" style="color: #000000 !important; background-color: #f0f7ff !important;">
                    <strong style="color: #000000 !important; font-size: 0.95rem;">🎯 Correct Real Fact{ref_date_badge}:</strong><br>
                    <div style="color: #000000 !important; margin-top: 4px; font-weight: 500; font-size: 1rem; line-height: 1.4;">
                        {r.real_fact or "No reliable correction could be confirmed from the retrieved sources."}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Explanation
            st.markdown(f"**Evidence & Explanation:** {r.explanation}")

            # Grounded Sources
            if r.sources:
                sources_md = " • ".join(f"[{s.title}]({s.url})" for s in r.sources if s.url)
                st.markdown(f"**Retrieved Sources Cited:** {sources_md}")
            else:
                st.caption("No external sources cited.")

            if r.error:
                st.caption(f"⚠️ Note: {r.error}")

            st.markdown("<hr style='margin: 12px 0 24px 0; border: none; border-top: 1px dashed #ccc;' />", unsafe_allow_html=True)
