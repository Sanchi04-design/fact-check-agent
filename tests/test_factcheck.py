"""
Unit and Integration Tests for Truth Layer Fact-Check Agent
Covers:
- PDF extraction (normal, empty, scanned/image-only, truncation)
- JSON parsing and Pydantic validation
- Grounding metadata extraction
- Verdict validation rules
- CSV export & escaping
- Parallel verification pipeline with mocked Gemini responses
"""

import io
import json
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

import factcheck as fc


# ---------------------------------------------------------------------------
# 1. PDF Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_pdf_pages_success():
    """Verify normal digital PDF extraction on sample_trap.pdf."""
    pages = fc.extract_pdf_pages("sample_trap.pdf")
    assert len(pages) == 2
    assert pages[0]["page"] == 1
    assert "Microsoft" in pages[0]["text"]
    assert pages[1]["page"] == 2
    assert "Tesla" in pages[1]["text"]


def test_format_tagged_pdf_text():
    """Verify pages formatting into tagged text blocks."""
    mock_pages = [
        {"page": 1, "text": "Claim 1 on page 1."},
        {"page": 2, "text": "Claim 2 on page 2."}
    ]
    formatted = fc.format_tagged_pdf_text(mock_pages)
    assert "--- PAGE 1 ---" in formatted
    assert "--- PAGE 2 ---" in formatted
    assert "Claim 1 on page 1." in formatted


def test_extract_pdf_pages_empty_fails():
    """Verify empty PDF raises EmptyPDFError."""
    # A byte stream with no pages
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf
        with pytest.raises(fc.EmptyPDFError):
            fc.extract_pdf_pages(io.BytesIO(b"fake empty"))


def test_extract_pdf_pages_scanned_detected():
    """Verify image-only/scanned PDF without text raises ScannedPDFError."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   \n  "  # only whitespace
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf
        with pytest.raises(fc.ScannedPDFError):
            fc.extract_pdf_pages(io.BytesIO(b"fake scanned"))


def test_extract_pdf_pages_truncation():
    """Verify long text gets safely truncated."""
    long_text = "A" * 6000
    mock_page = MagicMock()
    mock_page.extract_text.return_value = long_text
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf
        pages = fc.extract_pdf_pages(io.BytesIO(b"dummy"), max_chars_per_page=1000)
        assert len(pages[0]["text"]) < 1200
        assert "[truncated long page text]" in pages[0]["text"]


# ---------------------------------------------------------------------------
# 2. JSON Parsing & Pydantic Validation Tests
# ---------------------------------------------------------------------------

def test_clean_json_text_fences():
    """Verify stripping of markdown code fences."""
    raw = "```json\n{\"verdict\": \"Verified\"}\n```"
    cleaned = fc.clean_json_text(raw)
    assert cleaned == "{\"verdict\": \"Verified\"}"

    raw2 = "```\n[{\"claim\": \"test\"}]\n```"
    cleaned2 = fc.clean_json_text(raw2)
    assert cleaned2 == "[{\"claim\": \"test\"}]"


def test_extract_json_object_or_array():
    """Verify JSON parsing and regex fallback for messy model responses."""
    text_with_chatter = "Here is the result:\n```json\n[{\"claim\": \"A\", \"page\": 1, \"quote\": \"B\"}]\n```\nHope this helps!"
    parsed = fc.extract_json_object_or_array(text_with_chatter)
    assert isinstance(parsed, list)
    assert parsed[0]["claim"] == "A"

    obj_text = "Analysis complete:\n{\"verdict\": \"False\", \"real_fact\": \"Actual\", \"reference_date\": \"2024\", \"explanation\": \"Disproven\", \"confidence\": 0.95}"
    parsed_obj = fc.extract_json_object_or_array(obj_text)
    assert isinstance(parsed_obj, dict)
    assert parsed_obj["verdict"] == "False"


def test_pydantic_claim_verification_schema():
    """Verify ClaimVerification validates required fields and verdict types."""
    valid_data = {
        "verdict": "Inaccurate",
        "real_fact": "Corrected number is 100",
        "reference_date": "2024-Q3",
        "explanation": "Evidence shows 100 not 50",
        "confidence": 0.9
    }
    cv = fc.ClaimVerification(**valid_data)
    assert cv.verdict == "Inaccurate"
    assert cv.confidence == 0.9

    # Invalid verdict
    with pytest.raises(Exception):
        fc.ClaimVerification(
            verdict="MaybeTrue",
            explanation="Invalid",
            confidence=0.5
        )


# ---------------------------------------------------------------------------
# 3. Grounding Metadata Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_grounding_sources_success():
    """Verify extracting titles and URIs from grounding_metadata chunks."""
    chunk1 = MagicMock()
    chunk1.web.uri = "https://www.sec.gov/filing"
    chunk1.web.title = "SEC Filing"

    chunk2 = MagicMock()
    chunk2.web.uri = "https://news.microsoft.com/press"
    chunk2.web.title = "Microsoft Press"

    # Duplicate URI should be deduplicated
    chunk3 = MagicMock()
    chunk3.web.uri = "https://www.sec.gov/filing"
    chunk3.web.title = "SEC Duplicate"

    mock_response = MagicMock()
    candidate = MagicMock()
    candidate.grounding_metadata.grounding_chunks = [chunk1, chunk2, chunk3]
    mock_response.candidates = [candidate]

    sources = fc.extract_grounding_sources(mock_response)
    assert len(sources) == 2
    assert sources[0].url == "https://www.sec.gov/filing"
    assert sources[0].title == "SEC Filing"
    assert sources[1].url == "https://news.microsoft.com/press"


def test_extract_grounding_sources_empty():
    """Verify graceful handling when candidates or grounding chunks are None."""
    mock_response = MagicMock()
    mock_response.candidates = []
    assert fc.extract_grounding_sources(mock_response) == []

    mock_response2 = MagicMock()
    candidate = MagicMock()
    candidate.grounding_metadata = None
    mock_response2.candidates = [candidate]
    assert fc.extract_grounding_sources(mock_response2) == []


# ---------------------------------------------------------------------------
# 4. Auditable CSV Export Tests
# ---------------------------------------------------------------------------

def test_results_to_dataframe_and_csv():
    """Verify DataFrame structure and CSV byte generation with proper escaping."""
    results = [
        fc.ClaimResult(
            claim="Microsoft acquired Activision for $69B, reported as \"massive\" in media.",
            page=1,
            quote="completed its acquisition",
            verdict="Verified",
            real_fact="Closed at $68.7B",
            reference_date="2023-10",
            explanation="SEC 8-K confirms transaction closed.",
            confidence=0.98,
            sources=[
                fc.GroundedSource(title="SEC 8-K", url="https://www.sec.gov/archive"),
                fc.GroundedSource(title="Reuters", url="https://reuters.com/tech")
            ]
        ),
        fc.ClaimResult(
            claim="Stripe bought Spotify for $45B.",
            page=2,
            quote="Stripe acquired music streaming service Spotify",
            verdict="False",
            real_fact="No acquisition occurred.",
            reference_date="2024",
            explanation="Spotify remains independent.",
            confidence=1.0,
            sources=[]
        )
    ]

    df = fc.results_to_dataframe(results)
    assert len(df) == 2
    expected_cols = [
        "Original Claim", "Page", "Supporting Quote", "Verdict",
        "Correct Fact", "Reference Date", "Explanation",
        "Confidence", "Grounded Sources"
    ]
    for col in expected_cols:
        assert col in df.columns

    csv_bytes = fc.results_to_csv_bytes(results)
    assert isinstance(csv_bytes, bytes)
    csv_str = csv_bytes.decode("utf-8")
    assert "Microsoft acquired Activision" in csv_str
    assert "https://www.sec.gov/archive" in csv_str
    # Verify quotes escaping in CSV
    assert '""massive""' in csv_str or '"Microsoft acquired Activision' in csv_str


# ---------------------------------------------------------------------------
# 5. Parallel Pipeline Execution (Mocked)
# ---------------------------------------------------------------------------

def test_verify_all_claims_handles_partial_failure():
    """Verify ThreadPoolExecutor preserves successful claims even when one fails."""
    mock_client = MagicMock()

    claim1 = fc.ExtractedClaim(claim="Claim 1 is verified.", page=1, quote="Quote 1")
    claim2 = fc.ExtractedClaim(claim="Claim 2 fails with error.", page=1, quote="Quote 2")
    claim3 = fc.ExtractedClaim(claim="Claim 3 is false.", page=2, quote="Quote 3")

    def mock_verify_single(client, claim_item, model, current_date):
        if "Claim 2" in claim_item.claim:
            raise RuntimeError("Network timeout simulation")
        elif "Claim 1" in claim_item.claim:
            return fc.ClaimResult(
                claim=claim_item.claim,
                page=claim_item.page,
                quote=claim_item.quote,
                verdict="Verified",
                explanation="Grounded",
                confidence=0.95,
                sources=[fc.GroundedSource(title="Source 1", url="https://src1.org")]
            )
        else:
            return fc.ClaimResult(
                claim=claim_item.claim,
                page=claim_item.page,
                quote=claim_item.quote,
                verdict="False",
                real_fact="Correct Fact",
                reference_date="2024",
                explanation="Contradicted",
                confidence=0.99,
                sources=[fc.GroundedSource(title="Source 3", url="https://src3.org")]
            )

    with patch("factcheck.verify_single_claim", side_effect=mock_verify_single):
        results = fc.verify_all_claims(
            client=mock_client,
            claims=[claim1, claim2, claim3],
            max_workers=2
        )

        assert len(results) == 3
        # Claim 1 succeeded
        assert results[0].verdict == "Verified"
        # Claim 2 failed gracefully without crashing pipeline
        assert results[1].verdict == "Unverifiable"
        assert "Network timeout" in results[1].explanation
        # Claim 3 succeeded
        assert results[2].verdict == "False"
