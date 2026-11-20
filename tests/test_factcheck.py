"""
Unit and Integration Tests for Truth Layer Fact-Check Agent (Tavily + Gemini)
Covers:
- PDF extraction (normal, empty, scanned/image-only, truncation)
- JSON parsing and Pydantic validation (ExtractedClaim with search_query, ClaimVerification)
- Tavily search result formatting, snippet truncation, and caching
- Evidence block formatting for Gemini prompts
- Client-side enforcement: Verified requires cited evidence
- GroundedSource mapping strictly from cited evidence items
- CSV export & escaping (including Search Query column)
- Parallel pipeline execution with mocked Tavily and Gemini
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
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf
        with pytest.raises(fc.EmptyPDFError):
            fc.extract_pdf_pages(io.BytesIO(b"fake empty"))


def test_extract_pdf_pages_scanned_detected():
    """Verify image-only/scanned PDF without text raises ScannedPDFError."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   \n  "
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
    text_with_chatter = "Here is the result:\n```json\n[{\"claim\": \"A\", \"page\": 1, \"quote\": \"B\", \"search_query\": \"Q\"}]\n```\nHope this helps!"
    parsed = fc.extract_json_object_or_array(text_with_chatter)
    assert isinstance(parsed, list)
    assert parsed[0]["claim"] == "A"
    assert parsed[0]["search_query"] == "Q"

    obj_text = "Analysis complete:\n{\"verdict\": \"False\", \"real_fact\": \"Actual\", \"reference_date\": \"2024\", \"explanation\": \"Disproven\", \"confidence\": 0.95, \"evidence_used\": [1]}"
    parsed_obj = fc.extract_json_object_or_array(obj_text)
    assert isinstance(parsed_obj, dict)
    assert parsed_obj["verdict"] == "False"
    assert parsed_obj["evidence_used"] == [1]


def test_pydantic_extracted_claim_schema():
    """Verify ExtractedClaim validates claim, page, quote, and search_query."""
    claim = fc.ExtractedClaim(
        claim="Tesla delivered 499,550 cars in 2024.",
        page=2,
        quote="Tesla's global vehicle deliveries were 499,550 in 2024",
        search_query="Tesla 2024 annual vehicle deliveries"
    )
    assert claim.page == 2
    assert claim.search_query == "Tesla 2024 annual vehicle deliveries"


def test_pydantic_claim_verification_schema():
    """Verify ClaimVerification validates required fields and verdict types."""
    valid_data = {
        "verdict": "Inaccurate",
        "real_fact": "Corrected number is 100",
        "reference_date": "2024-Q3",
        "explanation": "Evidence shows 100 not 50",
        "confidence": 0.9,
        "evidence_used": [1, 2]
    }
    cv = fc.ClaimVerification(**valid_data)
    assert cv.verdict == "Inaccurate"
    assert cv.confidence == 0.9
    assert cv.evidence_used == [1, 2]

    # Invalid verdict
    with pytest.raises(Exception):
        fc.ClaimVerification(
            verdict="MaybeTrue",
            explanation="Invalid",
            confidence=0.5
        )


# ---------------------------------------------------------------------------
# 3. Tavily Search, Caching & Evidence Formatting Tests
# ---------------------------------------------------------------------------

def test_tavily_search_and_caching():
    """Verify Tavily search parsing, snippet truncation, and in-memory cache."""
    mock_tavily = MagicMock()
    mock_tavily.search.return_value = {
        "results": [
            {
                "title": "SEC 10-K Filing",
                "url": "https://sec.gov/filing1",
                "content": "A" * 800,  # exceeds 600 chars
                "published_date": "2024-11-01"
            }
        ]
    }

    # First call - fresh
    items, is_cached, err = fc.search_tavily(
        mock_tavily,
        query="unique_test_query_123",
        claim_text="Some claim",
        max_retries=1
    )
    assert err is None
    assert is_cached is False
    assert len(items) == 1
    assert len(items[0].content) <= 605
    assert items[0].url == "https://sec.gov/filing1"
    assert mock_tavily.search.call_count == 1

    # Second call - from cache
    items2, is_cached2, err2 = fc.search_tavily(
        mock_tavily,
        query="unique_test_query_123",
        claim_text="Some claim",
        max_retries=1
    )
    assert is_cached2 is True
    assert len(items2) == 1
    # Search was NOT called again!
    assert mock_tavily.search.call_count == 1


def test_format_evidence_block():
    """Verify numbered formatting of evidence items."""
    items = [
        fc.TavilyEvidenceItem(
            index=1,
            title="Source 1",
            url="https://src1.com",
            content="Snippet 1",
            published_date="2024-01-01"
        ),
        fc.TavilyEvidenceItem(
            index=2,
            title="Source 2",
            url="https://src2.com",
            content="Snippet 2",
            published_date=None
        )
    ]
    block = fc.format_evidence_block(items)
    assert "[1] Title: Source 1" in block
    assert "URL: https://src1.com" in block
    assert "Date: 2024-01-01" in block
    assert "[2] Title: Source 2" in block


# ---------------------------------------------------------------------------
# 4. Client-side Rules & Evidence Mapping Tests
# ---------------------------------------------------------------------------

def test_verified_downgrades_without_cited_evidence():
    """Verify that a Verified verdict with no evidence_used is downgraded to Unverifiable."""
    mock_genai = MagicMock()
    mock_tavily = MagicMock()

    mock_tavily.search.return_value = {
        "results": [
            {"title": "Doc 1", "url": "https://doc1.com", "content": "Text 1"}
        ]
    }

    # Gemini returns Verified but empty evidence_used []
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "verdict": "Verified",
        "real_fact": "Fact",
        "reference_date": "2024",
        "explanation": "I think it is true.",
        "confidence": 0.9,
        "evidence_used": []  # EMPTY!
    })
    mock_genai.models.generate_content.return_value = mock_response

    claim = fc.ExtractedClaim(
        claim="Some claim",
        page=1,
        quote="Quote",
        search_query="query"
    )

    result = fc.verify_claim_with_evidence(
        genai_client=mock_genai,
        tavily_client=mock_tavily,
        claim_item=claim
    )

    # Must be downgraded to Unverifiable!
    assert result.verdict == "Unverifiable"
    assert "Downgraded" in result.explanation


def test_sources_mapped_strictly_from_cited_evidence():
    """Verify that displayed sources come strictly from the cited evidence item indices."""
    mock_genai = MagicMock()
    mock_tavily = MagicMock()

    mock_tavily.search.return_value = {
        "results": [
            {"title": "Doc 1", "url": "https://doc1.com", "content": "Evidence 1"},
            {"title": "Doc 2", "url": "https://doc2.com", "content": "Evidence 2"},
            {"title": "Doc 3", "url": "https://doc3.com", "content": "Evidence 3"}
        ]
    }

    # Gemini cites ONLY item 2
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "verdict": "Inaccurate",
        "real_fact": "Correct Fact",
        "reference_date": "2024-Q3",
        "explanation": "Evidence 2 confirms the actual figure.",
        "confidence": 0.95,
        "evidence_used": [2]
    })
    mock_genai.models.generate_content.return_value = mock_response

    claim = fc.ExtractedClaim(
        claim="Claim about doc",
        page=1,
        quote="Quote",
        search_query="doc search"
    )

    result = fc.verify_claim_with_evidence(
        genai_client=mock_genai,
        tavily_client=mock_tavily,
        claim_item=claim
    )

    assert result.verdict == "Inaccurate"
    assert len(result.sources) == 1
    assert result.sources[0].url == "https://doc2.com"
    assert result.sources[0].title == "Doc 2"


# ---------------------------------------------------------------------------
# 5. Auditable CSV Export Tests
# ---------------------------------------------------------------------------

def test_results_to_dataframe_and_csv():
    """Verify DataFrame structure and CSV byte generation with proper escaping."""
    results = [
        fc.ClaimResult(
            claim="Microsoft acquired Activision for $69B, reported as \"massive\" in media.",
            page=1,
            quote="completed its acquisition",
            search_query="Microsoft Activision acquisition $69 billion",
            verdict="Verified",
            real_fact="Closed at $68.7B",
            reference_date="2023-10",
            explanation="SEC 8-K confirms transaction closed.",
            confidence=0.98,
            sources=[
                fc.GroundedSource(title="SEC 8-K", url="https://www.sec.gov/archive"),
                fc.GroundedSource(title="Reuters", url="https://reuters.com/tech")
            ]
        )
    ]

    df = fc.results_to_dataframe(results)
    assert len(df) == 1
    expected_cols = [
        "Original Claim", "Page", "Supporting Quote", "Search Query",
        "Verdict", "Correct Fact", "Reference Date", "Explanation",
        "Confidence", "Grounded Sources"
    ]
    for col in expected_cols:
        assert col in df.columns

    csv_bytes = fc.results_to_csv_bytes(results)
    assert isinstance(csv_bytes, bytes)
    csv_str = csv_bytes.decode("utf-8")
    assert "Microsoft acquired Activision" in csv_str
    assert "Microsoft Activision acquisition $69 billion" in csv_str
    assert "https://www.sec.gov/archive" in csv_str


# ---------------------------------------------------------------------------
# 6. Parallel Pipeline Execution (Mocked)
# ---------------------------------------------------------------------------

def test_verify_all_claims_handles_partial_failure():
    """Verify ThreadPoolExecutor preserves successful claims even when one fails."""
    mock_genai = MagicMock()
    mock_tavily = MagicMock()

    claim1 = fc.ExtractedClaim(claim="Claim 1", page=1, quote="Q1", search_query="sq1")
    claim2 = fc.ExtractedClaim(claim="Claim 2", page=1, quote="Q2", search_query="sq2")

    def mock_verify_single(genai_client, tavily_client, claim_item, model, current_date):
        if "Claim 2" in claim_item.claim:
            raise RuntimeError("Simulated network timeout")
        return fc.ClaimResult(
            claim=claim_item.claim,
            page=claim_item.page,
            quote=claim_item.quote,
            search_query=claim_item.search_query,
            verdict="Verified",
            explanation="Grounded",
            confidence=0.95,
            sources=[fc.GroundedSource(title="Source 1", url="https://src1.org")]
        )

    with patch("factcheck.verify_claim_with_evidence", side_effect=mock_verify_single):
        results = fc.verify_all_claims(
            genai_client=mock_genai,
            tavily_client=mock_tavily,
            claims=[claim1, claim2],
            max_workers=2
        )

        assert len(results) == 2
        assert results[0].verdict == "Verified"
        assert results[1].verdict == "Unverifiable"
        assert "Simulated network timeout" in results[1].explanation
