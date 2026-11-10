"""Render presentation/5_to_7_minute_script.md into a print-friendly PDF.
Run from the project root:  python presentation/build/make_script_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parents[2]
import sys
SRC = ROOT / "presentation" / (sys.argv[1] if len(sys.argv) > 1 else "5_to_7_minute_script.md")
OUT = ROOT / "presentation" / (sys.argv[2] if len(sys.argv) > 2 else "Presentation_Script.pdf")

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DV-I", F + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DV-BI", F + "DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

NAVY = colors.HexColor("#0B1F33")
INK2 = colors.HexColor("#3D4F63")
BLUE = colors.HexColor("#1E5AA8")
TINT = colors.HexColor("#EEF3F8")
PEACH = colors.HexColor("#FBE9E0")
GRID = colors.HexColor("#D5DCE4")
MEMBER_COL = {"SRUSHTI": colors.HexColor("#1E5AA8"), "AGADH": colors.HexColor("#1BAF7A"),
              "SNEH": colors.HexColor("#EB6834")}

def S(name, **kw):
    base = {"fontName": "DV", "textColor": NAVY}
    base.update(kw)
    base.setdefault("leading", base.get("fontSize", 10) * 1.35)
    return ParagraphStyle(name, **base)
st = {
    "title": S("title", fontSize=20, fontName="DV-B", spaceAfter=4, leading=25),
    "sub": S("sub", fontSize=11, textColor=INK2, spaceAfter=2),
    "body": S("body", fontSize=9.5, textColor=INK2, spaceAfter=3),
    "member": S("member", fontSize=15, fontName="DV-B", textColor=colors.white, leading=20),
    "slide": S("slide", fontSize=12.5, fontName="DV-B", spaceBefore=6, spaceAfter=2),
    "meta": S("meta", fontSize=9, textColor=INK2, spaceAfter=4),
    "speak": S("speak", fontSize=12.5, leading=19, textColor=NAVY),
    "trans": S("trans", fontSize=11.5, leading=17, fontName="DV-I", textColor=NAVY),
    "h2": S("h2", fontSize=13, fontName="DV-B", spaceBefore=8, spaceAfter=4),
    "bullet": S("bullet", fontSize=10, textColor=NAVY, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "cell": S("cell", fontSize=9.5), "cellb": S("cellb", fontSize=9.5, fontName="DV-B", textColor=colors.white),
}


def inline(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<font face='DV'>\1</font>", t)
    return t


def boxed(par, bg, border):
    tb = Table([[par]], colWidths=[170 * mm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.6, border),
                            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return tb


def member_bar(text, col):
    tb = Table([[Paragraph(inline(text), st["member"])]], colWidths=[170 * mm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return tb


def md_table(rows):
    data = [[Paragraph(inline(c), st["cellb"] if i == 0 else st["cell"]) for c in r] for i, r in enumerate(rows)]
    tb = Table(data, colWidths=[24 * mm, 16 * mm, 82 * mm, 18 * mm, 20 * mm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return tb


def build():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    story, i, current_col, pending_slide = [], 0, BLUE, []
    table_rows, transition_next = [], False

    def flush_slide():
        if pending_slide:
            story.append(KeepTogether(list(pending_slide)))
            pending_slide.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                table_rows.append(cells)
            i += 1
            if i >= len(lines) or not lines[i].startswith("|"):
                story.append(md_table(table_rows)); story.append(Spacer(1, 6)); table_rows = []
            continue
        if ln.startswith("# "):
            story.append(Paragraph(inline(ln[2:]), st["title"]))
        elif ln.startswith("## MEMBER"):
            flush_slide()
            name = ln.split(":", 1)[1].strip()
            key = name.split()[0]
            current_col = MEMBER_COL.get(key, BLUE)
            if not ln.startswith("## MEMBER 1"):
                story.append(PageBreak())
            else:
                story.append(PageBreak())
            story.append(member_bar(name.title().replace("(≈", "(≈"), current_col))
            story.append(Spacer(1, 6))
        elif ln.startswith("## "):
            flush_slide()
            story.append(Spacer(1, 10))
            story.append(Paragraph(inline(ln[3:]), st["h2"]))
        elif ln.startswith("### "):
            flush_slide()
            pending_slide.append(Paragraph(inline(ln[4:]), st["slide"]))
        elif ln.startswith("**Transition:**"):
            transition_next = True
        elif ln.startswith("> "):
            text = inline(ln[2:])
            if transition_next:
                flush_slide()
                story.append(Spacer(1, 2))
                story.append(boxed(Paragraph("<b>Hand-off:</b> " + text, st["trans"]), PEACH, current_col))
                story.append(Spacer(1, 6))
                transition_next = False
            elif pending_slide:
                pending_slide.append(boxed(Paragraph(text, st["speak"]), TINT, current_col))
                pending_slide.append(Spacer(1, 6))
            else:
                story.append(boxed(Paragraph(text, st["body"]), PEACH, GRID)); story.append(Spacer(1, 6))
        elif ln.startswith("- "):
            flush_slide()
            story.append(Paragraph(inline(ln[2:]), st["bullet"], bulletText="•"))
        elif ln.strip() in ("", "---"):
            pass
        else:
            target = pending_slide if pending_slide else story
            style = st["meta"] if pending_slide else (st["sub"] if i < 4 else st["body"])
            target.append(Paragraph(inline(ln), style))
        i += 1
    flush_slide()

    def footer(c, d):
        c.saveState(); c.setFont("DV", 8); c.setFillColor(INK2)
        c.drawString(20 * mm, 10 * mm, "ML Project Review 2 · Presentation script · Srushti More [298] · Agadh Khanolkar [299] · Sneh Prasad [311]")
        c.drawRightString(190 * mm, 10 * mm, f"Page {d.page}"); c.restoreState()

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm, title="Presentation Script: Financial Risk Profiling and Regime Detection",
                            author="Srushti More, Agadh Khanolkar, Sneh Prasad")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
