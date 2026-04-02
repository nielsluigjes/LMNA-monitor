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
<script>(function(){var k="lmna-theme",r=document.documentElement,s=localStorage.getItem(k),l=window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches;if(s==="light"||(s!=="dark"&&l))r.setAttribute("data-theme","light");})();</script>
<title>LMNA — overzicht</title>
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
    --prose: #c5ccc6;
    --prose-dim: #9aa39b;
    --intro-grad: linear-gradient(180deg, rgba(20,24,23,0.6) 0%, transparent 100%);
    --insights-bg: rgba(20, 24, 23, 0.35);
    --chip-accent-bg: rgba(184, 245, 160, 0.1);
    --chip-accent-border: rgba(184, 245, 160, 0.2);
    --filter-chip-hover-bg: rgba(184,245,160,0.08);
    --summary-hover-bg: rgba(91, 196, 245, 0.06);
  }
  html[data-theme="light"] {
    color-scheme: light;
    --bg: #f1f4f2;
    --surface: #ffffff;
    --surface2: #e6ebe7;
    --border: #c9d1ca;
    --accent: #2a6b3a;
    --accent2: #0872a0;
    --accent3: #8a6700;
    --danger: #b42318;
    --text: #121814;
    --muted: #556054;
    --recruiting: #2a6b3a;
    --completed: #5c665e;
    --active: #0872a0;
    --prose: #3d463e;
    --prose-dim: #5a635c;
    --intro-grad: linear-gradient(180deg, rgba(230,235,231,0.95) 0%, transparent 100%);
    --insights-bg: rgba(230, 235, 231, 0.65);
    --chip-accent-bg: rgba(42, 107, 58, 0.1);
    --chip-accent-border: rgba(42, 107, 58, 0.22);
    --filter-chip-hover-bg: rgba(42, 107, 58, 0.1);
    --summary-hover-bg: rgba(8, 114, 160, 0.08);
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
  .header-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
  }
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 36px;
    padding: 0;
    border-radius: 4px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--muted);
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
  }
  .theme-toggle:hover {
    color: var(--accent);
    border-color: var(--accent);
  }
  .theme-toggle__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
  }
  .theme-toggle__icon svg {
    display: block;
    width: 100%;
    height: 100%;
  }
  .theme-toggle__moon { display: none; }
  html[data-theme="light"] .theme-toggle__sun { display: none; }
  html[data-theme="light"] .theme-toggle__moon { display: inline-flex; }

  /* INTRO */
  .intro {
    padding: 28px 48px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--intro-grad);
  }
  .intro h2 {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 12px;
  }
  .intro p {
    color: var(--prose);
    max-width: 52rem;
    margin-bottom: 12px;
    font-size: 14px;
  }
  .intro-disclaimer {
    font-size: 13px;
    color: var(--muted);
    border-left: 3px solid var(--accent3);
    padding-left: 14px;
    margin: 14px 0 0;
    max-width: 52rem;
  }
  .intro-lead {
    margin-bottom: 0;
    color: var(--prose);
    font-size: 14px;
    line-height: 1.5;
    max-width: 52rem;
  }
  .intro-details {
    margin-top: 16px;
    max-width: 52rem;
    border: 0;
  }
  .intro-details > summary {
    cursor: pointer;
    color: var(--accent2);
    font-size: 14px;
    font-weight: 500;
    list-style: none;
    padding: 10px 14px;
    margin: 0 -14px;
    border-radius: 8px;
    user-select: none;
    line-height: 1.45;
  }
  .intro-details > summary:hover {
    background: var(--summary-hover-bg);
  }
  .intro-details > summary::-webkit-details-marker { display: none; }
  .intro-details > summary::before {
    content: "▸ ";
    display: inline-block;
    transition: transform 0.15s;
    color: var(--muted);
  }
  .intro-details[open] > summary::before {
    transform: rotate(90deg);
  }
  .intro-details-body {
    padding: 4px 0 2px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .intro-detail-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
  }
  .intro-detail-title {
    font-family: 'Fraunces', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 10px;
    letter-spacing: -0.01em;
    line-height: 1.25;
  }
  .intro-detail-text {
    font-size: 13px;
    color: var(--muted);
    line-height: 1.55;
    margin: 0 0 12px;
  }
  .intro-detail-list {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 13px;
    color: var(--prose);
    line-height: 1.55;
  }
  .intro-detail-list li + li { margin-top: 10px; }
  .intro-detail-list strong { color: var(--text); font-weight: 500; }
  .intro-search-hints {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .intro-search-hint {
    margin: 0;
  }
  .intro-search-hint dt {
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    margin: 0 0 8px;
    line-height: 1.35;
  }
  .intro-search-hint dd {
    margin: 0;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.5;
  }
  .intro-search-term-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 8px;
    margin-top: 6px;
  }
  .intro-search-terms-label {
    font-size: 11px;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    margin-right: 4px;
  }
  .intro-search-term {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    background: var(--chip-accent-bg);
    border: 1px solid var(--chip-accent-border);
    padding: 4px 10px;
    border-radius: 4px;
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
    color: var(--prose-dim);
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
    background: var(--filter-chip-hover-bg);
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
    background: var(--filter-chip-hover-bg);
  }

  .panel-hint {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 12px;
    max-width: 40rem;
    line-height: 1.45;
  }

  .news-sum-wrap {
    margin-top: 8px;
    border: 0;
  }
  .news-sum-wrap summary {
    cursor: pointer;
    color: var(--accent2);
    font-size: 12px;
    font-weight: 500;
    list-style: none;
    user-select: none;
  }
  .news-sum-wrap summary::-webkit-details-marker { display: none; }
  .news-sum-wrap .news-summary {
    color: var(--prose-dim);
    font-size: 12px;
    line-height: 1.65;
    margin-top: 8px;
  }

  /* INSIGHTS — lokale heuristiek, geen API */
  .insights {
    padding: 28px 48px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--insights-bg);
    max-width: 100%;
  }
  .insights h2 {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--accent3);
    margin-bottom: 6px;
    line-height: 1.2;
  }
  .insights-sub {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 14px;
    max-width: 48rem;
  }
  .insights-method {
    font-size: 12px;
    color: var(--prose);
    max-width: 48rem;
    line-height: 1.5;
    margin-bottom: 16px;
    padding: 10px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    border-left: 3px solid var(--accent3);
  }
  .insight-block {
    margin-bottom: 18px;
  }
  .insight-block:last-child { margin-bottom: 0; }
  .insight-block-title {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 8px;
    line-height: 1.3;
    letter-spacing: -0.01em;
  }
  .insight-block-lead {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.5;
    margin: 0 0 12px;
  }
  .insight-block--recruit {
    padding-left: 12px;
    border-left: 3px solid var(--accent);
  }
  .insight-para {
    color: var(--prose);
    font-size: 13px;
    max-width: 48rem;
    line-height: 1.55;
    margin: 0;
  }
  .theme-cluster {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
    margin-bottom: 8px;
    max-width: 48rem;
  }
  .theme-cluster h3 {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--accent2);
    margin-bottom: 4px;
  }
  .theme-cluster-blurb {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 8px;
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
    color: var(--prose-dim);
    font-size: 13px;
    line-height: 1.6;
  }
  .highlight-list {
    max-width: 48rem;
    margin: 0;
    padding: 12px 14px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  .highlight-list__title {
    display: block;
    font-family: 'Fraunces', serif;
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.25;
  }
  .highlight-list__lead {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 10px;
  }
  .highlight-list ol {
    margin: 0;
    padding-left: 1.2rem;
    color: var(--prose);
    font-size: 13px;
    line-height: 1.65;
  }
  .highlight-list a.insight-link,
  .theme-cluster ul a.insight-link {
    color: inherit;
    text-decoration: none;
    border-bottom: 1px solid rgba(91, 196, 245, 0.3);
  }
  .highlight-list a.insight-link:hover,
  .theme-cluster ul a.insight-link:hover {
    color: var(--accent2);
    border-bottom-color: var(--accent2);
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
    .insights {
      display: none;
    }
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
    <p>Onderzoek, studies en nieuws — ter informatie. Geen medisch advies.</p>
  </div>
  <div class="header-meta">
    <button type="button" class="theme-toggle" id="theme-toggle" aria-pressed="false" aria-label="Schakel naar licht thema">
      <span class="theme-toggle__icon theme-toggle__sun" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></span>
      <span class="theme-toggle__icon theme-toggle__moon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></span>
    </button>
    <div class="last-updated">
      Laatst bijgewerkt<span id="ts">—</span>
    </div>
  </div>
</header>

<section class="intro" aria-labelledby="intro-heading">
  <h2 id="intro-heading">Voor wie</h2>
  <p class="intro-lead">Voor patiënten en gezinnen die LMNA-bronnen op één plek willen. Zoek en filter om te vernauwen.</p>
  <p class="intro-disclaimer">Niet voor zelfdiagnose — overleg met je cardioloog of geneticus.</p>
  <details class="intro-details">
    <summary>Uitleg: LMNA en het hart, en hoe je hier zoekt</summary>
    <div class="intro-details-body">
      <section class="intro-detail-section" aria-labelledby="intro-heart-title">
        <h3 id="intro-heart-title" class="intro-detail-title">LMNA en het hart</h3>
        <p class="intro-detail-text">Een mutatie in LMNA kan het hart op verschillende manieren beïnvloeden. Daarom staan er veel verschillende studies en artikelen in dit overzicht — lang niet alles is voor jou relevant.</p>
        <ul class="intro-detail-list">
          <li>Het hart kan minder stevig pompen. Dat noemen artsen vaak <strong>dilatatieve cardiomyopathie</strong>, kort <strong>DCM</strong>.</li>
          <li>Of er zijn klachten door een verstoorde <strong>geleiding</strong> van de elektrische prikkel in het hart, of door een <strong>ritmestoornis</strong>.</li>
        </ul>
      </section>
      <section class="intro-detail-section" aria-labelledby="intro-search-title">
        <h3 id="intro-search-title" class="intro-detail-title">Hoe je hier zoekt</h3>
        <p class="intro-detail-text">Typ onderstaande woorden in de zoekbalk van een tab. Veel bronnen zijn Engelstalig; daarom staan er ook Engelse zoektermen bij.</p>
        <dl class="intro-search-hints">
          <div class="intro-search-hint">
            <dt>Onderwerp: zwakker wordend hart of hartfalen</dt>
            <dd>
              <div class="intro-search-term-row">
                <span class="intro-search-terms-label">Probeer</span>
                <span class="intro-search-term">DCM</span>
                <span class="intro-search-term">heart failure</span>
                <span class="intro-search-term">cardiomyopathy</span>
              </div>
            </dd>
          </div>
          <div class="intro-search-hint">
            <dt>Onderwerp: ritme of geleiding (bijv. AV-blok)</dt>
            <dd>
              <div class="intro-search-term-row">
                <span class="intro-search-terms-label">Probeer</span>
                <span class="intro-search-term">conduction</span>
                <span class="intro-search-term">arrhythmia</span>
                <span class="intro-search-term">AV block</span>
              </div>
            </dd>
          </div>
        </dl>
      </section>
    </div>
  </details>
</section>

<div class="stats-bar">
  <div class="stat">
    <div class="stat-num" id="stat-news">—</div>
    <div class="stat-label">Nieuws</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-pubs">—</div>
    <div class="stat-label">Publicaties</div>
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
<div class="dashboard-split">
<section class="insights" aria-labelledby="insights-heading">
  <h2 id="insights-heading">Waar begin je?</h2>
  <p class="insights-sub">Korte oriëntatie — geen medisch advies. Gebruik de tabs links om nieuws, publicaties en studies te bekijken.</p>
  <p class="insights-method" id="insights-method"></p>
  <div id="insights-body"></div>
</section>

<div class="dashboard-split__main">
<div class="tabs">
  <button class="tab active" onclick="switchTab('news', this)">Nieuws</button>
  <button class="tab" onclick="switchTab('publications', this)">Publicaties</button>
  <button class="tab" onclick="switchTab('trials', this)">Studies</button>
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
    <span class="chip-label">Snel</span>
    <button type="button" class="chip" onclick="quickNews('lamin')">LMNA / lamin</button>
    <button type="button" class="chip" onclick="quickNews('cardiomyopathy')">cardiomyopathie</button>
    <button type="button" class="chip" onclick="quickNews('dilated')">DCM</button>
    <button type="button" class="chip" onclick="quickNews('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickNews('')">alles tonen</button>
  </div>
  <div class="search-bar">
    <input type="text" id="search-news" placeholder="Zoek…" oninput="filterNews()" autocomplete="off">
  </div>
  <div class="result-count" id="count-news"></div>
  <div class="card-grid" id="news-list"></div>
</div>

<!-- PUBLICATIONS -->
<div id="panel-publications" class="panel">
  <div class="sort-row" aria-label="Sorteer publicaties">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setPubSort('relevance', this)">Relevantie</button>
    <button type="button" class="filter-btn" onclick="setPubSort('date', this)">Recent</button>
  </div>
  <div class="chip-row" aria-label="Snel zoeken publicaties">
    <span class="chip-label">Snel</span>
    <button type="button" class="chip" onclick="quickPub('dilated cardiomyopathy')">DCM</button>
    <button type="button" class="chip" onclick="quickPub('LMNA')">LMNA</button>
    <button type="button" class="chip" onclick="quickPub('heart failure')">hartfalen</button>
    <button type="button" class="chip" onclick="quickPub('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickPub('arrhythmia')">aritmie</button>
    <button type="button" class="chip" onclick="quickPub('pacing')">pacemaker</button>
    <button type="button" class="chip" onclick="quickPub('')">alles tonen</button>
  </div>
  <div class="search-bar">
    <input type="text" id="search-pubs" placeholder="Zoek…" oninput="filterPubs()" autocomplete="off">
  </div>
  <div class="result-count" id="count-pubs"></div>
  <div class="card-grid" id="pubs-list"></div>
</div>

<!-- TRIALS -->
<div id="panel-trials" class="panel">
  <p class="panel-hint"><strong>RECRUITING</strong> = studie zoekt deelnemers (geen aanbeveling; bespreek met je arts).</p>
  <div class="sort-row" aria-label="Sorteer studies">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setTrialSort('relevance', this)">Relevantie</button>
    <button type="button" class="filter-btn" onclick="setTrialSort('date', this)">Startdatum</button>
  </div>
  <div class="chip-row" aria-label="Snel zoeken studies">
    <span class="chip-label">Snel</span>
    <button type="button" class="chip" onclick="quickTrial('LMNA')">LMNA</button>
    <button type="button" class="chip" onclick="quickTrial('cardiomyopathy')">cardiomyopathie</button>
    <button type="button" class="chip" onclick="quickTrial('dilated')">DCM</button>
    <button type="button" class="chip" onclick="quickTrial('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickTrial('lamin')">lamin</button>
    <button type="button" class="chip" onclick="quickTrial('')">alles tonen</button>
  </div>
  <div class="filter-row" id="trial-filters"></div>
  <div class="search-bar">
    <input type="text" id="search-trials" placeholder="Zoek…" oninput="filterTrials()" autocomplete="off">
  </div>
  <div class="result-count" id="count-trials"></div>
  <div class="trial-grid" id="trials-list"></div>
</div>

</main>
</div>
</div>

<script>
(function initThemeToggle() {
  const KEY = "lmna-theme";
  const root = document.documentElement;
  const btn = document.getElementById("theme-toggle");
  function prefersLight() {
    return window.matchMedia && matchMedia("(prefers-color-scheme: light)").matches;
  }
  function effectiveMode() {
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
  }
  function syncButton() {
    if (!btn) return;
    const light = effectiveMode() === "light";
    btn.setAttribute("aria-pressed", light ? "true" : "false");
    var label = light ? "Schakel naar donker thema" : "Schakel naar licht thema";
    btn.setAttribute("aria-label", label);
    btn.title = label;
  }
  function applyFromStorage() {
    const s = localStorage.getItem(KEY);
    if (s === "light") root.setAttribute("data-theme", "light");
    else if (s === "dark") root.removeAttribute("data-theme");
    else if (prefersLight()) root.setAttribute("data-theme", "light");
    else root.removeAttribute("data-theme");
    syncButton();
  }
  applyFromStorage();
  btn?.addEventListener("click", function () {
    const next = effectiveMode() === "light" ? "dark" : "light";
    if (next === "light") root.setAttribute("data-theme", "light");
    else root.removeAttribute("data-theme");
    localStorage.setItem(KEY, next);
    syncButton();
  });
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", function () {
    if (localStorage.getItem(KEY) === "light" || localStorage.getItem(KEY) === "dark") return;
    applyFromStorage();
  });
})();
const DATA = __DATA__;

function escHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function escAttr(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

/** Publicatie-aanbeveling: { title, url } of legacy string. */
function insightRecLi(item) {
  const title = typeof item === "string" ? item : (item && item.title) || "";
  const url = typeof item === "string" ? "" : (item && item.url) || "";
  const t = escHtml(title);
  if (url) {
    return `<li><a class="insight-link" href="${escAttr(url)}" target="_blank" rel="noopener">${t}</a></li>`;
  }
  return `<li>${t}</li>`;
}

function renderInsights() {
  const ins = DATA.insights || {};
  const noteEl = document.getElementById("insights-method");
  if (noteEl) noteEl.textContent = ins.method_note || "";
  const body = document.getElementById("insights-body");
  if (!body) return;
  const parts = [];
  if (ins.overview_line) {
    parts.push(
      `<div class="insight-block">` +
        `<h3 class="insight-block-title">Wat staat er in dit scherm?</h3>` +
        `<p class="insight-para">${escHtml(ins.overview_line)}</p>` +
      `</div>`
    );
  }
  if (ins.recruiting_note) {
    parts.push(
      `<div class="insight-block insight-block--recruit">` +
        `<h3 class="insight-block-title">Studies die deelnemers zoeken</h3>` +
        `<p class="insight-para">${escHtml(ins.recruiting_note)}</p>` +
      `</div>`
    );
  }
  const hl = ins.highlights || [];
  if (hl.length) {
    parts.push(
      `<div class="insight-block">` +
        `<div class="highlight-list">` +
        `<span class="highlight-list__title">Waar kun je starten met lezen?</span>` +
        `<p class="highlight-list__lead">Vijf publicaties die in dit overzicht vaak aansluiten op LMNA en het hart — automatisch gekozen op titel en samenvatting.</p>` +
        `<ol>` +
        hl.map(insightRecLi).join("") +
        `</ol></div></div>`
    );
  }
  const rows = ins.theme_rows || [];
  if (rows.length) {
    parts.push(`<div class="insight-block">`);
    parts.push(`<h3 class="insight-block-title">Onderwerpen bij de publicaties</h3>`);
    if (ins.themes_intro) {
      parts.push(`<p class="insight-block-lead">${escHtml(ins.themes_intro)}</p>`);
    }
    for (const row of rows) {
      const ex = (row.examples || []).map(insightRecLi).join("");
      const blurb = row.blurb
        ? `<p class="theme-cluster-blurb">${escHtml(row.blurb)}</p>`
        : "";
      parts.push(
        `<div class="theme-cluster"><h3>${escHtml(row.label)}</h3>${blurb}` +
        `<div class="count">${row.count} publicatie(s) in dit scherm</div><ul>${ex}</ul></div>`
      );
    }
    parts.push(`</div>`);
  } else if (ins.empty_themes_note) {
    parts.push(
      `<div class="insight-block"><p class="insight-para">${escHtml(ins.empty_themes_note)}</p></div>`
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
    `${sorted.length} / ${DATA.publications.length} publicaties`;
  const el = document.getElementById("pubs-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🔬</div>Geen resultaten — pas zoek of filters aan.</div>';
    return;
  }
  el.innerHTML = sorted.map(p => {
    const chips = (p.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const rel = typeof p.relevance === "number" ? p.relevance : 0;
    const badges = `<div class="card-badges"><span class="rel-chip" title="Relevantiescore (automatisch)" aria-label="Relevantie ${rel}">${rel}</span>${chips}</div>`;
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
        <span class="toggle-abstract" onclick="toggleAbs('${p.id}', this)">▸ abstract</span>
      ` : ""}
    </div>
  `;
  }).join("");
}

function toggleAbs(id, el) {
  const abs = document.getElementById("abs-" + id);
  abs.classList.toggle("open");
  el.textContent = abs.classList.contains("open") ? "▾ verberg" : "▸ abstract";
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
    `${sorted.length} / ${DATA.trials.length} studies`;
  const el = document.getElementById("trials-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🧪</div>Geen studies — pas filter of zoekterm.</div>';
    return;
  }
  el.innerHTML = sorted.map(t => {
    const tChips = (t.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const tRel = typeof t.relevance === "number" ? t.relevance : 0;
    const tBadges = `<div class="card-badges"><span class="rel-chip" title="Relevantiescore (automatisch)" aria-label="Relevantie ${tRel}">${tRel}</span>${tChips}</div>`;
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
    `${sorted.length} / ${DATA.news.length} nieuws`;
  const el = document.getElementById("news-list");
  if (!sorted.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">📰</div>Geen nieuws — pas je zoekterm aan.</div>';
    return;
  }
  el.innerHTML = sorted.map(n => {
    const nChips = (n.theme_labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
    const nRel = typeof n.relevance === "number" ? n.relevance : 0;
    const nBadges = `<div class="card-badges"><span class="rel-chip" title="Relevantiescore (automatisch)" aria-label="Relevantie ${nRel}">${nRel}</span>${nChips}</div>`;
    return `
    <div class="card">
      ${nBadges}
      <div class="card-header">
        <div class="card-title"><a href="${n.url}" target="_blank" rel="noopener">${n.title || "—"}</a></div>
        <div class="card-date">${(n.pub_date || "").substring(0, 16)}</div>
      </div>
      <div class="card-meta"><strong>${n.source || "—"}</strong></div>
      ${n.summary ? `<details class="news-sum-wrap"><summary>Samenvatting</summary><div class="news-summary">${escHtml(n.summary)}</div></details>` : ""}
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
