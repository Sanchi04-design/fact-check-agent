"""
Generate a reproducible Sample Trap PDF for the Truth Layer Fact-Check Agent.
Contains intentional supported facts, outdated figures, incorrect numbers, and fabricated claims.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf(output_filename: str = "sample_trap.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#283593'),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#212121'),
        spaceAfter=10
    )
    quote_style = ParagraphStyle(
        'DocQuote',
        parent=styles['Italic'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#455a64'),
        leftIndent=15,
        spaceAfter=10
    )

    story = []

    # Page 1
    story.append(Paragraph("Apex Tech Ventures: 2026 Strategic Market & Intelligence Briefing", title_style))
    story.append(Paragraph("<b>Executive Summary & Historical Milestones</b>", h2_style))
    story.append(Paragraph(
        "Welcome to the annual Apex Tech strategic memorandum. As we navigate the enterprise technology "
        "landscape in 2026, we review cornerstone market acquisitions and foundational software platforms.",
        body_style
    ))
    
    # Claim 1 (Supported / Verified)
    story.append(Paragraph(
        "In enterprise gaming and cloud ecosystem convergence, Microsoft completed its acquisition of Activision Blizzard for approximately $69 billion in October 2023, representing one of the largest technology transactions in history.",
        body_style
    ))
    
    # Claim 2 (Supported / Verified)
    story.append(Paragraph(
        "In open-source developer tooling, modern enterprise automation continues to lean on foundational infrastructure: Python 3.0 was officially released in December 2008, establishing the modern standard for language syntax.",
        body_style
    ))

    # Claim 3 (Fabricated / False)
    story.append(Paragraph(
        "In artificial intelligence frontier labs, pioneering development began decades ago when Anthropic was founded in 1998 by Steve Jobs and Bill Gates to explore neural computation.",
        body_style
    ))

    # Claim 4 (Outdated)
    story.append(Paragraph(
        "Regarding global consumer scale, our macroeconomic models project ongoing expansion. As of 2026, the global human population stands at approximately 7.2 billion people across all continents.",
        body_style
    ))

    # Claim 5 (Supported / Verified)
    story.append(Paragraph(
        "Looking at modern hardware financial performance, Apple reported total net sales of $94.9 billion for its fourth fiscal quarter ended September 28, 2024.",
        body_style
    ))

    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("Apex Tech Ventures: Market Metrics & Enterprise Benchmarks", title_style))
    story.append(Paragraph("<b>Section II: Automotive, E-Commerce & Structural Landmarks</b>", h2_style))

    # Claim 6 (Outdated / Incorrect)
    story.append(Paragraph(
        "In the clean mobility sector, global adoption reached critical mass recently: Tesla's global vehicle deliveries were 499,550 in 2024, maintaining their production trajectory.",
        body_style
    ))

    # Claim 7 (Numerically Incorrect)
    story.append(Paragraph(
        "In e-commerce infrastructure, commerce platforms expanded rapidly: Shopify reported total revenue of $4.8 billion for the third quarter of 2024.",
        body_style
    ))

    # Claim 8 (False / Fabricated M&A)
    story.append(Paragraph(
        "In corporate consolidation, fintech giant Stripe acquired music streaming service Spotify in March 2024 for $45 billion to integrate streaming commerce.",
        body_style
    ))

    # Claim 9 (Numerically Incorrect Spec)
    story.append(Paragraph(
        "In civil engineering and architectural tourism benchmarks, Paris remains a benchmark of European construction: The Eiffel Tower in Paris stands at an official architectural height of 150 meters.",
        body_style
    ))

    # Claim 10 (Grossly False Financial)
    story.append(Paragraph(
        "Finally, in digital advertising and cloud infrastructure scale, Alphabet (Google) generated $10 billion in total revenue in full year 2024.",
        body_style
    ))

    doc.build(story)
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    generate_pdf()
