#!/usr/bin/env python3
"""
Vigil PDF Checker
Runs daily via GitHub Actions.
Checks each PDF URL for availability and size changes.
Sends an email alert if anything is broken or changed.
"""

import json
import os
import hashlib
import requests
from datetime import datetime
from pathlib import Path

PDFS = [
    {"label": "REF-96791- CDC Top 10 Tips for HPV Vaccination Success 2018",
     "url": "https://www.cdc.gov/hpv/media/pdfs/2024/07/Top10-improving-practice.pdf"},
    {"label": "REF-99800- ACS Elimination Statement on HPV Cancers 2020",
     "url": "https://www.cancer.org/content/dam/cancer-org/online-documents/en/pdf/flyers/acs-elimination-statement-on-hpv-cancers.pdf"},
    {"label": "REF-291518- HHS Immunization Schedule Assessment 2026",
     "url": "https://www.hhs.gov/sites/default/files/assessment-of-the-us-childhood-and-adolescent-immunization-schedule-compared-to-other-countries.pdf"},
    {"label": "REF-237388- ACOG Joint Statement on Elimination of HPV 2025",
     "url": "https://www.acog.org/-/media/project/acog/acogorg/files/pdfs/news/joint-statement_hpv-012121-v1.pdf"},
    {"label": "REF-231873- NCI-Designated Centers Endorse Eliminating HPV 2018",
     "url": "https://hpvroundtable.org/wp-content/uploads/2018/06/Cancer-Center-HPVConsensusStatement_FINAL_06.01.2018.pdf"},
    {"label": "REF-188100- CDC Child Adolescent Immuniz Schedule US 2025",
     "url": "https://www.cdc.gov/vaccines/hcp/imz-schedules/downloads/child/0-18yrs-child-combined-schedule.pdf"},
    {"label": "REF-188101- CDC Adult Immuniz Schedule Ages 19 Or Older 2025",
     "url": "https://www.cdc.gov/vaccines/hcp/imz-schedules/downloads/adult/adult-combined-schedule.pdf"},
    {"label": "REF-256864- ACS HPV Vaccination Roundtable Recomm Age 9 2023",
     "url": "https://hpvroundtable.org/wp-content/uploads/2023/05/2023-National-Age-9-CTA-Letter-Final.pdf"},
    {"label": "REF-97095- ACS Steps for Increasing HPV Vaccination 2021",
     "url": "https://www.cancer.org/content/dam/cancer-org/online-documents/en/pdf/flyers/steps-for-increasing-hpv-vaccination-in-practice.pdf"},
    {"label": "REF-252115- ACS Cancer Prevention Through HPV Vaccination 2024",
     "url": "https://hpvroundtable.org/wp-content/uploads/2024/10/Cancer-Prevention-Through-HPV-Vaccination-An-Action-Guide-for-Large-Health-Systems.pdf"},
    {"label": "REF-227883- NHIS 2022 Survey Description June 2023",
     "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2022/srvydesc-508.pdf"},
    {"label": "REF-291902- NHIS 2024 Survey Description July 2025",
     "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/srvydesc-508.pdf"},
    {"label": "REF-231777- CDC NHIS Survey Description 2019",
     "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2019/srvydesc-508.pdf"},
    {"label": "REF-96607- APhA Guidelines Pharmacy-Based Immuniz Advoc 2019",
     "url": "https://aphanet.pharmacist.com/sites/default/files/files/Guidelines_for_Pharmacy_Based_IMZ_Advocacy_Approved_Jan_26_2019.pdf"},
    {"label": "REF-227692- CDC BRFSS Overview 2022",
     "url": "https://www.cdc.gov/brfss/annual_data/2022/pdf/Overview_2022-508.pdf"},
    {"label": "REF-227692- CDC BRFSS Overview 2020 SDQR",
     "url": "https://www.cdc.gov/brfss/annual_data/2020/pdf/2020-sdqr-508.pdf"},
    {"label": "REF-285731- CDC LLCP 2020 Codebook Report 2021",
     "url": "https://www.cdc.gov/brfss/annual_data/2020/pdf/codebook20_llcp-v2-508.pdf"},
    {"label": "REF-285482- CDC USCS Data Viz Tool Technical Notes 2025",
     "url": "https://www.cdc.gov/united-states-cancer-statistics/technical-notes/pdf/uscs-data-visualizations-tool-technical-notes-2022-september-508.pdf"},
    {"label": "REF-259218- AIM Promoting Vaccine Confidence 2021",
     "url": "https://www.immunizationmanagers.org/content/uploads/2022/03/Vaccine-Confidence-Full-Guide.pdf"},
]

SNAPSHOT_FILE = Path("pdf_snapshots.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def load_snapshots():
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text())
    return {}


def save_snapshots(data):
    SNAPSHOT_FILE.write_text(json.dumps(data, indent=2))


def check_pdf(url):
    """Returns (status, size_bytes, content_hash, last_modified) or raises."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if r.status_code == 200:
            size = int(r.headers.get("content-length", 0))
            etag = r.headers.get("etag", "")
            last_mod = r.headers.get("last-modified", "")
            return r.status_code, size, etag, last_mod
        elif r.status_code in (405, 403):
            pass
        else:
            return r.status_code, 0, "", ""
    except Exception:
        pass

    r = requests.get(url, headers=HEADERS, timeout=60, stream=True, allow_redirects=True)
    if r.status_code != 200:
        return r.status_code, 0, "", ""

    chunk = b""
    for block in r.iter_content(65536):
        chunk += block
        if len(chunk) >= 65536:
            break
    r.close()

    content_hash = hashlib.md5(chunk).hexdigest()
    size = int(r.headers.get("content-length", len(chunk)))
    etag = r.headers.get("etag", "")
    last_mod = r.headers.get("last-modified", "")
    return r.status_code, size, etag or content_hash, last_mod


def send_email(subject, body):
    """Send email via Gmail SMTP using GitHub Actions secrets."""
    import smtplib
    from email.mime.text import MIMEText

    sender = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("NOTIFY_EMAIL", sender)

    if not sender or not password:
        print("Email not configured — printing report instead:")
        print(body)
        return

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print(f"Email sent to {recipient}")


def main():
    today = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    snapshots = load_snapshots()

    broken = []
    changed = []
    ok = []
    errors = []

    print(f"\n{'=' * 60}")
    print(f"Vigil PDF Checker — {today}")
    print(f"{'=' * 60}\n")

    for pdf in PDFS:
        label = pdf["label"]
        url = pdf["url"]
        prev = snapshots.get(url, {})

        print(f"Checking: {label[:60]}...")
        try:
            status, size, etag, last_mod = check_pdf(url)

            if status != 200:
                broken.append({"label": label, "url": url, "reason": f"HTTP {status}"})
                print(f"  BROKEN — HTTP {status}")
                snapshots[url] = {**prev, "last_status": status, "checked": today}
                continue

            prev_size = prev.get("size", 0)
            prev_etag = prev.get("etag", "")
            prev_mod = prev.get("last_modified", "")

            size_changed = prev_size and abs(size - prev_size) > 1024
            etag_changed = prev_etag and etag and etag != prev_etag
            mod_changed = prev_mod and last_mod and last_mod != prev_mod

            if size_changed or etag_changed or mod_changed:
                reasons = []
                if size_changed:
                    reasons.append(f"size {prev_size:,} -> {size:,} bytes")
                if etag_changed:
                    reasons.append("ETag changed")
                if mod_changed:
                    reasons.append(f"last-modified: {prev_mod} -> {last_mod}")
                changed.append({"label": label, "url": url, "reasons": ", ".join(reasons)})
                print(f"  CHANGED — {', '.join(reasons)}")
            elif not prev:
                print(f"  First check — snapshot saved (size: {size:,} bytes)")
            else:
                ok.append(label)
                print(f"  OK (size: {size:,} bytes)")

            snapshots[url] = {
                "label": label,
                "size": size,
                "etag": etag,
                "last_modified": last_mod,
                "last_status": status,
                "checked": today,
            }

        except Exception as e:
            errors.append({"label": label, "url": url, "error": str(e)})
            print(f"  ERROR — {e}")

    save_snapshots(snapshots)

    needs_alert = broken or changed or errors

    print(f"\n{'=' * 60}")
    print(f"Summary: {len(ok)} OK | {len(changed)} changed | {len(broken)} broken | {len(errors)} errors")
    print(f"{'=' * 60}\n")

    if not needs_alert:
        print("All PDFs OK — no alert needed.")
        return

    lines = [
        f"Vigil PDF Check Report — {today}",
        "=" * 50,
        "",
    ]

    if broken:
        lines.append(f"BROKEN LINKS ({len(broken)})")
        lines.append("These PDFs returned an error — the link may be dead or moved:")
        for b in broken:
            lines.append("")
            lines.append(f"  - {b['label']}")
            lines.append(f"    {b['url']}")
            lines.append(f"    Reason: {b['reason']}")
        lines.append("")

    if changed:
        lines.append(f"CHANGED ({len(changed)})")
        lines.append("These PDFs appear to have been updated:")
        for c in changed:
            lines.append("")
            lines.append(f"  - {c['label']}")
            lines.append(f"    {c['url']}")
            lines.append(f"    What changed: {c['reasons']}")
        lines.append("")

    if errors:
        lines.append(f"CHECK ERRORS ({len(errors)})")
        lines.append("These couldn't be reached (may be temporary):")
        for e in errors:
            lines.append("")
            lines.append(f"  - {e['label']}")
            lines.append(f"    {e['url']}")
            lines.append(f"    Error: {e['error']}")
        lines.append("")

    lines.append(f"{len(ok)} PDFs checked OK with no changes.")
    lines.append("")
    lines.append("— Vigil PDF Checker")

    body = "\n".join(lines)
    subject = f"Vigil: {len(broken)} broken, {len(changed)} changed PDFs — {today[:10]}"

    send_email(subject, body)
    print(body)


if __name__ == "__main__":
    main()
