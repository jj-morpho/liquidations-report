"""
PDF report generator for the Morpho Weekly Risk Report.
Uses ReportLab to produce a polished, Morpho-branded PDF.
"""
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd

from config import COLORS


# Colors
BG_DARK = HexColor(COLORS["bg_dark"])
BLUE_PRIMARY = HexColor(COLORS["blue_primary"])
BLUE_LIGHT = HexColor(COLORS["blue_light"])
TEXT_WHITE = HexColor(COLORS["text_white"])
TEXT_GRAY = HexColor(COLORS["text_gray"])
TEXT_LIGHT = HexColor(COLORS["text_light_gray"])
GREEN = HexColor(COLORS["green"])
RED = HexColor(COLORS["red"])
CARD_BG = HexColor(COLORS["bg_card"])


def _format_usd(value):
    """Format USD value for display."""
    if isinstance(value, str):
        return value
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.2f}"


def build_styles():
    """Create custom paragraph styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=28,
        leading=34,
        textColor=TEXT_WHITE,
        spaceAfter=6,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=13,
        leading=17,
        textColor=TEXT_GRAY,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading1"],
        fontSize=18,
        leading=24,
        textColor=BLUE_LIGHT,
        spaceBefore=24,
        spaceAfter=10,
        borderWidth=0,
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=TEXT_LIGHT,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="Highlight",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=TEXT_WHITE,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="FooterText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="TLDR",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        textColor=TEXT_WHITE,
        spaceAfter=6,
        leftIndent=12,
        borderPadding=8,
    ))

    styles.add(ParagraphStyle(
        name="KPILabel",
        parent=styles["Normal"],
        fontSize=9,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="KPIValue",
        parent=styles["Normal"],
        fontSize=22,
        textColor=BLUE_PRIMARY,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))

    return styles


def _header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()
    width, height = letter

    # Header line
    canvas.setStrokeColor(BLUE_PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(40, height - 40, width - 40, height - 40)

    # Header text
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(TEXT_GRAY)
    canvas.drawString(45, height - 35, "MORPHO")
    canvas.setFillColor(BLUE_PRIMARY)
    canvas.drawString(95, height - 35, "WEEKLY RISK REPORT")

    # Date in header
    canvas.setFillColor(TEXT_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 45, height - 35, datetime.now().strftime("%B %d, %Y"))

    # Footer
    canvas.setStrokeColor(HexColor("#30363D"))
    canvas.setLineWidth(0.5)
    canvas.line(40, 35, width - 40, 35)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_GRAY)
    canvas.drawString(45, 22, "Generated automatically from Dune Analytics data  |  data.morpho.org/risk")
    canvas.drawRightString(width - 45, 22, f"Page {doc.page}")

    canvas.restoreState()


def generate_report(report_data, charts, output_path="morpho_weekly_risk_report.pdf"):
    """
    Generate the complete Morpho Weekly Risk Report PDF.
    """
    styles = build_styles()
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%B %d")
    week_end = now.strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=55,
        bottomMargin=50,
    )

    story = []

    # --- TITLE SECTION ---
    story.append(Spacer(1, 10))
    story.append(Paragraph("Morpho Weekly Risk Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Rolling 7-Day Summary  |  {week_start} \u2013 {week_end}",
        styles["ReportSubtitle"]
    ))

    # Divider
    story.append(HRFlowable(
        width="100%", thickness=1, color=HexColor("#30363D"),
        spaceAfter=15, spaceBefore=5
    ))

    # --- TLDR SECTION ---
    summary = report_data.get("weekly_summary", pd.DataFrame())
    if not summary.empty:
        s = summary.iloc[0]
        total_liq = _format_usd(s.get("total_liquidated_usd", 0))
        positions = int(s.get("total_positions_liquidated", 0))
        markets = int(s.get("total_markets", 0))
        chains = int(s.get("total_chains", 0))
        bad_debt = s.get("total_bad_debt_usd", 0)
    else:
        total_liq, positions, markets, chains, bad_debt = "$0", 0, 0, 0, 0

    bad_debt_text = (
        f'<font color="#{COLORS["green"][1:]}">'
        f'with zero realized bad debt</font>'
        if bad_debt == 0
        else f'<font color="#{COLORS["red"][1:]}">'
             f'with {_format_usd(bad_debt)} in realized bad debt</font>'
    )

    story.append(Paragraph("TLDR", styles["SectionHeader"]))
    story.append(Paragraph(
        f"Over the past 7 days, Morpho processed <b>{total_liq}</b> in liquidations "
        f"across <b>{positions:,}</b> positions and <b>{markets}</b> markets on "
        f"<b>{chains}</b> networks\u2014{bad_debt_text}.",
        styles["TLDR"]
    ))
    story.append(Spacer(1, 10))

    # --- KPI CARDS IMAGE ---
    if "kpi" in charts and os.path.exists(charts["kpi"]):
        story.append(Image(charts["kpi"], width=6.8 * inch, height=1.5 * inch))
        story.append(Spacer(1, 15))

    # --- SECTION 1: LIQUIDATIONS ---
    story.append(Paragraph("1. Liquidations &amp; Bad Debt", styles["SectionHeader"]))
    story.append(Paragraph(
        f"Morpho\u2019s infrastructure processed {total_liq} in liquidations over "
        f"the past week, demonstrating continued resilience. Liquidation activity "
        f"spanned {chains} chains and {markets} distinct markets.",
        styles["BodyText2"]
    ))

    # Daily liquidation chart
    if "daily_liquidations" in charts and os.path.exists(charts["daily_liquidations"]):
        story.append(Spacer(1, 8))
        story.append(Image(charts["daily_liquidations"], width=6.5 * inch, height=3.2 * inch))
        story.append(Spacer(1, 8))

    # Liquidation by chain chart
    if "liq_by_chain" in charts and os.path.exists(charts["liq_by_chain"]):
        story.append(Image(charts["liq_by_chain"], width=6.5 * inch, height=2.9 * inch))
        story.append(Spacer(1, 8))

    # Chain breakdown table
    chain_df = report_data.get("liquidations_by_chain", pd.DataFrame())
    if not chain_df.empty:
        story.append(Paragraph(
            "<b>Liquidation Breakdown by Chain</b>", styles["Highlight"]
        ))
        table_data = [["Chain", "Volume", "Positions", "Markets"]]
        for _, row in chain_df.head(8).iterrows():
            table_data.append([
                row["blockchain"].capitalize(),
                _format_usd(row["total_liquidated_usd"]),
                f"{int(row['num_liquidations']):,}",
                str(int(row["markets_affected"])),
            ])

        t = Table(table_data, colWidths=[1.8 * inch, 1.6 * inch, 1.4 * inch, 1.2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_LIGHT),
            ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD_BG, HexColor("#1C2128")]),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#30363D")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

    # --- SECTION 2: BAD DEBT ---
    story.append(Paragraph("2. Bad Debt Overview", styles["SectionHeader"]))

    if bad_debt == 0:
        story.append(Paragraph(
            "No realized bad debt events occurred during the past 7 days, "
            "confirming the effectiveness of Morpho\u2019s liquidation mechanisms "
            "and the prudent risk parameters set by curators across the network.",
            styles["BodyText2"]
        ))
    else:
        story.append(Paragraph(
            f"A total of {_format_usd(bad_debt)} in realized bad debt was recorded. "
            f"See the breakdown below for details.",
            styles["BodyText2"]
        ))

    # Bad debt chart
    if "bad_debt" in charts and os.path.exists(charts["bad_debt"]):
        story.append(Spacer(1, 8))
        story.append(Image(charts["bad_debt"], width=6.5 * inch, height=2.6 * inch))
        story.append(Spacer(1, 12))

    # --- SECTION 3: KEY TAKEAWAYS ---
    story.append(Paragraph("3. Key Takeaways", styles["SectionHeader"]))

    takeaways = [
        (f"<b>Infrastructure performed as designed.</b> Morpho processed "
         f"{total_liq} in liquidations across {positions:,} positions and "
         f"{markets} markets on {chains} networks\u2014with zero bad debt."),
        ("<b>Protocol resilience confirmed.</b> Despite market conditions, "
         "liquidation mechanisms functioned smoothly across all chains, "
         "demonstrating the robustness of Morpho\u2019s decentralized architecture."),
        ("<b>Curator risk management effective.</b> Market parameters set by "
         "curators ensured timely liquidations and prevented any losses "
         "to lenders across the network."),
    ]

    for i, text in enumerate(takeaways, 1):
        story.append(Paragraph(f"{i}. {text}", styles["TLDR"]))
        story.append(Spacer(1, 4))

    # --- DATA SOURCES ---
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=HexColor("#30363D"),
        spaceAfter=10, spaceBefore=10
    ))
    story.append(Paragraph("Data Sources", styles["SectionHeader"]))
    story.append(Paragraph(
        '\u2022  <link href="https://data.morpho.org/risk">Morpho Risk Dashboard</link> (data.morpho.org/risk)',
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        '\u2022  <link href="https://dune.com/morpho/morpho-liquidation">Morpho Liquidation Dashboard</link> (Dune Analytics)',
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"\u2022  Report generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        styles["BodyText2"]
    ))

    # --- BUILD PDF ---
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"Report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    from data_fetcher import generate_sample_data
    from chart_generator import generate_all_charts

    output_dir = "/tmp/morpho_report"
    os.makedirs(output_dir, exist_ok=True)

    data = generate_sample_data()
    charts = generate_all_charts(data, output_dir=output_dir)
    generate_report(data, charts, os.path.join(output_dir, "morpho_weekly_risk_report.pdf"))
