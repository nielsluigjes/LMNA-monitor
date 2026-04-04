#!/usr/bin/env python3
"""
LMNA Cardiac Disease Monitor: Scraper
Fetches: PubMed, ClinicalTrials.gov (wereldwijd + NL/DE/BE-locaties), RSS feeds
(PubMed-zoekalerts, ClinicalTrials.gov RSS, tijdschrift- en OA-feeds; geen nieuwsaggregaat).
Slaat geen PubMed-abstracts of RSS-samenvattingen op (alleen metadata + links).
Run manually or via cron: 0 7 * * * python3 scraper.py  (dagelijks 07:00, lokaal)
"""

import sqlite3
import requests
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import feedparser  # pip install feedparser

DB_PATH = Path(__file__).parent / "lmna.db"


# ── Search terms ────────────────────────────────────────────────────────────
PUBMED_QUERY = (
    '(LMNA[tiab] OR lamin A[tiab] OR laminopathy[tiab] OR laminopathies[tiab]) '
    'AND ("dilated cardiomyopathy"[tiab] OR "dilaterende cardiomyopathie"[tiab] '
    'OR "AV block"[tiab] OR "atrioventricular block"[tiab] OR "heart block"[tiab] '
    'OR bradycardia[tiab] OR bradyarrhythmia[tiab] OR "conduction disease"[tiab] '
    'OR "conduction system"[tiab] OR "DCM"[tiab]) '
    'AND ("last 2 years"[edat])'
)

CLINICALTRIALS_QUERY = "LMNA dilated cardiomyopathy AV block"

# ClinicalTrials.gov: studies met minstens één site in NL, DE of BE (naast wereldwijde zoekterm)
EU_BENELUX_DACH_LOCATIONS = (
    "(AREA[LocationCountry]Netherlands OR AREA[LocationCountry]Germany OR "
    "AREA[LocationCountry]Belgium)"
)

# Officiële / uitgever-RSS. URL’s periodiek valideren bij wijzigingen bij bronnen.
NEWS_RSS_FEEDS = [
    # NCBI PubMed — zoek-alerts
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=LMNA+dilated+cardiomyopathy+AV+block&format=rss",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=laminopathy+cardiomyopathy+LMNA&format=rss",
    # ClinicalTrials.gov — RSS API (o.a. studies met term in laatste posting-venster; kan leeg zijn)
    "https://clinicaltrials.gov/api/rss?term=LMNA",
    "https://clinicaltrials.gov/api/rss?term=LMNA+cardiomyopathy",
    # Circulation (AHA) — table of contents RSS
    "https://www.ahajournals.org/action/showFeed?type=etoc&feed=rss&jc=circ",
    # Open access — cardiovasculaire wetenschap (alternatief voor BMC waar Springer-RSS auth vereist)
    "https://www.frontiersin.org/journals/cardiovascular-medicine/rss",
]

RSS_USER_AGENT = (
    "LMNA-Monitor/1.0 (+https://github.com/nielsluigjes/LMNA-monitor; "
    "contact: lmna.monitor@gmail.com)"
)
RSS_FETCH_TIMEOUT = 30
RSS_DELAY_BETWEEN_FEEDS_SEC = 0.35

# ── DB setup ─────────────────────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS publications (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            authors     TEXT,
            journal     TEXT,
            pub_date    TEXT,
            abstract    TEXT,
            url         TEXT,
            fetched_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS trials (
            nct_id      TEXT PRIMARY KEY,
            title       TEXT,
            status      TEXT,
            phase       TEXT,
            conditions  TEXT,
            interventions TEXT,
            start_date  TEXT,
            primary_end TEXT,
            locations   TEXT,
            url         TEXT,
            fetched_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS news (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            source      TEXT,
            pub_date    TEXT,
            url         TEXT,
            summary     TEXT,
            fetched_at  TEXT
        );
    """)
    con.commit()
    return con

# ── PubMed ───────────────────────────────────────────────────────────────────
def fetch_pubmed(con, max_results=50):
    print("📚 Fetching PubMed...")
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Search
    r = requests.get(f"{base}/esearch.fcgi", params={
        "db": "pubmed", "term": PUBMED_QUERY,
        "retmax": max_results, "retmode": "json", "sort": "date"
    }, timeout=30)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        print("  No results.")
        return

    # Fetch details
    r2 = requests.get(f"{base}/efetch.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "xml"
    }, timeout=30)
    r2.raise_for_status()

    root = ET.fromstring(r2.text)
    cur = con.cursor()
    new = 0
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", "")
        title = article.findtext(".//ArticleTitle", "")
        journal = article.findtext(".//Journal/Title", "")
        
        # Authors
        authors = []
        for a in article.findall(".//Author")[:5]:
            ln = a.findtext("LastName", "")
            fn = a.findtext("ForeName", "")
            if ln:
                authors.append(f"{ln} {fn}".strip())
        authors_str = ", ".join(authors) + (" et al." if len(authors) == 5 else "")

        # Date
        pub = article.find(".//PubDate")
        year  = pub.findtext("Year", "") if pub else ""
        month = pub.findtext("Month", "") if pub else ""
        pub_date = f"{year}-{month}" if month else year

        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        try:
            cur.execute("""
                INSERT OR IGNORE INTO publications
                (id, title, authors, journal, pub_date, abstract, url, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pmid, title, authors_str, journal, pub_date, "", url,
                  datetime.now().isoformat()))
            if cur.rowcount:
                new += 1
        except Exception as e:
            print(f"  DB error: {e}")

    con.commit()
    print(f"  ✓ {new} new publications added (of {len(ids)} found)")
    time.sleep(0.4)  # NCBI rate limit

# ── ClinicalTrials ────────────────────────────────────────────────────────────
def _upsert_trial_from_study(cur, study):
    """Parse one CT.gov v2 study object; returns True if a row was written."""
    ps = study.get("protocolSection", {})
    id_mod   = ps.get("identificationModule", {})
    stat_mod = ps.get("statusModule", {})
    arms_mod = ps.get("armsInterventionsModule", {})
    cond_mod = ps.get("conditionsModule", {})
    locs_mod = ps.get("contactsLocationsModule", {})

    nct_id     = id_mod.get("nctId", "")
    if not nct_id:
        return False
    title      = id_mod.get("briefTitle", "")
    status     = stat_mod.get("overallStatus", "")
    phase      = ", ".join(ps.get("designModule", {}).get("phases", []))
    conditions = ", ".join(cond_mod.get("conditions", []))
    interventions = ", ".join(
        i.get("interventionName", "") for i in arms_mod.get("interventions", [])[:5]
    )
    start_date = stat_mod.get("startDateStruct", {}).get("date", "")
    primary_end = stat_mod.get("primaryCompletionDateStruct", {}).get("date", "")
    locs = locs_mod.get("locations") or []
    locations  = ", ".join(sorted({
        l.get("locationCountry", "") for l in locs if l.get("locationCountry")
    }))
    trial_url  = f"https://clinicaltrials.gov/study/{nct_id}"

    cur.execute("""
        INSERT OR REPLACE INTO trials
        (nct_id, title, status, phase, conditions, interventions,
         start_date, primary_end, locations, url, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nct_id, title, status, phase, conditions, interventions,
          start_date, primary_end, locations, trial_url,
          datetime.now().isoformat()))
    return cur.rowcount > 0


def fetch_trials(con):
    print("🔬 Fetching ClinicalTrials.gov...")
    url = "https://clinicaltrials.gov/api/v2/studies"
    base = {
        "query.cond": "LMNA cardiomyopathy",
        "pageSize": 100,
        "format": "json",
        "fields": (
            "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,"
            "StartDate,PrimaryCompletionDate,LocationCountry"
        ),
    }
    # Twee passes: wereldwijd, en expliciet met site in NL / DE / BE (EU-prioriteit)
    passes = [
        ("wereldwijd", {**base, "query.term": "LMNA laminopathy cardiac"}),
        (
            "locaties NL · DE · BE",
            {
                **base,
                "query.term": f"LMNA laminopathy cardiac {EU_BENELUX_DACH_LOCATIONS}",
            },
        ),
    ]

    cur = con.cursor()
    seen_nct = set()
    upserted = 0
    for label, params in passes:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        studies = data.get("studies", [])
        new_in_pass = 0
        for study in studies:
            nct = (study.get("protocolSection") or {}).get("identificationModule", {}).get("nctId")
            if nct and nct in seen_nct:
                continue
            if _upsert_trial_from_study(cur, study):
                upserted += 1
            if nct:
                seen_nct.add(nct)
            new_in_pass += 1
        dup = len(studies) - new_in_pass
        extra = f", {dup} overlap met eerdere pass" if dup else ""
        print(f"  · {label}: {len(studies)} uit API ({new_in_pass} nieuw{extra})")

    con.commit()
    print(f"  ✓ {upserted} trials upserted ({len(seen_nct)} unieke NCT-id’s)")

# ── News (RSS) ────────────────────────────────────────────────────────────────
def fetch_news(con):
    print("📰 Fetching news via RSS (officiële feeds)...")
    cur = con.cursor()
    # Verwijder oude rijen van eerdere Google News RSS (blijven anders in de DB staan)
    cur.execute("DELETE FROM news WHERE url LIKE '%news.google.com%'")
    removed = cur.rowcount
    if removed:
        print(f"  🧹 {removed} oude nieuwsregel(s) verwijderd (vroegere feed-bron)")
    new = 0
    headers = {"User-Agent": RSS_USER_AGENT}
    for feed_url in NEWS_RSS_FEEDS:
        try:
            r = requests.get(
                feed_url,
                headers=headers,
                timeout=RSS_FETCH_TIMEOUT,
            )
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                url = entry.get("link", "")
                if not url:
                    continue
                source = feed.feed.get("title", feed_url)
                pub_date = entry.get("published", "") or entry.get("updated", "")
                uid = hashlib.md5(url.encode()).hexdigest()

                cur.execute("""
                    INSERT OR IGNORE INTO news
                    (id, title, source, pub_date, url, summary, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uid, title, source, pub_date, url, "",
                      datetime.now().isoformat()))
                if cur.rowcount:
                    new += 1
        except Exception as e:
            print(f"  Feed error ({feed_url[:56]}...): {e}")
        time.sleep(RSS_DELAY_BETWEEN_FEEDS_SEC)

    con.commit()
    print(f"  ✓ {new} new news items added")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🧬 LMNA Monitor: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    con = init_db()
    fetch_pubmed(con)
    fetch_trials(con)
    fetch_news(con)
    con.close()
    print("\n✅ Done. Open dashboard.html to view results.\n")
