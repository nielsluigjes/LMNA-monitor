#!/usr/bin/env python3
"""
LMNA Cardiac Disease Monitor — Scraper
Fetches: PubMed, ClinicalTrials.gov, NewsAPI / RSS feeds
Run manually or via cron: 0 8 * * 1 python3 scraper.py
"""

import sqlite3
import requests
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import feedparser  # pip install feedparser

DB_PATH = Path(__file__).parent / "lmna.db"

# ── Search terms ────────────────────────────────────────────────────────────
PUBMED_QUERY = (
    '(LMNA[tiab] OR lamin A[tiab] OR laminopathy[tiab] OR laminopathies[tiab]) '
    'AND (cardiomyopathy[tiab] OR arrhythmia[tiab] OR cardiac[tiab] OR heart[tiab] '
    'OR "dilated cardiomyopathy"[tiab] OR "heart failure"[tiab]) '
    'AND ("last 1 year"[edat])'
)

CLINICALTRIALS_QUERY = "LMNA cardiomyopathy"

NEWS_RSS_FEEDS = [
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=LMNA+cardiac&format=rss",
    "https://www.cardiologytoday.com/rss",
    "https://www.heart.org/rss",
    # Google News (no key needed)
    "https://news.google.com/rss/search?q=LMNA+cardiomyopathy&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=laminopathy+cardiac&hl=en-US&gl=US&ceid=US:en",
]

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
        abstract = " ".join(t.text or "" for t in article.findall(".//AbstractText"))
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
            """, (pmid, title, authors_str, journal, pub_date, abstract[:2000], url,
                  datetime.now().isoformat()))
            if cur.rowcount:
                new += 1
        except Exception as e:
            print(f"  DB error: {e}")

    con.commit()
    print(f"  ✓ {new} new publications added (of {len(ids)} found)")
    time.sleep(0.4)  # NCBI rate limit

# ── ClinicalTrials ────────────────────────────────────────────────────────────
def fetch_trials(con):
    print("🔬 Fetching ClinicalTrials.gov...")
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": "LMNA cardiomyopathy",
        "query.term": "LMNA laminopathy cardiac",
        "pageSize": 100,
        "format": "json",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,StartDate,PrimaryCompletionDate,LocationCountry"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    cur = con.cursor()
    new = 0
    for study in data.get("studies", []):
        ps = study.get("protocolSection", {})
        id_mod   = ps.get("identificationModule", {})
        stat_mod = ps.get("statusModule", {})
        desc_mod = ps.get("descriptionModule", {})
        arms_mod = ps.get("armsInterventionsModule", {})
        cond_mod = ps.get("conditionsModule", {})
        locs_mod = ps.get("contactsLocationsModule", {})

        nct_id     = id_mod.get("nctId", "")
        title      = id_mod.get("briefTitle", "")
        status     = stat_mod.get("overallStatus", "")
        phase      = ", ".join(ps.get("designModule", {}).get("phases", []))
        conditions = ", ".join(cond_mod.get("conditions", []))
        interventions = ", ".join(
            i.get("interventionName", "") for i in arms_mod.get("interventions", [])[:5]
        )
        start_date = stat_mod.get("startDateStruct", {}).get("date", "")
        primary_end = stat_mod.get("primaryCompletionDateStruct", {}).get("date", "")
        locations  = ", ".join(set(
            l.get("locationCountry", "") for l in locs_mod.get("locations", [])[:10]
        ))
        trial_url  = f"https://clinicaltrials.gov/study/{nct_id}"

        cur.execute("""
            INSERT OR REPLACE INTO trials
            (nct_id, title, status, phase, conditions, interventions,
             start_date, primary_end, locations, url, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nct_id, title, status, phase, conditions, interventions,
              start_date, primary_end, locations, trial_url,
              datetime.now().isoformat()))
        if cur.rowcount:
            new += 1

    con.commit()
    print(f"  ✓ {new} trials upserted")

# ── News (RSS) ────────────────────────────────────────────────────────────────
def fetch_news(con):
    print("📰 Fetching news via RSS...")
    cur = con.cursor()
    new = 0
    for feed_url in NEWS_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title   = entry.get("title", "")
                url     = entry.get("link", "")
                summary = entry.get("summary", "")[:1000]
                source  = feed.feed.get("title", feed_url)
                pub_date = entry.get("published", "")
                uid = hashlib.md5(url.encode()).hexdigest()

                cur.execute("""
                    INSERT OR IGNORE INTO news
                    (id, title, source, pub_date, url, summary, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uid, title, source, pub_date, url, summary,
                      datetime.now().isoformat()))
                if cur.rowcount:
                    new += 1
        except Exception as e:
            print(f"  Feed error ({feed_url[:50]}...): {e}")

    con.commit()
    print(f"  ✓ {new} new news items added")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🧬 LMNA Monitor — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    con = init_db()
    fetch_pubmed(con)
    fetch_trials(con)
    fetch_news(con)
    con.close()
    print("\n✅ Done. Open dashboard.html to view results.\n")
