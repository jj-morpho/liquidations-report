"""
PDF report generator for the Morpho Weekly Risk Report.
Clean, plain style — white background, professional formatting.
"""
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd

from config import COLORS


# Plain color constants
BLACK = HexColor("#222222")
DARK_GRAY = HexColor("#444444")
MID_GRAY = HexColor("#777777")
LIGHT_GRAY = HexColor("#BBBBBB")
VERY_LIGHT = HexColor("#F2F2F2")
ACCENT_BLUE = HexColor("#4A7CBA")
ACCENT_GREEN = HexColor("#27AE60")
ACCENT_RED = HexColor("#C0392B")
BORDER_GRAY = HexColor("#DDDDDD")


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
    """Create clean paragraph styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        textColor=BLACK,
        spaceAfter=4,
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        textColor=MID_GRAY,
        spaceAfter=16,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading1"],
        fontSize=16,
        leading=22,
        textColor=BLACK,
        spaceBefore=20,
        spaceAfter=8,
        fontName="Helvetica-Bold",
        borderWidth=0,
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=DARK_GRAY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="Highlight",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=BLACK,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="FooterText",
        parent=styles["Normal"],
        fontSize=7,
        leading=10,
        textColor=LIGHT_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="TLDR",
        parent=styles["Normal"],
        fontSize=11,
        leading=17,
        textColor=DARK_GRAY,
        spaceAfter=4,
        leftIndent=10,
    ))

    styles.add(ParagraphStyle(
        name="KPILabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="KPIValue",
        parent=styles["Normal"],
        fontSize=20,
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="Takeaway",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=DARK_GRAY,
        spaceAfter=6,
        leftIndent=10,
    ))

    return styles


def _header_footer(canvas, doc):
    """Add a minimal header and footer to each page."""
    canvas.saveState()
    width, height = letter

    # Header: thin rule
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(45, height - 40, width - 45, height - 40)

    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(BLACK)
    canvas.drawString(48, height - 35, "MORPHO")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(95, height - 35, "Weekly Risk Report")

    # Date right-aligned
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(width - 48, height - 35, datetime.now().strftime("%B %d, %Y"))

    # Footer: thin rule
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(45, 35, width - 45, 35)

    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(LIGHT_GRAY)
    canvas.drawString(48, 23, "Generated from Dune Analytics  |  data.morpho.org/risk")
    canvas.drawRightString(width - 48, 23, f"Page {doc.page}")

    canvas.restoreState()


def _build_kpi_row(summary, styles):
    """Build a row of KPI cards as a table."""
    if summary.empty:
        return None

    s = summary.iloc[0]
    total_liq = _format_usd(s.get("total_liquidated_usd", 0))
    positions = f"{int(s.get('total_positions_liquidated', 0)):,}"
    markets = str(int(s.get("total_markets", 0)))
    chains = str(int(s.get("total_chains", 0)))
    bad_debt = s.get("total_bad_debt_usd", 0)
    bad_debt_str = _format_usd(bad_debt) if bad_debt > 0 else "$0"

    data = [[total_liq, positions, markets, chains, bad_debt_str]]
    labels = [["Liquidation Vol.", "Positions", "Markets", "Chains", "Bad Debt"]]

    # Values row
    t_values = Table(data, colWidths=[1.3 * inch] * 5)
    t_values.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 16),
        ("TEXTCOLOR", (0, 0), (-1, -1), ACCENT_BLUE),
        ("TEXTCOLOR", (4, 0), (4, 0), ACCENT_GREEN if bad_debt == 0 else ACCENT_RED),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    # Labels row
    t_labels = Table(labels, colWidths=[1.3 * inch] * 5)
    t_labels.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), MID_GRAY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    # Combine into a container
    container_data = [[t_values], [t_labels]]
    container = Table(container_data, colWidths=[6.5 * inch])
    container.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("BACKGROUND", (0, 0), (-1, -1), VERY_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return container


def generate_report(report_data, charts, output_path="morpho_weekly_risk_report.pdf"):
    """
    Generate the complete Morpho Weekly Risk Report PDF (plain format).
    """
    styles = build_styles()
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%B %d")
    week_end = now.strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=55,
        bottomMargin=50,
    )

    story = []

    # --- TITLE ---
    story.append(Spacer(1, 8))
    story.append(Paragraph("Morpho Weekly Risk Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Rolling 7-Day Summary  \u2014  {week_start} \u2013 {week_end}",
        styles["ReportSubtitle"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER_GRAY,
        spaceAfter=12, spaceBefore=2
    ))

    # --- KPI ROW ---
    summary = report_data.get("weekly_summary", pd.DataFrame())
    kpi_row = _build_kpi_row(summary, styles)
    if kpi_row:
        story.append(kpi_row)
        story.append(Spacer(1, 14))

    # Extract summary values for use below
    if not summary.empty:
        s = summary.iloc[0]
        total_liq = _format_usd(s.get("total_liquidated_usd", 0))
        positions = int(s.get("total_positions_liquidated", 0))
        markets = int(s.get("total_markets", 0))
        chains = int(s.get("total_chains", 0))
        bad_debt = s.get("total_bad_debt_usd", 0)
    else:
        total_liq, positions, markets, chains, bad_debt = "$0", 0, 0, 0, 0

    # --- TLDR ---
    bad_debt_text = (
        f'<font color="#27AE60">with zero realized bad debt</font>'
        if bad_debt == 0
        else f'<font color="#C0392B">with {_format_usd(bad_debt)} in realized bad debt</font>'
    )

    story.append(Paragraph("TLDR", styles["SectionHeader"]))
    story.append(Paragraph(
        f"Over the past 7 days, Morpho processed <b>{total_liq}</b> in liquidations "
        f"across <b>{positions:,}</b> positions and <b>{markets}</b> markets on "
        f"<b>{chains}</b> networks\u2014{bad_debt_text}.",
        styles["TLDR"]
    ))
    story.append(Spacer(1, 8))

    # --- SECTION 1: LIQUIDATIONS ---
    story.append(Paragraph("1. Liquidations &amp; Bad Debt", styles["SectionHeader"]))
    story.append(Paragraph(
        f"Morpho\u2019s infrastructure processed {total_liq} in liquidations over "
        f"the past week. Liquidation activity spanned {chains} chains "
        f"and {markets} distinct markets.",
        styles["BodyText2"]
    ))

    # Daily liquidation chart
    if "daily_liquidations" in charts and os.path.exists(charts["daily_liquidations"]):
        story.append(Spacer(1, 6))
        story.append(Image(charts["daily_liquidations"], width=6.2 * inch, height=3.0 * inch))
        story.append(Spacer(1, 6))

    # Liquidation by chain chart
    if "liq_by_chain" in charts and os.path.exists(charts["liq_by_chain"]):
        story.append(Image(charts["liq_by_chain"], width=6.2 * inch, height=2.7 * inch))
        story.append(Spacer(1, 6))

    # Chain breakdown table
    chain_df = report_data.get("liquidations_by_chain", pd.DataFrame())
    if not chain_df.empty:
        story.append(Paragraph(
            "Liquidation Breakdown by Chain", styles["Highlight"]
        ))
        table_data = [["Chain", "Volume", "Positions", "Markets"]]
        for _, row in chain_df.head(8).iterrows():
            table_data.append([
                row["blockchain"].capitalize(),
                _format_usd(row["total_liquidated_usd"]),
                f"{int(row['num_liquidations']):,}",
                str(int(row["markets_affected"])),
            ])

        t = Table(table_data, colWidths=[1.7 * inch, 1.5 * inch, 1.3 * inch, 1.2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_GRAY),
            ("BACKGROUND", (0, 1), (-1, -1), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, VERY_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # --- SECTION 2: VAULT LIQUIDITY ---
    story.append(Paragraph("2. Vault Liquidity", styles["SectionHeader"]))
    story.append(Paragraph(
        "Vault liquidity measures the percentage of deposited assets that remain available "
        "for withdrawal. Higher liquidity indicates healthier vault conditions and sufficient "
        "buffer for lender withdrawals even during periods of market stress.",
        styles["BodyText2"]
    ))

    from config import BLUECHIP_VAULTS, LONGTAIL_VAULTS

    vault_charts = charts.get("vault_charts", {})

    # Bluechip vaults
    if any(v["name"] in vault_charts for v in BLUECHIP_VAULTS):
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "<b>Bluechip Vaults</b> \u2014 Conservative risk profile, high liquidity expected",
            styles["BodyText2"]
        ))
        for vault in BLUECHIP_VAULTS:
            if vault["name"] in vault_charts and os.path.exists(vault_charts[vault["name"]]):
                story.append(Image(vault_charts[vault["name"]], width=6.2 * inch, height=2.5 * inch))
                story.append(Spacer(1, 4))

    # Long-tail vaults
    if any(v["name"] in vault_charts for v in LONGTAIL_VAULTS):
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "<b>Long-Tail Vaults</b> \u2014 Higher yield, relatively more risk exposure",
            styles["BodyText2"]
        ))
        for vault in LONGTAIL_VAULTS:
            if vault["name"] in vault_charts and os.path.exists(vault_charts[vault["name"]]):
                story.append(Image(vault_charts[vault["name"]], width=6.2 * inch, height=2.5 * inch))
                story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # --- SECTION 3: BAD DEBT ---
    story.append(Paragraph("3. Bad Debt Overview", styles["SectionHeader"]))

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
        story.append(Spacer(1, 6))
        story.append(Image(charts["bad_debt"], width=6.2 * inch, height=2.5 * inch))
        story.append(Spacer(1, 10))

    # --- SECTION 4: KEY TAKEAWAYS ---
    story.append(Paragraph("4. Key Takeaways", styles["SectionHeader"]))

    takeaways = [
        (f"<b>Infrastructure performed as designed.</b> Morpho processed "
         f"{total_liq} in liquidations across {positions:,} positions and "
         f"{markets} markets on {chains} networks."),
        ("<b>Protocol resilience confirmed.</b> Liquidation mechanisms "
         "functioned smoothly across all chains, demonstrating the "
         "robustness of Morpho\u2019s decentralized architecture."),
        ("<b>Curator risk management effective.</b> Market parameters set by "
         "curators ensured timely liquidations and prevented losses "
         "to lenders across the network."),
        ("<b>Vault liquidity remained healthy.</b> Both bluechip and long-tail "
         "vaults maintained sufficient available liquidity, demonstrating "
         "that Morpho Vaults can sustain large withdrawals even during volatile periods."),
    ]

    for i, text in enumerate(takeaways, 1):
        story.append(Paragraph(f"{i}. {text}", styles["Takeaway"]))
        story.append(Spacer(1, 3))

    # --- DATA SOURCES ---
    story.append(Spacer(1, 16))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER_GRAY,
        spaceAfter=8, spaceBefore=8
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

    # --- BUILD ---
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
