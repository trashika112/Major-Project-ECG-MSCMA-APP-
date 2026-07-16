import os
import json
import numpy as np
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist_str() -> str:
    """Report timestamps are shown in IST (India Standard Time), not UTC,
    since this app is built for hospital use in India — UTC would show a
    time several hours off from the clock on the wall."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from config import REPORTS_DIR, CLINICAL_DISCLAIMER, N_LEADS

LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF",
              "V1", "V2", "V3", "V4", "V5", "V6"][:N_LEADS]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="HospitalTitle", fontSize=16, leading=20, textColor=colors.HexColor("#0B3B5C"),
                           spaceAfter=2, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Small", fontSize=8, textColor=colors.grey))
styles.add(ParagraphStyle(name="Disclaimer", fontSize=8, textColor=colors.HexColor("#8A5300"),
                           backColor=colors.HexColor("#FFF6E5"), borderPadding=6))


def _build_saliency_heatmap_png(saliency_npz_path: str, record_id: int) -> str | None:
    """Renders the (leads x time) saliency map saved at upload time into a PNG
    for embedding in the PDF. Returns the PNG path, or None if unavailable
    (e.g. older records uploaded before this feature existed)."""
    if not saliency_npz_path or not os.path.exists(saliency_npz_path):
        return None

    import matplotlib
    matplotlib.use("Agg")  # headless — no display needed on the server
    import matplotlib.pyplot as plt

    data = np.load(saliency_npz_path)
    saliency = data["saliency"]  # (leads, T)
    n_leads = saliency.shape[0]
    lead_labels = LEAD_NAMES[:n_leads] if n_leads <= len(LEAD_NAMES) else [f"L{i+1}" for i in range(n_leads)]

    fig, ax = plt.subplots(figsize=(9.0, 3.6), dpi=300)
    im = ax.imshow(saliency, aspect="auto", cmap="inferno",
                    extent=[0, saliency.shape[1], n_leads, 0])
    ax.set_yticks(np.arange(n_leads) + 0.5)
    ax.set_yticklabels(lead_labels, fontsize=11)
    ax.set_xlabel("Sample (10s record)", fontsize=11)
    ax.set_title("Grad×Input Saliency — which lead/time regions drove the top prediction",
                 fontsize=12, pad=10)
    ax.tick_params(axis="x", labelsize=10)
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(labelsize=9)
    cbar.set_label("relative influence", fontsize=10)
    fig.tight_layout()

    png_path = os.path.join(REPORTS_DIR, f"heatmap_{record_id}.png")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return png_path


def build_report_pdf(patient, ecg_record, prediction, hospital_name="ECG Clinical Decision Support System",
                      saliency_path: str | None = None):
    """patient, ecg_record, prediction are ORM objects (models_db.py)."""
    filename = f"report_{patient.patient_code}_{ecg_record.id}.pdf"
    out_path = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                             topMargin=18 * mm, bottomMargin=16 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph(hospital_name, styles["HospitalTitle"]))
    story.append(Paragraph("AI-Assisted ECG Diagnostic Report", styles["Normal"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#0B3B5C")))
    story.append(Spacer(1, 10))

    meta_table = Table([
        ["Patient ID", patient.patient_code, "Date", _now_ist_str()],
        ["Name", patient.name, "Doctor", patient.doctor_name or "-"],
        ["Age / Gender", f"{patient.age or '-'} / {patient.gender or '-'}", "Model", prediction.model_version],
    ], colWidths=[70, 160, 70, 160])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0B3B5C")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#0B3B5C")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    probs = json.loads(prediction.probs_json)
    predicted = json.loads(prediction.predicted_classes_json)

    story.append(Paragraph("<b>Prediction Summary</b>", styles["Heading3"]))
    pred_rows = [["Class", "Probability", "Detected"]]
    for cls, p in sorted(probs.items(), key=lambda kv: -kv[1]):
        pred_rows.append([cls, f"{p*100:.1f}%", "Yes" if cls in predicted else "No"])
    pred_table = Table(pred_rows, colWidths=[120, 120, 120])
    pred_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3B5C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 10))

    risk_color = {"HIGH": "#B91C1C", "MODERATE": "#B45309", "LOW": "#15803D"}.get(prediction.risk_level, "#0B3B5C")
    story.append(Paragraph(
        f"<b>Top Finding:</b> {prediction.top_class} "
        f"(confidence {prediction.top_confidence*100:.1f}%) &nbsp;&nbsp; "
        f"<b>Risk Level:</b> <font color='{risk_color}'>{prediction.risk_level}</font>",
        styles["Normal"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Model Interpretation</b>", styles["Heading3"]))
    story.append(Paragraph(
        f"The model detected patterns most consistent with <b>{prediction.top_class}</b> "
        f"at {prediction.top_confidence*100:.1f}% confidence. Highlighted lead regions "
        f"(see attached ECG viewer) indicate the segments that contributed most strongly "
        f"to this prediction.", styles["Normal"]))
    story.append(Spacer(1, 6))
    suggested = "Immediate cardiology review recommended." if prediction.risk_level == "HIGH" \
        else "Routine clinical correlation recommended."
    story.append(Paragraph(f"<b>Suggested Action:</b> {suggested}", styles["Normal"]))
    story.append(Spacer(1, 14))

    heatmap_png = _build_saliency_heatmap_png(saliency_path, ecg_record.id)
    if heatmap_png:
        story.append(Paragraph("<b>ECG Saliency Heatmap</b>", styles["Heading3"]))
        story.append(Image(heatmap_png, width=170 * mm, height=170 * mm * (3.6 / 9.0)))
        story.append(Paragraph(
            "Highlighted regions indicate ECG segments that contributed most strongly to the "
            "model's decision — not a clinical annotation of the exact lesion location.",
            styles["Small"]))
        story.append(Spacer(1, 12))

    story.append(Paragraph(CLINICAL_DISCLAIMER, styles["Disclaimer"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Report generated: {_now_ist_str()} | "
        f"Record #{ecg_record.id} | File: {ecg_record.original_filename}", styles["Small"]))

    doc.build(story)
    return out_path
