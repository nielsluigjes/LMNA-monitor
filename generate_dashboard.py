#!/usr/bin/env python3
"""
LMNA Monitor — Dashboard Generator
Reads lmna.db and produces a self-contained dashboard.html
Run after scraper.py: python3 generate_dashboard.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

from insight_engine import enrich_all

DB_PATH   = Path(__file__).parent / "lmna.db"
OUT_PATH  = Path(__file__).parent / "dashboard.html"

def load_data():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    pubs = con.execute("""
        SELECT * FROM publications ORDER BY pub_date DESC LIMIT 100
    """).fetchall()

    trials = con.execute("""
        SELECT * FROM trials ORDER BY
            CASE status
                WHEN 'RECRUITING' THEN 1
                WHEN 'NOT_YET_RECRUITING' THEN 2
                WHEN 'ACTIVE_NOT_RECRUITING' THEN 3
                ELSE 4
            END, start_date DESC
    """).fetchall()

    news = con.execute("""
        SELECT * FROM news ORDER BY fetched_at DESC LIMIT 100
    """).fetchall()

    stats = {
        "total_pubs": con.execute("SELECT COUNT(*) FROM publications").fetchone()[0],
        "total_trials": con.execute("SELECT COUNT(*) FROM trials").fetchone()[0],
        "recruiting": con.execute("SELECT COUNT(*) FROM trials WHERE status='RECRUITING'").fetchone()[0],
        "total_news": con.execute("SELECT COUNT(*) FROM news").fetchone()[0],
        "last_updated": datetime.now().strftime("%d-%m-%Y %H:%M"),
    }
    con.close()
    return (
        [dict(r) for r in pubs],
        [dict(r) for r in trials],
        [dict(r) for r in news],
        stats
    )

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LMNA — onderzoek &amp; nieuws</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,300&family=Lexend:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0d0f0e;
    --surface: #141817;
    --surface2: #1c201e;
    --border: #2a2e2b;
    --accent: #b8f5a0;
    --accent2: #5bc4f5;
    --accent3: #f5c45b;
    --danger: #f55b5b;
    --text: #e8ede9;
    --muted: #6b756c;
    --recruiting: #b8f5a0;
    --completed: #6b756c;
    --active: #5bc4f5;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Lexend', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.65;
    min-height: 100vh;
  }

  /* HEADER */
  header {
    padding: 48px 48px 32px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 24px;
    flex-wrap: wrap;
  }
  .logo-block h1 {
    font-family: 'Fraunces', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.02em;
    line-height: 1;
  }
  .logo-block p {
    color: var(--muted);
    margin-top: 8px;
    font-size: 13px;
    font-family: 'Lexend', sans-serif;
    font-weight: 300;
    letter-spacing: 0.02em;
    text-transform: none;
    line-height: 1.5;
    max-width: 36rem;
  }
  .last-updated {
    color: var(--muted);
    font-size: 12px;
    text-align: right;
    font-family: 'DM Mono', monospace;
  }
  .last-updated span {
    display: block;
    color: var(--accent);
    font-size: 13px;
    margin-top: 2px;
  }

  /* INTRO */
  .intro {
    padding: 28px 48px 32px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(180deg, rgba(20,24,23,0.6) 0%, transparent 100%);
  }
  .intro h2 {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 12px;
  }
  .intro p {
    color: #c5ccc6;
    max-width: 52rem;
    margin-bottom: 12px;
    font-size: 14px;
  }
  .intro-disclaimer {
    font-size: 13px;
    color: var(--muted);
    border-left: 3px solid var(--accent3);
    padding-left: 14px;
    margin: 18px 0 0;
    max-width: 52rem;
  }
  .intro-tips {
    margin-top: 20px;
    display: grid;
    gap: 10px;
    max-width: 52rem;
  }
  .intro-tip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    color: #c5ccc6;
  }
  .intro-tip strong {
    color: var(--accent2);
    font-weight: 500;
  }

  /* STATS BAR */
  .stats-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-bottom: 1px solid var(--border);
  }
  .stat {
    padding: 28px 40px;
    border-right: 1px solid var(--border);
  }
  .stat:last-child { border-right: none; }
  .stat-num {
    font-family: 'Fraunces', serif;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text);
  }
  .stat-num.green { color: var(--accent); }
  .stat-label {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 6px;
    font-family: 'DM Mono', monospace;
  }

  .stats-footnote {
    padding: 12px 48px 16px;
    color: var(--muted);
    font-size: 12px;
    border-bottom: 1px solid var(--border);
    max-width: 52rem;
    line-height: 1.55;
  }

  /* NAV TABS */
  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    padding: 0 48px;
    gap: 0;
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 100;
  }
  .tab {
    padding: 16px 24px;
    cursor: pointer;
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    background: none;
    border-top: none;
    border-left: none;
    border-right: none;
    font-family: 'DM Mono', monospace;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }

  /* MAIN CONTENT */
  main { padding: 40px 48px; }
  .panel { display: none; }
  .panel.active { display: block; }

  /* SEARCH */
  .search-bar {
    margin-bottom: 28px;
    position: relative;
  }
  .search-bar input {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 12px 16px;
    color: var(--text);
    font-family: 'Lexend', sans-serif;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-bar input:focus { border-color: var(--accent); }
  .search-bar input::placeholder { color: var(--muted); }

  /* CARDS */
  .card-grid { display: flex; flex-direction: column; gap: 2px; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 20px 24px;
    transition: border-color 0.15s;
  }
  .card:hover { border-color: var(--accent); }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 8px;
  }
  .card-title {
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    font-weight: 300;
    color: var(--text);
    line-height: 1.4;
    flex: 1;
  }
  .card-title a { color: inherit; text-decoration: none; }
  .card-title a:hover { color: var(--accent); }
  .card-date {
    color: var(--muted);
    font-size: 11px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .card-meta {
    color: var(--muted);
    font-size: 12px;
    font-family: 'DM Mono', monospace;
    margin-bottom: 10px;
  }
  .card-meta strong { color: var(--accent2); }
  .abstract {
    color: #9aa39b;
    font-size: 13px;
    font-family: 'Lexend', sans-serif;
    line-height: 1.75;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }
  .abstract.open { max-height: 400px; }
  .toggle-abstract {
    color: var(--muted);
    font-size: 10px;
    cursor: pointer;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 8px;
    display: inline-block;
  }
  .toggle-abstract:hover { color: var(--accent); }

  /* BADGES */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 500;
    flex-shrink: 0;
  }
  .badge-recruiting { background: rgba(184,245,160,0.15); color: var(--recruiting); border: 1px solid rgba(184,245,160,0.3); }
  .badge-active { background: rgba(91,196,245,0.15); color: var(--active); border: 1px solid rgba(91,196,245,0.3); }
  .badge-completed { background: rgba(107,117,108,0.15); color: var(--completed); border: 1px solid rgba(107,117,108,0.3); }
  .badge-other { background: rgba(245,196,91,0.15); color: var(--accent3); border: 1px solid rgba(245,196,91,0.3); }

  /* TRIAL CARDS */
  .trial-grid { display: flex; flex-direction: column; gap: 2px; }
  .trial-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 20px 24px;
    transition: border-color 0.15s;
  }
  .trial-card:hover { border-color: var(--accent2); }
  .trial-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 10px; }
  .trial-title {
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    font-weight: 300;
    line-height: 1.4;
  }
  .trial-title a { color: inherit; text-decoration: none; }
  .trial-title a:hover { color: var(--accent2); }
  .trial-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 12px; font-family: 'DM Mono', monospace; color: var(--muted); }
  .trial-meta span strong { color: var(--text); }

  /* EMPTY */
  .empty {
    text-align: center;
    padding: 80px 20px;
    color: var(--muted);
  }
  .empty-icon { font-size: 3rem; margin-bottom: 16px; }

  /* FILTER ROW */
  .filter-row {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .filter-btn {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 6px 14px;
    border-radius: 2px;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
  }
  .filter-btn:hover, .filter-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(184,245,160,0.08);
  }

  /* RESULT COUNT */
  .result-count { color: var(--muted); font-size: 12px; margin-bottom: 16px; }

  /* QUICK SEARCH CHIPS */
  .chip-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
  }
  .chip-label {
    font-size: 11px;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.06em;
    margin-right: 4px;
  }
  .chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 6px 12px;
    border-radius: 999px;
    font-family: 'Lexend', sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }
  .chip:hover {
    border-color: var(--accent);
    background: rgba(184,245,160,0.08);
  }

  .panel-hint {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 16px;
    max-width: 48rem;
    line-height: 1.55;
  }

  /* INSIGHTS — lokale heuristiek, geen API */
  .insights {
    padding: 28px 48px 32px;
    border-bottom: 1px solid var(--border);
    background: rgba(20, 24, 23, 0.35);
    max-width: 100%;
  }
  .insights h2 {
    font-family: 'Fraunces', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--accent3);
    margin-bottom: 12px;
  }
  .insights-method {
    font-size: 12px;
    color: var(--muted);
    max-width: 52rem;
    line-height: 1.55;
    margin-bottom: 16px;
    font-style: italic;
  }
  .insight-para {
    color: #c5ccc6;
    font-size: 14px;
    max-width: 52rem;
    line-height: 1.65;
    margin-bottom: 12px;
  }
  .theme-cluster {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
    max-width: 52rem;
  }
  .theme-cluster h3 {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--accent2);
    margin-bottom: 8px;
  }
  .theme-cluster .count {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .theme-cluster ul {
    margin: 0;
    padding-left: 1.15rem;
    color: #9aa39b;
    font-size: 13px;
    line-height: 1.6;
  }
  .highlight-list {
    max-width: 52rem;
    margin-top: 16px;
    padding: 14px 18px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  .highlight-list strong {
    color: var(--accent);
    font-weight: 500;
    display: block;
    margin-bottom: 8px;
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
  }
  .highlight-list ol {
    margin: 0;
    padding-left: 1.2rem;
    color: #c5ccc6;
    font-size: 13px;
    line-height: 1.65;
  }

  .sort-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }
  .rel-chip {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--accent3);
    border: 1px solid rgba(245,196,91,0.35);
    padding: 2px 8px;
    border-radius: 2px;
    margin-right: 6px;
    vertical-align: middle;
  }
  .theme-chip {
    display: inline-block;
    font-size: 10px;
    color: var(--accent2);
    border: 1px solid rgba(91,196,245,0.35);
    padding: 2px 8px;
    border-radius: 999px;
    margin-right: 4px;
    margin-top: 4px;
    vertical-align: middle;
  }
  .card-badges { margin-bottom: 8px; }

  /* Insights + tabs/inhoud: twee kolommen op brede schermen */
  .dashboard-split {
    display: block;
  }
  .dashboard-split__main {
    min-width: 0;
  }
  @media (min-width: 960px) {
    .dashboard-split {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 400px);
      align-items: start;
    }
    .dashboard-split__main {
      grid-column: 1;
      grid-row: 1;
    }
    .insights {
      grid-column: 2;
      grid-row: 1;
      border-bottom: none;
      border-right: none;
      border-left: 1px solid var(--border);
      padding-left: 28px;
      padding-right: 48px;
      position: sticky;
      top: 0;
      align-self: start;
      max-height: 100vh;
      overflow-y: auto;
    }
    .insights .insights-method,
    .insights .insight-para,
    .insights .theme-cluster,
    .insights .highlight-list {
      max-width: none;
    }
  }

  @media (max-width: 768px) {
    header { padding: 24px; }
    .intro { padding: 24px; }
    .stats-footnote { padding: 12px 24px 16px; }
    .insights { padding: 24px; }
    .stats-bar { grid-template-columns: repeat(2, 1fr); }
    .tabs { padding: 0 24px; overflow-x: auto; }
    main { padding: 24px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-block">
    <h1>LMNA</h1>
    <p>Overzicht van recent onderzoek, klinische studies en nieuws rond het LMNA-gen en LMNA-gerelateerde hartafwijkingen — automatisch verzameld, bedoeld als achtergrond bij het gesprek met je arts, niet als medisch advies.</p>
  </div>
  <div class="last-updated">
    Laatst bijgewerkt<span id="ts">—</span>
  </div>
</header>

<section class="intro" aria-labelledby="intro-heading">
  <h2 id="intro-heading">Voor wie is dit?</h2>
  <p>LMNA-mutaties kunnen zich op verschillende manieren uiten bij het hart — bijvoorbeeld als <strong style="color:var(--text);font-weight:500">dilatatiecardiomyopathie (DCM)</strong>, maar ook met <strong style="color:var(--text);font-weight:500">geleidingsstoornissen</strong> of hartritmestoornissen. Niet iedereen met dezelfde mutatie heeft dezelfde klachten. De onderstaande lijsten zijn breed verzameld; gebruik zoekbalk en snelfilters om te vernauwen naar wat voor jullie relevant is.</p>
  <p class="intro-disclaimer"><strong>Belangrijk:</strong> dit dashboard is alleen ter informatie. Interpreteer niets zelf als diagnose of behandeladvies — bespreek altijd met je cardioloog of klinisch geneticus.</p>
  <div class="intro-tips">
    <div class="intro-tip"><strong>Focus DCM / pompfunctie</strong> — probeer snelfilters zoals „DCM”, „heart failure” of „cardiomyopathy” bij publicaties en studies.</div>
    <div class="intro-tip"><strong>Focus ritme / geleiding</strong> (zoals AV-blok, bradycardie) — probeer „conduction”, „arrhythmia”, „pacing” of „AV block”. Artikelen en trials zijn vaak Engelstalig.</div>
  </div>
</section>

<div class="stats-bar">
  <div class="stat">
    <div class="stat-num" id="stat-news">—</div>
    <div class="stat-label">Nieuws</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-pubs">—</div>
    <div class="stat-label">Publicaties (totaal in db)</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-trials">—</div>
    <div class="stat-label">Studies</div>
  </div>
  <div class="stat">
    <div class="stat-num green" id="stat-recruiting">—</div>
    <div class="stat-label">Werving open</div>
  </div>
</div>
<p class="stats-footnote">De getallen zijn <em>totaal in de database</em>, niet alles op één scherm. Per tab tonen we de recentste items; gebruik zoeken en filters om gericht te lezen — je hoeft niet „alles” te verwerken.</p>

<div class="dashboard-split">
<section class="insights" aria-labelledby="insights-heading">
  <h2 id="insights-heading">Wat valt op?</h2>
  <p class="insights-method" id="insights-method"></p>
  <div id="insights-body"></div>
</section>

<div class="dashboard-split__main">
<div class="tabs">
  <button class="tab active" onclick="switchTab('news', this)">Nieuws</button>
  <button class="tab" onclick="switchTab('publications', this)">Publicaties</button>
  <button class="tab" onclick="switchTab('trials', this)">Klinische studies</button>
</div>

<main>

<!-- NEWS -->
<div id="panel-news" class="panel active">
  <div class="sort-row" aria-label="Sorteer nieuws">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setNewsSort('relevance', this)">Relevantie</button>
    <button type="button" class="filter-btn" onclick="setNewsSort('date', this)">Recent</button>
  </div>
  <div class="chip-row" aria-label="Snel zoeken nieuws">
    <span class="chip-label">Snel zoeken</span>
    <button type="button" class="chip" onclick="quickNews('lamin')">LMNA / lamin</button>
    <button type="button" class="chip" onclick="quickNews('cardiomyopathy')">cardiomyopathie</button>
    <button type="button" class="chip" onclick="quickNews('dilated')">DCM</button>
    <button type="button" class="chip" onclick="quickNews('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickNews('')">alles tonen</button>
  </div>
  <div class="search-bar">
    <input type="text" id="search-news" placeholder="Zoek in nieuws…" oninput="filterNews()" autocomplete="off">
  </div>
  <div class="result-count" id="count-news"></div>
  <div class="card-grid" id="news-list"></div>
</div>

<!-- PUBLICATIONS -->
<div id="panel-publications" class="panel">
  <p class="panel-hint">Samenvattingen komen uit PubMed; voor de volledige tekst opent je de link. Staat een abstract vreemd afgekapt, dan is dat meestal door automatisch ophalen — de paper zelf op PubMed is leidend.</p>
  <div class="sort-row" aria-label="Sorteer publicaties">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setPubSort('relevance', this)">Relevantie</button>
    <button type="button" class="filter-btn" onclick="setPubSort('date', this)">Recent</button>
  </div>
  <div class="chip-row" aria-label="Snel zoeken publicaties">
    <span class="chip-label">Snel zoeken</span>
    <button type="button" class="chip" onclick="quickPub('dilated cardiomyopathy')">DCM</button>
    <button type="button" class="chip" onclick="quickPub('LMNA')">LMNA</button>
    <button type="button" class="chip" onclick="quickPub('heart failure')">hartfalen</button>
    <button type="button" class="chip" onclick="quickPub('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickPub('arrhythmia')">aritmie</button>
    <button type="button" class="chip" onclick="quickPub('pacing')">pacemaker</button>
    <button type="button" class="chip" onclick="quickPub('')">alles tonen</button>
  </div>
  <div class="search-bar">
    <input type="text" id="search-pubs" placeholder="Zoek in titel, auteurs, abstract, tijdschrift…" oninput="filterPubs()" autocomplete="off">
  </div>
  <div class="result-count" id="count-pubs"></div>
  <div class="card-grid" id="pubs-list"></div>
</div>

<!-- TRIALS -->
<div id="panel-trials" class="panel">
  <p class="panel-hint"><strong>RECRUITING</strong> betekent dat de studie deelnemers zoekt (inschrijfvoorwaarden staan op ClinicalTrials.gov). Dit is géén aanbeveling om mee te doen — alleen een startpunt om met je team te bespreken.</p>
  <div class="sort-row" aria-label="Sorteer studies">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setTrialSort('relevance', this)">Relevantie</button>
    <button type="button" class="filter-btn" onclick="setTrialSort('date', this)">Startdatum</button>
  </div>
  <div class="chip-row" aria-label="Snel zoeken studies">
    <span class="chip-label">Snel zoeken</span>
    <button type="button" class="chip" onclick="quickTrial('LMNA')">LMNA</button>
    <button type="button" class="chip" onclick="quickTrial('cardiomyopathy')">cardiomyopathie</button>
    <button type="button" class="chip" onclick="quickTrial('dilated')">DCM</button>
    <button type="button" class="chip" onclick="quickTrial('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickTrial('lamin')">lamin</button>
    <button type="button" class="chip" onclick="quickTrial('')">alles tonen</button>
  </div>
  <div class="filter-row" id="trial-filters"></div>
  <div class="search-bar">
    <input type="text" id="search-trials" placeholder="Zoek in studietitel, aandoening, interventie…" oninput="filterTrials()" autocomplete="off">
  </div>
  <div class="result-count" id="count-trials"></div>
  <div class="trial-grid" id="trials-list"></div>
</div>

</main>
</div>
</div>

<script>
const DATA = __DATA__;

function escHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function renderInsights() {
  const ins = DATA.insights || {};
  const noteEl = document.getElementById("insights-method");
  if (noteEl) noteEl.textContent = ins.method_note || "";
  const body = document.getElementById("insights-body");
  if (!body) return;
  const parts = [];
  for (const p of ins.paragraphs || []) {
    parts.push(`<p class="insight-para">${escHtml(p)}</p>`);
  }
  const hl = ins.highlights || [];
  if (hl.length) {
    parts.push(
      `<div class="highlight-list"><strong>Hoogste relevantiescore (heuristiek)</strong><ol>` +
      hl.map(t => `<li>${escHtml(t)}</li>`).join("") +
      `</ol></div>`
    );
  }
  for (const row of ins.theme_rows || []) {
    const ex = (row.examples || []).map(t => `<li>${escHtml(t)}</li>`).join("");
    parts.push(
      `<div class="theme-cluster"><h3>${escHtml(row.label)}</h3>` +
      `<div class="count">${row.count} publicatie(s) in dit overzicht</div><ul>${ex}</ul></div>`
    );
  }
  body.innerHTML = parts.join("");
}

/** Afnemende relevantie, daarna datum (recent eerst). */
function sortByRelevanceDesc(arr, dateField) {
  const copy = [...arr];
  copy.sort((a, b) => {
    const dr = (b.relevance || 0) - (a.relevance || 0);
    if (dr) return dr;
    const da = String(a[dateField] || "");
    const db = String(b[dateField] || "");
    return db.localeCompare(da);
  });
  return copy;
}

// ── Stats ─────────────────────────────────────────────────────────────────
document.getElementById("ts").textContent = DATA.stats.last_updated;
document.getElementById("stat-pubs").textContent = DATA.stats.total_pubs;
document.getElementById("stat-trials").textContent = DATA.stats.total_trials;
document.getElementById("stat-recruiting").textContent = DATA.stats.recruiting;
document.getElementById("stat-news").textContent = DATA.stats.total_news;
renderInsights();

// ── Tabs ──────────────────────────────────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
  btn.classList.add("active");
}

function quickNews(q) {
  document.getElementById("search-news").value = q;
  filterNews();
}
function quickPub(q) {
  document.getElementById("search-pubs").value = q;
  filterPubs();
}
function quickTrial(q) {
  document.getElementById("search-trials").value = q;
  filterTrials();
}

function newsItemDate(n) {
  return String(n.pub_date || n.fetched_at || "");
}

// ── Publications ──────────────────────────────────────────────────────────
let pubFilter = "";
let pubSort = "relevance";

function setPubSort(mode, btn) {
  pubSort = mode;
  const row = btn.closest(".sort-row");
  if (row) row.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderPubs();
}

function sortPubsList(arr) {
  const copy = [...arr];
  if (pubSort === "relevance") {
    copy.sort((a, b) => {
      const dr = (b.relevance || 0) - (a.relevance || 0);
      if (dr) return dr;
      return String(b.pub_date || "").localeCompare(String(a.pub_date || ""));
    });
  } else {
    copy.sort((a, b) => String(b.pub_date || "").localeCompare(String(a.pub_date || "")));
  }
  return copy;
}

function filterPubs() {
  pubFilter = document.getElementById("search-pubs").value.toLowerCase();
  renderPubs();
}

function renderPubs() {
  const filtered = DATA.publications.filter(p =>
    (p.title || "").toLowerCase().includes(pubFilter) ||
    (p.authors || "").toLowerCase().includes(pubFilter) ||
    (p.abstract || "").toLowerCase().includes(pubFilter) ||
    (p.journal || "").toLowerCase().includes(pubFilter)
  );
  const sorted = sortPubsList(filtered);
  document.getElementById("count-pubs").textContent =
    `${sorted.length} van ${DATA.publications.length} publicaties in dit overzicht`;
  const el = document.getElementById("pubs-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🔬</div>Geen resultaten. Probeer een andere zoekterm of „alles tonen”.</div>';
    return;
  }
  el.innerHTML = sorted.map(p => {
    const chips = (p.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const rel = typeof p.relevance === "number" ? p.relevance : 0;
    const badges = `<div class="card-badges"><span class="rel-chip">Relevantie ${rel}</span>${chips}</div>`;
    return `
    <div class="card">
      ${badges}
      <div class="card-header">
        <div class="card-title"><a href="${p.url}" target="_blank" rel="noopener">${p.title || "—"}</a></div>
        <div class="card-date">${p.pub_date || ""}</div>
      </div>
      <div class="card-meta">
        <strong>${p.journal || "—"}</strong>${p.authors ? " · " + p.authors : ""}
      </div>
      ${p.abstract ? `
        <div class="abstract" id="abs-${p.id}">${p.abstract}</div>
        <span class="toggle-abstract" onclick="toggleAbs('${p.id}', this)">▸ toon abstract</span>
      ` : ""}
    </div>
  `;
  }).join("");
}

function toggleAbs(id, el) {
  const abs = document.getElementById("abs-" + id);
  abs.classList.toggle("open");
  el.textContent = abs.classList.contains("open") ? "▾ verberg abstract" : "▸ toon abstract";
}

// ── Trials ────────────────────────────────────────────────────────────────
let trialStatusFilter = "ALL";
let trialSearch = "";
let trialSort = "relevance";

function setTrialSort(mode, btn) {
  trialSort = mode;
  const row = btn.closest(".sort-row");
  if (row) row.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderTrials();
}

function sortTrialsList(arr) {
  const copy = [...arr];
  if (trialSort === "relevance") {
    return sortByRelevanceDesc(copy, "start_date");
  }
  copy.sort((a, b) => {
    const da = String(a.start_date || "");
    const db = String(b.start_date || "");
    const c = db.localeCompare(da);
    if (c) return c;
    return (b.relevance || 0) - (a.relevance || 0);
  });
  return copy;
}

function badgeClass(status) {
  if (!status) return "badge-other";
  const s = status.toUpperCase();
  if (s.includes("RECRUIT")) return "badge-recruiting";
  if (s.includes("ACTIVE") || s.includes("ENROLLING")) return "badge-active";
  if (s.includes("COMPLET")) return "badge-completed";
  return "badge-other";
}

function buildTrialFilters() {
  const statuses = [...new Set(DATA.trials.map(t => t.status).filter(Boolean))];
  const el = document.getElementById("trial-filters");
  function escapeAttr(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }
  const parts = [
    `<button type="button" class="filter-btn active" data-trial-status="ALL">Alles</button>`
  ].concat(
    statuses.map(s =>
      `<button type="button" class="filter-btn" data-trial-status="${escapeAttr(s)}">${(s || "").replace(/_/g, " ")}</button>`
    )
  );
  el.innerHTML = parts.join("");
  el.querySelectorAll("[data-trial-status]").forEach(btn => {
    btn.addEventListener("click", () => {
      trialStatusFilter = btn.getAttribute("data-trial-status") || "ALL";
      document.querySelectorAll("#trial-filters .filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderTrials();
    });
  });
}

function filterTrials() {
  trialSearch = document.getElementById("search-trials").value.toLowerCase();
  renderTrials();
}

function renderTrials() {
  const filtered = DATA.trials.filter(t => {
    const matchStatus = trialStatusFilter === "ALL" || t.status === trialStatusFilter;
    const matchSearch = !trialSearch ||
      (t.title || "").toLowerCase().includes(trialSearch) ||
      (t.conditions || "").toLowerCase().includes(trialSearch) ||
      (t.interventions || "").toLowerCase().includes(trialSearch);
    return matchStatus && matchSearch;
  });
  const sorted = sortTrialsList(filtered);
  document.getElementById("count-trials").textContent =
    `${sorted.length} van ${DATA.trials.length} studies in dit overzicht`;
  const el = document.getElementById("trials-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🧪</div>Geen studies gevonden. Pas de statusfilter of zoekterm aan.</div>';
    return;
  }
  el.innerHTML = sorted.map(t => {
    const tChips = (t.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const tRel = typeof t.relevance === "number" ? t.relevance : 0;
    const tBadges = `<div class="card-badges"><span class="rel-chip">Relevantie ${tRel}</span>${tChips}</div>`;
    return `
    <div class="trial-card">
      ${tBadges}
      <div class="trial-header">
        <div class="trial-title"><a href="${t.url}" target="_blank" rel="noopener">${t.title || "—"}</a></div>
        <span class="badge ${badgeClass(t.status)}">${(t.status || "—").replace(/_/g," ")}</span>
      </div>
      <div class="trial-meta">
        <span><strong>${t.nct_id}</strong></span>
        ${t.phase ? `<span>Fase: <strong>${t.phase}</strong></span>` : ""}
        ${t.start_date ? `<span>Start: <strong>${t.start_date}</strong></span>` : ""}
        ${t.primary_end ? `<span>Einde: <strong>${t.primary_end}</strong></span>` : ""}
        ${t.locations ? `<span>📍 ${t.locations}</span>` : ""}
        ${t.interventions ? `<span>💊 ${t.interventions}</span>` : ""}
      </div>
    </div>
  `;
  }).join("");
}

// ── News ──────────────────────────────────────────────────────────────────
let newsFilter = "";
let newsSort = "relevance";

function setNewsSort(mode, btn) {
  newsSort = mode;
  const row = btn.closest(".sort-row");
  if (row) row.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderNews();
}

function sortNewsList(arr) {
  const copy = [...arr];
  if (newsSort === "relevance") {
    copy.sort((a, b) => {
      const dr = (b.relevance || 0) - (a.relevance || 0);
      if (dr) return dr;
      const da = newsItemDate(a);
      const db = newsItemDate(b);
      return db.localeCompare(da);
    });
    return copy;
  }
  copy.sort((a, b) => {
    const da = newsItemDate(a);
    const db = newsItemDate(b);
    const c = db.localeCompare(da);
    if (c) return c;
    return (b.relevance || 0) - (a.relevance || 0);
  });
  return copy;
}

function filterNews() {
  newsFilter = document.getElementById("search-news").value.toLowerCase();
  renderNews();
}
function renderNews() {
  const filtered = DATA.news.filter(n =>
    (n.title || "").toLowerCase().includes(newsFilter) ||
    (n.source || "").toLowerCase().includes(newsFilter) ||
    (n.summary || "").toLowerCase().includes(newsFilter)
  );
  const sorted = sortNewsList(filtered);
  document.getElementById("count-news").textContent =
    `${sorted.length} van ${DATA.news.length} nieuwsberichten in dit overzicht`;
  const el = document.getElementById("news-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">📰</div>Geen nieuws gevonden. Probeer een andere zoekterm.</div>';
    return;
  }
  el.innerHTML = sorted.map(n => {
    const nChips = (n.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const nRel = typeof n.relevance === "number" ? n.relevance : 0;
    const nBadges = `<div class="card-badges"><span class="rel-chip">Relevantie ${nRel}</span>${nChips}</div>`;
    return `
    <div class="card">
      ${nBadges}
      <div class="card-header">
        <div class="card-title"><a href="${n.url}" target="_blank" rel="noopener">${n.title || "—"}</a></div>
        <div class="card-date">${(n.pub_date || "").substring(0, 16)}</div>
      </div>
      <div class="card-meta"><strong>${n.source || "—"}</strong></div>
      ${n.summary ? `<div style="color:#9aa39b;font-size:12px;line-height:1.7">${n.summary}</div>` : ""}
    </div>
  `;
  }).join("");
}

// ── Init ──────────────────────────────────────────────────────────────────
renderPubs();
buildTrialFilters();
renderTrials();
renderNews();
</script>
</body>
</html>
"""

def generate():
    pubs, trials, news, stats = load_data()
    pubs, trials, news, insights = enrich_all(pubs, trials, news)
    payload = {
        "publications": pubs,
        "trials": trials,
        "news": news,
        "stats": stats,
        "insights": insights,
    }
    data_js = json.dumps(payload, ensure_ascii=False, default=str)
    html = HTML_TEMPLATE.replace("__DATA__", data_js)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard written to: {OUT_PATH}")
    print(f"   {stats['total_pubs']} publications · {stats['total_trials']} trials · {stats['total_news']} news")

if __name__ == "__main__":
    generate()
