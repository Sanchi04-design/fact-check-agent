"""
Truth Layer - Fact-Checking Web App for Marketing & Sales Documents
Audits marketing PDFs, extracts checkable claims, verifies them against live Google Search data,
and highlights inaccuracies with verified real facts.
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


init_session_state()

# ---------------------------------------------------------------------------
# Sidebar: Credentials, Model Config, and Reference Guide
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🛡️ Truth Layer Settings")
    st.caption("AI-powered fact auditing with live Google Search grounding.")

    st.markdown("---")
    st.subheader("1. API Configuration")

    # API key resolution
    secrets_key_available = False
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            secrets_key_available = True
    except Exception:
        pass

    env_key_available = bool(os.getenv("GEMINI_API_KEY"))

    sidebar_api_key = ""
    if secrets_key_available:
        st.success("API Key detected in Streamlit Secrets")
    elif env_key_available:
        st.info("API Key detected in Environment (.env)")
    else:
        sidebar_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Your key is kept only in this session and never logged or committed."
        )

    # Optional manual key override
    with st.expander("Override API Key", expanded=False):
        override_key = st.text_input("Custom Gemini API Key", type="password")
        if override_key:
            sidebar_api_key = override_key

    # Model selection
    default_model = fc.get_model_name()
    available_models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.1-pro-preview"]
    if default_model not in available_models:
        available_models.insert(0, default_model)

    model_choice = st.selectbox(
        "Gemini Model",
        options=available_models,
        index=available_models.index(default_model) if default_model in available_models else 0,
        help="Model used for extraction and search-grounded verification."
    )

    st.markdown("---")
    st.subheader("2. Verdict Taxonomy")
    st.markdown("""
    - <span class="badge-verified">Verified</span>: Current authoritative search evidence directly confirms the claim.
    - <span class="badge-inaccurate">Inaccurate</span>: Evidence establishes the claim is outdated, partly wrong, or numerically incorrect.
    - <span class="badge-false">False</span>: Contradictory evidence disproves the claim or claim is demonstrably fabricated.
    - <span class="badge-unverifiable">Unverifiable</span>: Search failed, ambiguous evidence, or missing grounding chunks.
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
    "audits each against **live Google Search data**, and surfaces exact corrections."
)

uploaded_file = st.file_uploader(
    "Upload PDF Document",
    type=["pdf"],
    help="Select a digital text PDF (scanned image-only PDFs without OCR are not supported)."
)

# Active key resolution
resolved_api_key = fc.get_api_key(sidebar_api_key)

col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_button = st.button("🚀 Run Fact-Check", type="primary", disabled=(uploaded_file is None))

with col_info:
    if not resolved_api_key:
        st.warning("⚠️ Please provide a Gemini API Key in the sidebar or environment.")


# ---------------------------------------------------------------------------
# Execution Pipeline
# ---------------------------------------------------------------------------

if run_button and uploaded_file:
    if not resolved_api_key:
        st.error("Cannot proceed without a valid Gemini API Key. Please provide one in the sidebar.")
    else:
        st.session_state["pdf_filename"] = uploaded_file.name
        st.session_state["error_message"] = None

        try:
            client = fc.get_genai_client(resolved_api_key)
        except Exception as e:
            st.error(f"Failed to initialize Gemini Client: {e}")
            st.stop()

        # Step 1: PDF Extraction
        with st.status("📄 Processing PDF & Extracting Claims...", expanded=True) as status:
            try:
                st.write("Reading PDF text and page structure...")
                pdf_bytes = uploaded_file.getvalue()
                pages_data = fc.extract_pdf_pages(pdf_bytes)
                st.write(f"Extracted {len(pages_data)} pages of digital text.")

                tagged_text = fc.format_tagged_pdf_text(pages_data)

                st.write("Extracting specific, checkable empirical claims via Gemini...")
                extracted_claims = fc.extract_claims(
                    client=client,
                    tagged_pdf_text=tagged_text,
                    model=model_choice
                )

                if not extracted_claims:
                    st.warning("No specific empirical or numeric claims found in this document.")
                    status.update(label="No claims found", state="complete")
                    st.stop()

                st.session_state["claims"] = extracted_claims
                st.write(f"Identified **{len(extracted_claims)}** claims to verify.")

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

            # Step 2: Verification with Live Google Search Grounding
            status.update(label="🔍 Verifying claims against live Google Search data...", state="running")
            st.write("Initiating parallel search verification (temperature=0.0, max 4 workers)...")

            progress_bar = st.progress(0.0)
            progress_text = st.empty()

            def update_progress(done_count: int, total_count: int, last_res: Optional[fc.ClaimResult]):
                frac = done_count / total_count
                progress_bar.progress(frac)
                if last_res:
                    progress_text.text(f"Verified {done_count}/{total_count}: [{last_res.verdict}] {last_res.claim[:60]}...")

            verification_results = fc.verify_all_claims(
                client=client,
                claims=extracted_claims,
                model=model_choice,
                max_workers=4,
                progress_callback=update_progress
            )

            st.session_state["results"] = verification_results
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
                    " {r.quote} "
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Highlighted correction for Inaccurate / False
            if r.verdict in ("Inaccurate", "False") or (r.real_fact and r.real_fact != "N/A"):
                ref_date_badge = f" <em>(Effective: {r.reference_date})</em>" if r.reference_date else ""
                st.markdown(f"""
                <div class="correction-box">
                    <strong>🎯 Correct Real Fact{ref_date_badge}:</strong><br>
                    {r.real_fact or "No reliable correction could be confirmed."}
                </div>
                """, unsafe_allow_html=True)

            # Explanation
            st.markdown(f"**Evidence & Explanation:** {r.explanation}")

            # Grounded Sources
            if r.sources:
                sources_md = " • ".join(f"[{s.title}]({s.url})" for s in r.sources if s.url)
                st.markdown(f"**Live Grounded Sources:** {sources_md}")
            else:
                st.caption("No external grounding links available.")

            if r.error:
                st.caption(f"⚠️ Note: Encountered issue: {r.error}")

            st.markdown("<hr style='margin: 12px 0 24px 0; border: none; border-top: 1px dashed #ccc;' />", unsafe_allow_html=True)
