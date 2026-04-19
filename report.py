from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from minio import Minio
from datetime import datetime, timedelta
import io
import os
import uuid

# AuditorSEC brand colors
COLOR_PRIMARY = HexColor("#1a1a2e")
COLOR_ACCENT = HexColor("#e94560")
COLOR_HIGH = HexColor("#e94560")
COLOR_MEDIUM = HexColor("#f5a623")
COLOR_LOW = HexColor("#27ae60")
COLOR_CRITICAL = HexColor("#8b0000")

RISK_COLORS = {
    "CRITICAL": COLOR_CRITICAL,
    "HIGH": COLOR_HIGH,
    "MEDIUM": COLOR_MEDIUM,
    "LOW": COLOR_LOW,
}


def get_minio_client() -> Minio:
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False
    )


def ensure_bucket(client: Minio, bucket: str = "audit-reports"):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def generate_pdf_report(
    project_name: str,
    audit_type: str,
    anomalies: list[str],
    risk_level: str,
    recommendations: list[str],
    token_count: int,
    timestamp: str
) -> tuple[str, str]:
    """
    Generates PDF audit report, stores in MinIO.
    Returns (object_name, presigned_url).
    """
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=22, textColor=COLOR_PRIMARY, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey, spaceAfter=20
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=13, textColor=COLOR_PRIMARY, spaceBefore=16, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=15
    )
    risk_style = ParagraphStyle(
        "Risk", parent=styles["Normal"],
        fontSize=18,
        textColor=RISK_COLORS.get(risk_level, COLOR_MEDIUM),
        spaceAfter=8, fontName="Helvetica-Bold"
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey
    )

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm
    )

    story = []

    # Header
    story.append(Paragraph("AuditorSEC", title_style))
    story.append(Paragraph("Security Audit Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_ACCENT, spaceAfter=16))

    # Meta table
    meta_data = [
        ["Project", project_name],
        ["Audit type", audit_type.replace("_", " ").title()],
        ["Date", timestamp[:10]],
        ["Report ID", str(uuid.uuid4())[:8].upper()],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 13*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_PRIMARY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # Risk level
    story.append(Paragraph("Overall Risk Level", section_style))
    story.append(Paragraph(f"● {risk_level}", risk_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12))

    # Findings
    story.append(Paragraph("Findings", section_style))
    if anomalies:
        for i, anomaly in enumerate(anomalies, 1):
            story.append(Paragraph(f"{i}. {anomaly}", body_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No critical anomalies detected.", body_style))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12))

    # Recommendations
    story.append(Paragraph("Recommendations", section_style))
    if recommendations:
        priorities = ["CRITICAL", "HIGH", "HIGH", "MEDIUM", "MEDIUM"]
        rec_data = [["#", "Action", "Priority"]]
        for i, rec in enumerate(recommendations, 1):
            priority = priorities[i-1] if i <= len(priorities) else "LOW"
            rec_data.append([str(i), rec, priority])

        rec_table = Table(rec_data, colWidths=[1*cm, 13.5*cm, 2.5*cm])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(rec_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12))

    # Footer
    story.append(Paragraph(
        f"Generated by AuditorSEC API v0.1 · {timestamp} · "
        f"Tokens analyzed: {token_count} · For internal use only — confidential",
        footer_style
    ))

    doc.build(story)

    # Save to MinIO
    minio = get_minio_client()
    ensure_bucket(minio)

    object_name = (
        f"reports/{datetime.utcnow().strftime('%Y/%m/%d')}/"
        f"{project_name}_{uuid.uuid4().hex[:8]}.pdf"
    )

    pdf_bytes = buffer.getvalue()
    minio.put_object(
        "audit-reports",
        object_name,
        io.BytesIO(pdf_bytes),
        length=len(pdf_bytes),
        content_type="application/pdf"
    )

    url = minio.presigned_get_object(
        "audit-reports",
        object_name,
        expires=timedelta(hours=24)
    )

    return object_name, url
