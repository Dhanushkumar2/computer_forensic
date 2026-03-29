"""
PDF reporting utilities for forensic cases.
Generates formal reports with charts and ML inference summaries.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import patches
import textwrap

matplotlib.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
})

from django.conf import settings

from .mongodb_service import mongo_service


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _case_details_payload(case) -> Dict:
    return {
        "Case ID": case.case_id,
        "Title": case.title,
        "Status": case.status,
        "Priority": case.priority,
        "Image Path": case.image_path,
        "Image Name": case.image_name,
        "Image Size": case.image_size,
        "Created At": case.created_at.isoformat() if hasattr(case, "created_at") and case.created_at else "",
        "Extraction Time": case.extraction_time,
    }


def _artifact_counts(summary: Dict) -> Dict[str, int]:
    counts = summary.get("counts", {}) if summary else {}
    return {
        "Browser History": _safe_int(counts.get("browser_history")),
        "Browser Cookies": _safe_int(counts.get("browser_cookies")),
        "Browser Downloads": _safe_int(counts.get("browser_downloads")),
        "Registry": _safe_int(counts.get("registry_artifacts")),
        "Filesystem": _safe_int(counts.get("filesystem_artifacts")),
        "USB Devices": _safe_int(counts.get("usb_devices")),
        "Event Logs": _safe_int(counts.get("event_logs")),
        "Deleted Files": _safe_int(counts.get("deleted_files")),
        "Installed Programs": _safe_int(counts.get("installed_programs")),
        "User Activity": _safe_int(counts.get("user_activity")),
        "Android Artifacts": _safe_int(counts.get("android_artifacts")),
    }


def _activity_by_hour(stats: Dict) -> List[Tuple[int, int]]:
    items = stats.get("activity_by_hour", []) if stats else []
    results = []
    for entry in items:
        hour = entry.get("_id")
        count = entry.get("count")
        if hour is None:
            continue
        results.append((int(hour), int(count or 0)))
    if not results:
        return [(h, 0) for h in range(24)]
    results = sorted(results, key=lambda x: x[0])
    return results


def _parse_timestamp(ts: str):
    if not ts:
        return None
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", ""))
    except Exception:
        pass
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts.replace("Z", ""), fmt)
        except Exception:
            continue
    return None


def _timeline_heatmap(case_id: str) -> Tuple[List[int], List[str], List[List[int]]]:
    """Return hours, dates, matrix counts for heatmap."""
    events = list(mongo_service.storage.collections["timeline_events"].find({"case_id": case_id}))
    by_day_hour: Dict[str, Dict[int, int]] = {}
    for e in events:
        ts = _parse_timestamp(e.get("timestamp"))
        if not ts:
            continue
        day = ts.strftime("%Y-%m-%d")
        hour = ts.hour
        by_day_hour.setdefault(day, {})
        by_day_hour[day][hour] = by_day_hour[day].get(hour, 0) + 1

    dates = sorted(by_day_hour.keys())
    hours = list(range(24))
    matrix = []
    for day in dates:
        row = []
        for h in hours:
            row.append(by_day_hour.get(day, {}).get(h, 0))
        matrix.append(row)
    return hours, dates, matrix


def _timeline_range(case_id: str) -> Tuple[str | None, str | None, int]:
    events = list(mongo_service.storage.collections["timeline_events"].find({"case_id": case_id}))
    timestamps = []
    for e in events:
        ts = _parse_timestamp(e.get("timestamp"))
        if ts:
            timestamps.append(ts)
    if not timestamps:
        return None, None, 0
    start = min(timestamps).strftime("%Y-%m-%d %H:%M:%S")
    end = max(timestamps).strftime("%Y-%m-%d %H:%M:%S")
    return start, end, len(timestamps)


def _write_heatmap(pdf: PdfPages, hours: List[int], dates: List[str], matrix: List[List[int]], case_id: str, page_number: int):
    fig, ax = plt.subplots(figsize=(11, 6))
    _draw_page_border(fig)
    if not matrix:
        ax.text(0.5, 0.5, "No timeline events available", ha="center", va="center")
        ax.axis("off")
        _page_footer(fig, f"Case {case_id}", page_number)
        pdf.savefig(fig)
        plt.close(fig)
        return
    im = ax.imshow(matrix, aspect="auto", cmap="viridis")
    ax.set_title("Timeline Heatmap (Events by Day/Hour)", fontsize=14)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Date")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([str(h) for h in range(0, 24, 2)])
    ax.set_yticks(range(len(dates)))
    ax.set_yticklabels(dates, fontsize=8)
    fig.colorbar(im, ax=ax, label="Events")
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _write_top_domains(pdf: PdfPages, stats: Dict, case_id: str, page_number: int):
    domains = stats.get("top_domains", []) if stats else []
    labels = [d.get("_id") or "unknown" for d in domains]
    values = [d.get("visit_count", 0) for d in domains]
    fig, ax = plt.subplots(figsize=(10, 4))
    _draw_page_border(fig)
    if not values:
        ax.text(0.5, 0.5, "No top domains available", ha="center", va="center")
    else:
        ax.bar(labels, values, color="#f0a54b")
        ax.set_title("Top Visited Domains", fontsize=14)
        ax.set_ylabel("Visit Count")
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _write_usb_vendors(pdf: PdfPages, stats: Dict, case_id: str, page_number: int):
    vendors = stats.get("usb_manufacturers", []) if stats else []
    labels = [v.get("_id") or "unknown" for v in vendors]
    values = [v.get("count", 0) for v in vendors]
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_page_border(fig)
    if not values:
        ax.text(0.5, 0.5, "No USB vendor data available", ha="center", va="center")
    else:
        ax.bar(labels, values, color="#7b6cff")
        ax.set_title("USB Vendors", fontsize=14)
        ax.set_ylabel("Devices")
        ax.tick_params(axis="x", rotation=30, labelsize=8)
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _page_header(fig, title: str, subtitle: str | None = None):
    fig.text(0.5, 0.96, title, ha="center", fontsize=16, weight="bold")
    if subtitle:
        fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9)


def _page_footer(fig, text: str, page_number: int | None = None):
    footer = text
    if page_number is not None:
        footer = f"{text} | Page {page_number}"
    fig.text(0.5, 0.03, footer, ha="center", fontsize=8, color="#555555")


def _new_page():
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")
    _draw_page_border(fig)
    return fig


def _draw_page_border(fig):
    rect = patches.Rectangle(
        (0.04, 0.04),
        0.92,
        0.92,
        linewidth=1.0,
        edgecolor="#2c2c2c",
        facecolor="none",
        transform=fig.transFigure,
        zorder=10,
    )
    fig.add_artist(rect)


def _draw_wrapped_text(fig, x: float, y: float, text: str, max_chars: int, line_height: float, fontsize: int = 10, weight: str | None = None):
    lines = textwrap.wrap(text, width=max_chars) if text else [""]
    for line in lines:
        fig.text(x, y, line, fontsize=fontsize, weight=weight)
        y -= line_height
    return y


def _write_title_page(pdf: PdfPages, case, summary: Dict, stats: Dict, page_number: int):
    fig = _new_page()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _page_header(fig, "Forensic Investigation Report", f"Generated: {now}")

    details = _case_details_payload(case)
    y = 0.86
    fig.text(0.08, y, "Case Details", fontsize=14, weight="bold")
    y -= 0.03
    for key, value in details.items():
        fig.text(0.08, y, f"{key}:", fontsize=10, weight="bold")
        y = _draw_wrapped_text(fig, 0.28, y, f"{value}", max_chars=60, line_height=0.022, fontsize=10)
        if y < 0.18:
            break

    counts = _artifact_counts(summary)
    total_artifacts = sum(counts.values())
    fig.text(0.08, 0.28, "Summary", fontsize=14, weight="bold")
    fig.text(0.08, 0.25, f"Total Artifacts: {total_artifacts}", fontsize=11)
    fig.text(0.08, 0.22, f"Activity Hours Logged: {len(_activity_by_hour(stats))}", fontsize=11)

    _page_footer(fig, f"Case {case.case_id}", page_number)

    pdf.savefig(fig)
    plt.close(fig)


def _format_top_list(items: List[str], limit: int = 5) -> str:
    trimmed = [i for i in items if i]
    if not trimmed:
        return "None"
    return ", ".join(trimmed[:limit])


def _write_narrative(pdf: PdfPages, case, summary: Dict, stats: Dict, ml_anomalies: List[Dict], android_anomalies: List[Dict], page_number: int):
    """Write an explainable narrative section."""
    counts = _artifact_counts(summary)
    total_artifacts = sum(counts.values())
    top_categories = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_cat_text = ", ".join([f"{name} ({count})" for name, count in top_categories if count > 0]) or "No dominant categories"

    activity_hours = _activity_by_hour(stats)
    peak_hour = max(activity_hours, key=lambda x: x[1])[0] if activity_hours else None
    peak_count = max(activity_hours, key=lambda x: x[1])[1] if activity_hours else 0

    usb_vendors = stats.get("usb_manufacturers", []) if stats else []
    usb_vendor_list = [str(v.get("_id") or "unknown") for v in usb_vendors]

    top_domains = stats.get("top_domains", []) if stats else []
    domain_list = [str(d.get("_id") or "unknown") for d in top_domains]

    ml_scores = [_safe_float(a.get("anomaly_score")) for a in (ml_anomalies or [])]
    ml_avg = round(sum(ml_scores) / len(ml_scores), 3) if ml_scores else 0
    ml_max = round(max(ml_scores), 3) if ml_scores else 0
    ml_labels = {}
    for a in (ml_anomalies or []):
        label = a.get("label", "Unknown")
        ml_labels[label] = ml_labels.get(label, 0) + 1
    ml_label_text = ", ".join([f"{k}: {v}" for k, v in ml_labels.items()]) or "None"

    ml_count = len(ml_anomalies or [])
    android_ml_count = len(android_anomalies or [])
    timeline_start, timeline_end, timeline_count = _timeline_range(case.case_id)

    lines = [
        "Executive Summary",
        f"This report provides a structured overview of forensic artifacts and ML anomaly signals for case {case.case_id}.",
        f"A total of {total_artifacts} artifacts were indexed. The most represented categories were: {top_cat_text}.",
        f"Peak activity was observed around hour {peak_hour} with {peak_count} events." if peak_hour is not None else "Timeline activity was insufficient to determine a peak hour.",
        f"Top domains observed: {_format_top_list(domain_list)}.",
        f"USB vendors observed: {_format_top_list(usb_vendor_list)}.",
        f"Windows ML anomalies flagged: {ml_count} (avg score {ml_avg}, max score {ml_max}).",
        f"Windows ML label breakdown: {ml_label_text}.",
        f"Android ML anomalies flagged: {android_ml_count}.",
        f"Timeline coverage: {timeline_start} to {timeline_end} ({timeline_count} events)." if timeline_start else "Timeline coverage: no events available.",
        "Scope & Data Sources",
        "This report is generated from parsed disk artifacts, timeline events, and ML inference outputs stored in the case database.",
        "Where timestamps or records are missing, the report notes limitations and excludes unsupported conclusions.",
        "Methodology",
        "Artifacts are categorized by type (browser, registry, filesystem, USB, events, etc.).",
        "ML inference uses a GAT model for Windows artifacts and a TabTransformer for Android features to surface high-score anomalies.",
        "Interpretation",
        "High anomaly scores indicate deviations from baseline patterns. These are indicators only and require analyst validation.",
        "Per‑artifact insights highlight dominant evidence categories to guide investigation focus.",
        "Recommendations",
        "Review highest‑score anomalies, correlate timeline peaks with filesystem and registry changes, and preserve related evidence for follow‑up.",
        "Limitations & Ethics",
        "This report is automatically generated and may contain incomplete or noisy data. Do not treat ML outputs as definitive proof.",
    ]

    fig = _new_page()
    _page_header(fig, "Narrative Analysis", "Explainable summary and investigative context")

    y = 0.88
    for idx, line in enumerate(lines):
        if line in {"Executive Summary", "Interpretation", "Recommendations"}:
            fig.text(0.08, y, line, fontsize=14, weight="bold")
            y -= 0.035
            continue
        y = _draw_wrapped_text(fig, 0.08, y, line, max_chars=90, line_height=0.022, fontsize=10)
        if y < 0.08:
            break

    _page_footer(fig, f"Case {case.case_id}", page_number)

    pdf.savefig(fig)
    plt.close(fig)


def _write_bar_chart(pdf: PdfPages, counts: Dict[str, int], case_id: str, page_number: int):
    labels = list(counts.keys())
    values = list(counts.values())
    fig, ax = plt.subplots(figsize=(10, 6))
    _draw_page_border(fig)
    ax.bar(labels, values, color="#2f8bd8")
    ax.set_title("Artifact Counts by Category", fontsize=14)
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _write_pie_chart(pdf: PdfPages, counts: Dict[str, int], case_id: str, page_number: int):
    labels = [k for k, v in counts.items() if v > 0]
    values = [v for v in counts.values() if v > 0]
    fig, ax = plt.subplots(figsize=(8, 6))
    _draw_page_border(fig)
    if values:
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.set_title("Artifact Distribution", fontsize=14)
    else:
        ax.text(0.5, 0.5, "No artifact counts available", ha="center", va="center")
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _write_activity_line(pdf: PdfPages, activity_hours: List[Tuple[int, int]], case_id: str, page_number: int):
    hours = [h for h, _ in activity_hours]
    counts = [c for _, c in activity_hours]
    fig, ax = plt.subplots(figsize=(10, 4))
    _draw_page_border(fig)
    ax.plot(hours, counts, marker="o", color="#5ad1b8")
    ax.set_title("Activity by Hour", fontsize=14)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Events")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.3)
    _page_footer(fig, f"Case {case_id}", page_number)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def _write_section_heading(pdf: PdfPages, title: str, subtitle: str | None = None, page_number: int | None = None, case_id: str | None = None):
    fig = _new_page()
    _page_header(fig, title, subtitle)
    if case_id:
        _page_footer(fig, f"Case {case_id}", page_number)
    pdf.savefig(fig)
    plt.close(fig)


def _write_ml_table(pdf: PdfPages, title: str, rows: List[Dict], columns: List[str], case_id: str, page_number: int):
    fig, ax = plt.subplots(figsize=(11, 6))
    _draw_page_border(fig)
    ax.axis("off")
    ax.set_title(title, fontsize=14, pad=20)

    table_data = []
    for row in rows:
        table_data.append([row.get(col, "") for col in columns])

    if not table_data:
        ax.text(0.5, 0.5, "No ML anomalies found", ha="center", va="center")
    else:
        table = ax.table(
            cellText=table_data,
            colLabels=columns,
            cellLoc="left",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)

    fig.tight_layout()
    _page_footer(fig, f"Case {case_id}", page_number)
    pdf.savefig(fig)
    plt.close(fig)


def generate_case_report(case):
    """
    Generate a PDF report for the given case.
    Returns (file_path, file_url, report_id, created_at)
    """
    case_id = case.case_id
    summary = mongo_service.get_case_summary(case_id) or {}
    stats = mongo_service.get_case_statistics(case_id) or {}

    ml_anomalies = mongo_service.get_ml_anomalies(case_id, None, 20, 0) or []
    android_anomalies = mongo_service.get_android_ml_anomalies(case_id, None, 20, 0) or []

    counts = _artifact_counts(summary)
    activity_hours = _activity_by_hour(stats)

    reports_dir = Path(settings.MEDIA_ROOT) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now().isoformat()
    report_id = f"REPORT_{case_id}_{created_at.replace(':','').replace('-','').split('.')[0]}"
    file_name = f"{report_id}.pdf"
    file_path = reports_dir / file_name

    with PdfPages(file_path) as pdf:
        page = 1
        _write_title_page(pdf, case, summary, stats, page_number=page)
        page += 1
        _write_narrative(pdf, case, summary, stats, ml_anomalies, android_anomalies, page_number=page)
        page += 1
        _write_section_heading(pdf, "Artifact Visualizations", "Distribution and activity trends", page_number=page, case_id=case_id)
        page += 1
        _write_bar_chart(pdf, counts, case_id, page_number=page)
        page += 1
        _write_activity_line(pdf, activity_hours, case_id, page_number=page)
        page += 1
        _write_pie_chart(pdf, counts, case_id, page_number=page)
        page += 1
        # Extra visuals
        _write_section_heading(pdf, "Behavioral Insights", "Timeline heatmap, browsing, and USB summary", page_number=page, case_id=case_id)
        page += 1
        hours, dates, matrix = _timeline_heatmap(case_id)
        _write_heatmap(pdf, hours, dates, matrix, case_id, page_number=page)
        page += 1
        _write_top_domains(pdf, stats, case_id, page_number=page)
        page += 1
        _write_usb_vendors(pdf, stats, case_id, page_number=page)
        page += 1

        if ml_anomalies:
            _write_section_heading(pdf, "Windows ML Anomalies", "Top high-score records", page_number=page, case_id=case_id)
            page += 1
            ml_rows = []
            for item in ml_anomalies:
                ml_rows.append({
                    "Score": f"{_safe_float(item.get('anomaly_score')):.3f}",
                    "Label": item.get("label", ""),
                    "Activity": item.get("activity_name", ""),
                    "Action": item.get("action_name", ""),
                    "Hour": item.get("hour", ""),
                })
            _write_ml_table(
                pdf,
                "Windows ML High-Score Anomalies",
                ml_rows,
                ["Score", "Label", "Activity", "Action", "Hour"],
                case_id,
                page_number=page,
            )
            page += 1

        if android_anomalies:
            _write_section_heading(pdf, "Android ML Anomalies", "Top high-score records", page_number=page, case_id=case_id)
            page += 1
            android_rows = []
            for item in android_anomalies:
                android_rows.append({
                    "Score": f"{_safe_float(item.get('anomaly_score')):.3f}",
                    "Label": item.get("label", ""),
                    "Name": item.get("name", ""),
                })
            _write_ml_table(
                pdf,
                "Android ML High-Score Anomalies",
                android_rows,
                ["Score", "Label", "Name"],
                case_id,
                page_number=page,
            )

    file_url = f"{settings.MEDIA_URL}reports/{file_name}"
    return str(file_path), file_url, report_id, created_at
