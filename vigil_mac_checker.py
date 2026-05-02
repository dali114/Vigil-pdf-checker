#!/usr/bin/env python3
"""
Vigil Mac Checker - checks bot-blocked sites and PDFs directly from your Mac.
Writes results to ~/Downloads/vigil_mac_results.json for Vigil to read.
"""

import json, re, hashlib, os
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

VIGIL_DATA   = os.path.expanduser("~/Library/Application Support/vigil_mac_snapshots.json")
RESULTS_FILE = os.path.expanduser("~/Downloads/vigil_mac_results.json")

SITES = [
    {
        "url": "https://www.who.int/initiatives/cervical-cancer-elimination-initiative",
        "label": "REF-237367- WHO Cervical Cancer Elimination Initiative 2025",
        "type": "web"
    },
    {
        "url": "https://www.healthychildren.org/English/health-issues/vaccine-preventable-diseases/Pages/Human-Papillomavirus.aspx",
        "label": "REF-239236- AAP How Pediatricians Can Reco HPV Vaccination 2023",
        "type": "web"
    },
    {
        "url": "https://www.cancer.org/cancer/types/cervical-cancer/about/what-is-cervical-cancer.html",
        "label": "REF-284356- ACS Types of HPV 2024",
        "type": "web"
    },
    {
        "url": "https://www.census.gov/topics/population/age-and-sex.html",
        "label": "REF-234192- US Census Bureau Population by Age and Sex 2023",
        "type": "web"
    },
    {
        "url": "https://naspa.us/resource/2024-pharmacist-immunization-authority/",
        "label": "REF-286550- NASPA Pharm and Pharm Tech Vacc Authority 2024",
        "type": "web"
    },
    {
        "url": "https://www.cancer.gov/types/cervical/hp/cervical-prevention-pdq",
        "label": "REF-211991- NCI Cervical Cancer Prevention PDQ HP Version 2025",
        "type": "web"
    },
    {
        "url": "https://health.gov/healthypeople/objectives-and-data/social-determinants-health",
        "label": "REF-196180- Healthy People 2030 Social Determinants 2025",
        "type": "web"
    },
    {
        "url": "https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=00&areatype=country&cancer=047&race=00&sex=2&age=001&stage=999&year=0&type=incd&sortVariableName=rate&sortOrder=default&output=0",
        "label": "REF-158468- NCI State Cancer Profile Pap 3 yr 21-65 Table 2020",
        "type": "web"
    },
    {
        "url": "https://www.cdc.gov/brfss/annual_data/annual_2024.html",
        "label": "REF-166477- BRFSS CDC Surveillance 2024",
        "type": "web"
    },
    {
        "url": "https://www.cdc.gov/hpv/media/pdfs/2024/07/Top10-improving-practice.pdf",
        "label": "REF-96791- CDC Top 10 Tips for HPV Vaccination Success 2018",
        "type": "pdf"
    },
    {
        "url": "https://www.cancer.org/content/dam/cancer-org/online-documents/en/pdf/flyers/acs-elimination-statement-on-hpv-cancers.pdf",
        "label": "REF-99800- ACS Elimination Statement on HPV Cancers 2020",
        "type": "pdf"
    },
    {
        "url": "https://www.hhs.gov/sites/default/files/assessment-of-the-us-childhood-and-adolescent-immunization-schedule-compared-to-other-countries.pdf",
        "label": "REF-291518- HHS Immunization Schedule Assessment 2026",
        "type": "pdf"
    },
    {
        "url": "https://www.acog.org/-/media/project/acog/acogorg/files/pdfs/news/joint-statement_hpv-012121-v1.pdf",
        "label": "REF-237388- ACOG Joint Statement on Elimination of HPV 2025",
        "type": "pdf"
    },
    {
        "url": "https://hpvroundtable.org/wp-content/uploads/2018/06/Cancer-Center-HPVConsensusStatement_FINAL_06.01.2018.pdf",
        "label": "REF-231873- NCI-Designated Centers Endorse Eliminating HPV 2018",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/vaccines/hcp/imz-schedules/downloads/child/0-18yrs-child-combined-schedule.pdf",
        "label": "REF-188100- CDC Child Adolescent Immuniz Schedule US 2025",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/vaccines/hcp/imz-schedules/downloads/adult/adult-combined-schedule.pdf",
        "label": "REF-188101- CDC Adult Immuniz Schedule Ages 19 Or Older 2025",
        "type": "pdf"
    },
    {
        "url": "https://hpvroundtable.org/wp-content/uploads/2023/05/2023-National-Age-9-CTA-Letter-Final.pdf",
        "label": "REF-256864- ACS HPV Vaccination Roundtable Recomm Age 9 2023",
        "type": "pdf"
    },
    {
        "url": "https://www.cancer.org/content/dam/cancer-org/online-documents/en/pdf/flyers/steps-for-increasing-hpv-vaccination-in-practice.pdf",
        "label": "REF-97095- ACS Steps for Increasing HPV Vaccination 2021",
        "type": "pdf"
    },
    {
        "url": "https://hpvroundtable.org/wp-content/uploads/2024/10/Cancer-Prevention-Through-HPV-Vaccination-An-Action-Guide-for-Large-Health-Systems.pdf",
        "label": "REF-252115- ACS Cancer Prevention Through HPV Vaccination 2024",
        "type": "pdf"
    },
    {
        "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2022/srvydesc-508.pdf",
        "label": "REF-227883- NHIS 2022 Survey Description June 2023",
        "type": "pdf"
    },
    {
        "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/srvydesc-508.pdf",
        "label": "REF-291902- NHIS 2024 Survey Description July 2025",
        "type": "pdf"
    },
    {
        "url": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2019/srvydesc-508.pdf",
        "label": "REF-231777- CDC NHIS Survey Description 2019",
        "type": "pdf"
    },
    {
        "url": "https://aphanet.pharmacist.com/sites/default/files/files/Guidelines_for_Pharmacy_Based_IMZ_Advocacy_Approved_Jan_26_2019.pdf",
        "label": "REF-96607- APhA Guidelines Pharmacy-Based Immuniz Advoc 2019",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/brfss/annual_data/2022/pdf/Overview_2022-508.pdf",
        "label": "REF-227692- CDC BRFSS Overview 2022",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/brfss/annual_data/2020/pdf/2020-sdqr-508.pdf",
        "label": "REF-227692- CDC BRFSS Overview 2020 SDQR",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/brfss/annual_data/2020/pdf/codebook20_llcp-v2-508.pdf",
        "label": "REF-285731- CDC LLCP 2020 Codebook Report 2021",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/united-states-cancer-statistics/technical-notes/pdf/uscs-data-visualizations-tool-technical-notes-2022-september-508.pdf",
        "label": "REF-285482- CDC USCS Data Viz Tool Technical Notes 2025",
        "type": "pdf"
    },
    {
        "url": "https://www.immunizationmanagers.org/content/uploads/2022/03/Vaccine-Confidence-Full-Guide.pdf",
        "label": "REF-259218- AIM Promoting Vaccine Confidence 2021",
        "type": "pdf"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def load_snapshots():
    if os.path.exists(VIGIL_DATA):
        with open(VIGIL_DATA, "r") as f:
            return json.load(f)
    return {}

def save_snapshots(snaps):
    os.makedirs(os.path.dirname(VIGIL_DATA), exist_ok=True)
    with open(VIGIL_DATA, "w") as f:
        json.dump(snaps, f, indent=2)

def fetch_url(url, method="GET"):
    try:
        req = Request(url, headers=HEADERS, method=method)
        with urlopen(req, timeout=20) as resp:
            if method == "HEAD":
                return True, resp.status
            return resp.read().decode("utf-8", errors="ignore"), resp.status
    except HTTPError as e:
        return None, e.code
    except URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)

def extract_dates(html):
    dates = []
    if not html or not isinstance(html, str):
        return dates
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL|re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    label_pat = re.compile(
        r"(last\s+(?:updated|modified|reviewed|edited|revised)|published|posted|review\s+date|effective\s+date)"
        r"[\s:\-]+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4}|[A-Za-z]+\.?\s+\d{4}|\d{4}-\d{2}-\d{2})",
        re.I
    )
    for m in label_pat.finditer(text):
        dates.append({"label": m.group(1).strip(), "value": m.group(2).strip(), "source": "text"})
    if not dates:
        bare = re.search(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b", text[:3000], re.I)
        if bare:
            dates.append({"label": "Page date", "value": bare.group(1), "source": "text"})
    return dates

def text_snapshot(html):
    if not html or not isinstance(html, str):
        return ""
    html = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", html, flags=re.DOTALL|re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()[:50000]

def main():
    snaps = load_snapshots()
    results = []
    now = datetime.now(timezone.utc).isoformat()

    for site in SITES:
        url = site["url"]
        label = site["label"]
        site_type = site.get("type", "web")
        print("Checking: " + label[:60] + "...")

        if site_type == "pdf":
            # For PDFs just check if URL is alive
            result, status = fetch_url(url, method="HEAD")
            if result is False or (isinstance(status, int) and status >= 400):
                # Try GET if HEAD fails
                result, status = fetch_url(url, method="GET")
            alive = result is not False and (not isinstance(status, int) or status < 400)
            prev = snaps.get(url, {})
            prev_alive = prev.get("alive", None)
            if prev_alive is True and not alive:
                pdf_status = "changed"
                print("  BROKEN - was reachable before")
            elif alive:
                pdf_status = "ok"
                print("  ok | reachable")
            else:
                pdf_status = "error"
                print("  ERROR: " + str(status))
            snaps[url] = {"alive": alive, "checkedAt": now}
            results.append({"url": url, "label": label, "status": pdf_status,
                           "dates": [], "dateChanges": [], "contentChanged": False,
                           "checkedAt": now, "error": None if alive else str(status)})
            continue

        # Web pages - full content check
        html, status = fetch_url(url)
        if not html or not isinstance(html, str):
            print("  ERROR: " + str(status))
            results.append({"url": url, "label": label, "status": "error",
                           "error": str(status), "checkedAt": now})
            continue

        dates = extract_dates(html)
        snap_hash = hashlib.md5(text_snapshot(html).encode()).hexdigest()
        prev = snaps.get(url, {})
        prev_hash = prev.get("hash", "")
        prev_dates = prev.get("dates", [])
        content_changed = bool(prev_hash and snap_hash != prev_hash)
        date_changes = []
        for d in dates:
            prev_d = next((p for p in prev_dates if p["label"].lower() == d["label"].lower()), None)
            if prev_d and prev_d["value"] != d["value"]:
                date_changes.append({"label": d["label"], "from": prev_d["value"], "to": d["value"]})
        status_str = "changed" if (content_changed or date_changes) else ("ok" if prev_hash else "first_check")
        print("  " + status_str + " | dates: " + str([d["value"] for d in dates]))
        snaps[url] = {"hash": snap_hash, "dates": dates, "checkedAt": now}
        results.append({"url": url, "label": label, "status": status_str, "dates": dates,
                       "dateChanges": date_changes, "contentChanged": content_changed,
                       "checkedAt": now, "error": None})

    save_snapshots(snaps)
    with open(RESULTS_FILE, "w") as f:
        json.dump({"checkedAt": now, "results": results}, f, indent=2)

    changed = [r for r in results if r["status"] == "changed"]
    print("\nDone. " + str(len(results)) + " sites checked, " + str(len(changed)) + " changed.")
    print("Results: " + RESULTS_FILE)

if __name__ == "__main__":
    main()
