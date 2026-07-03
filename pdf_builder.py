from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

styles = getSampleStyleSheet()
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=10, leading=13)
center_style = ParagraphStyle("center", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER)
bold_center = ParagraphStyle("bcenter", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER, fontName="Helvetica-Bold")


def build_paper_pdf(path, meta, sections):
    doc = SimpleDocTemplate(path, pagesize=A4,
                             topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm)
    story = []

    story.append(Paragraph(meta.get("college", "COLLEGE NAME"), ParagraphStyle(
        "college", parent=styles["Title"], fontSize=14, alignment=TA_CENTER, spaceAfter=2)))
    if meta.get("college_sub"):
        story.append(Paragraph(meta["college_sub"], ParagraphStyle(
            "sub", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(meta.get("exam_title", "Theory Examination"), ParagraphStyle(
        "examtitle", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=8)))

    info_data = [
        ["Course:", meta.get("course", ""), "Semester:", meta.get("semester", ""), "Time:", meta.get("time", "")],
        ["Branch:", meta.get("branch", ""), "Subject code:", meta.get("subject_code", ""), "MM:", str(meta.get("max_marks", ""))],
        ["Subject:", meta.get("subject", ""), "", "", "", ""],
    ]
    info_table = Table(info_data, colWidths=[20 * mm, 40 * mm, 25 * mm, 30 * mm, 15 * mm, 30 * mm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTNAME", (4, 0), (4, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (1, 2), (5, 2)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    for s_idx, section in enumerate(sections):
        header = f"SECTION {section['label']}"
        marks_each = section.get("marks_each")
        count = len(section.get("questions", []))
        total = section.get("total_marks", marks_each * count if marks_each else "")

        story.append(Paragraph(header, ParagraphStyle(
            "sechead", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2)))

        note = section.get("note", "")
        note_row = [[Paragraph(note, cell_style), Paragraph(f"{marks_each} X {count} = {total}", bold_center)]]
        note_table = Table(note_row, colWidths=[140 * mm, 40 * mm])
        note_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(note_table)

        rows = [[Paragraph("Q No", bold_center), Paragraph("Statement", bold_center),
                 Paragraph("Bloom's Level", bold_center), Paragraph("CO", bold_center),
                 Paragraph("Marks", bold_center)]]

        for q in section["questions"]:
            qtext = q["question"]
            if q.get("or_question"):
                cell_content = Paragraph(qtext, cell_style)
                rows.append([Paragraph(q.get("qno", ""), center_style), cell_content,
                             Paragraph(q.get("bloom", ""), center_style),
                             Paragraph(q.get("co", ""), center_style),
                             Paragraph(str(q.get("marks", marks_each)), center_style)])
                rows.append([Paragraph("", center_style), Paragraph("<b>OR</b>", center_style), "", "", ""])
                rows.append([Paragraph("", center_style), Paragraph(q["or_question"], cell_style),
                             Paragraph(q.get("or_bloom", ""), center_style),
                             Paragraph(q.get("or_co", ""), center_style), ""])
            else:
                rows.append([Paragraph(q.get("qno", ""), center_style), Paragraph(qtext, cell_style),
                             Paragraph(q.get("bloom", ""), center_style),
                             Paragraph(q.get("co", ""), center_style),
                             Paragraph(str(q.get("marks", marks_each)), center_style)])

        q_table = Table(rows, colWidths=[14 * mm, 106 * mm, 25 * mm, 15 * mm, 20 * mm])
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ]
        # merge OR rows for marks/bloom/co columns visually by spanning blank cells
        q_table.setStyle(TableStyle(style_cmds))
        story.append(q_table)
        story.append(Spacer(1, 6))

    note_text = meta.get("footer_note", "")
    if note_text:
        story.append(Spacer(1, 6))
        story.append(Paragraph(note_text, ParagraphStyle("fn", parent=styles["Normal"], fontSize=8)))

    story.append(Spacer(1, 25))
    sign_row = [["____________________", "____________________", "____________________"],
                ["HOD", "PAQIC", "Subject Teacher"]]
    sign_table = Table(sign_row, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sign_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(sign_table)

    doc.build(story)
