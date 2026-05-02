#!/usr/bin/env python3
"""
Vigil Mac Checker - runs on your Mac via launchd
Fetches bot-blocked sites directly (no proxy), compares dates,
writes results to ~/Downloads/vigil_mac_results.json
Vigil reads this file on startup and merges changes.
"""

import json, re, hashlib, os, sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

VIGIL_DATA   = os.path.expanduser('~/Library/Application Support/vigil_mac_snapshots.json')
RESULTS_FILE = os.path.expanduser('~/Downloads/vigil_mac_results.json')

SITES = [
    {"url": "https://www.who.int/initiatives/cervical-cancer-elimination-initiative", "label": "REF-237367- WHO Cervical Cancer Elimination Initiative 2025"},
    {"url": "https://www.healthychildren.org/English/health-issues/vaccine-preventable-diseases/Pages/Human-Papillomavirus.aspx", "label": "REF-239236- AAP How Pediatricians Can Reco HPV Vaccination 2023"},
    {"url": "https://www.cancer.org/cancer/types/cervical-cancer/about/what-is-cervical-cancer.html", "label": "REF-284356- ACS Types of HPV 2024"},
    {"url": "https://www.census.gov/topics/population/age-and-sex.html", "label": "REF-234192- US Census Bureau Population by Age and Sex 2023"},
    {"url": "https://naspa.us/resource/2024-pharmacist-immunization-authority/", "label": "REF-286550- NASPA Pharm and Pharm Tech Vacc Authority 2024"},
    {"url": "https://www.cancer.gov/types/cervical/hp/cervical-prevention-pdq", "label": "REF-211991- NCI Cervical Cancer Prevention PDQ HP Version 2025"},
    {"url": "https://health.gov/healthypeople/objectives-and-data/social-determinants-health", "label": "REF-196180- Healthy People 2030 Social Determinants 2025"},
    {"url": "https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=00&areatype=country&cancer=047&race=00&sex=2&age=001&stage=999&year=0&type=incd&sortVariableName=rate&sortOrder=default&output=0", "label": "REF-158468- NCI State Cancer Profile Pap 3 yr 21-65 Table 2020"},
    {"url": "https://www.cdc.gov/brfss/annual_data/annual_2024.html", "label": "REF-166477- BRFSS CDC Surveillance 2024"},
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def load_snapshots():
    if os.path.exists(VIGIL_DATA):
        with open(VIGIL_DATA, 'r') as f:
            return json.load(f)
    return {}

def save_snapshots(snaps):
    os.makedirs(os.path.dirname(VIGIL_DATA), exist_ok=True)
    with open(VIGIL_DATA, 'w') as f:
        json.dump(snaps, f, indent=2)

def fetch_page(url):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except HTTPError as e:
        return None, "HTTP " + str(e.code)
    except URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)

def extract_dates(html):
    dates = []
    if not html:
        return dates
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL|re.I)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    label_pat = re.compile(
        r'(last\s+(?:updated|modified|reviewed|edited|revised)|published|posted|review\s+date|effective\s+date)'
        r'[\s:\-]+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4}|[A-Za-z]+\.?\s+\d{4}|\d{4}-\d{2}-\d{2})',
        re.I
    )
    for m in label_pat.finditer(text):
        dates.append({'label': m.group(1).strip(), 'value': m.group(2).strip(), 'source': 'text'})
    if not dates:
        bare = re.search(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b', text[:3000], re.I)
        if bare:
            dates.append({'label': 'Page date', 'value': bare.group(1), 'source': 'text'})
    return dates

def text_snapshot(html):
    if not html:
        return ''
    html = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL|re.I)
    text = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', text).strip()[:50000]

def main():
    snaps = load_snapshots()
    results = []
    now = datetime.now(timezone.utc).isoformat()
    for site in SITES:
        url = site['url']
        label = site['label']
        print("Checking: " + label[:60] + "...")
        html = fetch_page(url)
        if not html or isinstance(html, tuple):
            error = html[1] if isinstance(html, tuple) else "No response"
            print("  ERROR: " + error)
            results.append({'url': url, 'label': label, 'status': 'error', 'error': error, 'checkedAt': now})
            continue
        dates = extract_dates(html)
        snap_hash = hashlib.md5(text_snapshot(html).encode()).hexdigest()
        prev = snaps.get(url, {})
        prev_hash = prev.get('hash', '')
        prev_dates = prev.get('dates', [])
        content_changed = bool(prev_hash and snap_hash != prev_hash)
        date_changes = []
        for d in dates:
            prev_d = next((p for p in prev_dates if p['label'].lower() == d['label'].lower()), None)
            if prev_d and prev_d['value'] != d['value']:
                date_changes.append({'label': d['label'], 'from': prev_d['value'], 'to': d['value']})
        status = 'changed' if (content_changed or date_changes) else ('ok' if prev_hash else 'first_check')
        print("  " + status + " | dates: " + str([d['value'] for d in dates]))
        snaps[url] = {'hash': snap_hash, 'dates': dates, 'checkedAt': now}
        results.append({'url': url, 'label': label, 'status': status, 'dates': dates, 'dateChanges': date_changes, 'contentChanged': content_changed, 'checkedAt': now, 'error': None})
    save_snapshots(snaps)
    with open(RESULTS_FILE, 'w') as f:
        json.dump({'checkedAt': now, 'results': results}, f, indent=2)
    changed = [r for r in results if r['status'] == 'changed']
    print("Done. " + str(len(results)) + " sites checked, " + str(len(changed)) + " changed.")
    print("Results written to: " + RESULTS_FILE)

if __name__ == '__main__':
    main()
