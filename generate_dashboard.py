#!/usr/bin/env python3
"""
LMNA Monitor: Dashboard Generator
Reads lmna.db and produces a self-contained dashboard.html
Run after scraper.py: python3 generate_dashboard.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

from insight_engine import enrich_all
from scraper import rss_html_to_plain

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

    news_rows = con.execute("""
        SELECT * FROM news ORDER BY fetched_at DESC LIMIT 100
    """).fetchall()
    news = [
        {**dict(row), "summary": rss_html_to_plain(row["summary"] or "")}
        for row in news_rows
    ]

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
        news,
        stats
    )

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>(function(){var k="lmna-theme",r=document.documentElement,s=localStorage.getItem(k),l=window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches;if(s==="light"||(s!=="dark"&&l))r.setAttribute("data-theme","light");})();</script>
<title>LMNA-Monitor: overzicht</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
  :root {
    --radius-sm: 10px;
    --radius-md: 16px;
    --radius-lg: 22px;
    --radius-pill: 9999px;
    --shadow-sm: 0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 20px rgba(0,0,0,0.22);
    --shadow-md: 0 1px 0 rgba(255,255,255,0.05) inset, 0 12px 40px rgba(0,0,0,0.35);
    --shadow-hover: 0 1px 0 rgba(255,255,255,0.06) inset, 0 16px 48px rgba(0,0,0,0.4);
    --bg: #080a09;
    --surface: #101412;
    --surface2: #181c1a;
    --surface-elevated: #1e2320;
    --border: rgba(255,255,255,0.08);
    --accent: #9fe88a;
    --accent2: #6dd4ff;
    --accent3: #f0c14d;
    --danger: #ff6b6b;
    --text: #eef2ee;
    --muted: #8a938b;
    --recruiting: #9fe88a;
    --completed: #7a847c;
    --active: #6dd4ff;
    --prose: #c4cbc5;
    --prose-dim: #9aa39b;
    --intro-grad: linear-gradient(165deg, rgba(30,35,32,0.55) 0%, transparent 55%);
    --insights-bg: rgba(16, 20, 18, 0.5);
    --chip-accent-bg: rgba(159, 232, 138, 0.12);
    --chip-accent-border: rgba(159, 232, 138, 0.22);
    --filter-chip-hover-bg: rgba(159, 232, 138, 0.1);
    --summary-hover-bg: rgba(109, 212, 255, 0.08);
    --tabs-bar-bg: rgba(8, 10, 9, 0.72);
  }
  html[data-theme="light"] {
    color-scheme: light;
    --shadow-sm: 0 1px 0 rgba(255,255,255,0.85) inset, 0 4px 24px rgba(15, 40, 25, 0.06);
    --shadow-md: 0 1px 0 rgba(255,255,255,0.9) inset, 0 12px 40px rgba(15, 40, 25, 0.08);
    --shadow-hover: 0 1px 0 rgba(255,255,255,0.95) inset, 0 20px 50px rgba(15, 40, 25, 0.1);
    --bg: #f4f7f4;
    --surface: #ffffff;
    --surface2: #eef2ee;
    --surface-elevated: #ffffff;
    --border: rgba(15, 40, 25, 0.1);
    --accent: #1d6b32;
    --accent2: #0a6f9e;
    --accent3: #8a5f00;
    --danger: #b42318;
    --text: #0f1711;
    --muted: #5c665e;
    --recruiting: #1d6b32;
    --completed: #5c665e;
    --active: #0a6f9e;
    --prose: #3a443c;
    --prose-dim: #5a635c;
    --intro-grad: linear-gradient(165deg, rgba(255,255,255,0.92) 0%, transparent 50%);
    --insights-bg: rgba(255, 255, 255, 0.72);
    --chip-accent-bg: rgba(29, 107, 50, 0.1);
    --chip-accent-border: rgba(29, 107, 50, 0.2);
    --filter-chip-hover-bg: rgba(29, 107, 50, 0.08);
    --summary-hover-bg: rgba(10, 111, 158, 0.08);
    --tabs-bar-bg: rgba(244, 247, 244, 0.82);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse 100% 70% at 0% -10%, rgba(159, 232, 138, 0.09), transparent 52%),
      radial-gradient(ellipse 90% 55% at 100% 0%, rgba(109, 212, 255, 0.07), transparent 48%),
      radial-gradient(ellipse 70% 45% at 50% 110%, rgba(240, 193, 77, 0.05), transparent 55%);
    color: var(--text);
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    font-size: 15px;
    font-weight: 400;
    line-height: 1.6;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }
  html[data-theme="light"] body {
    background-image:
      radial-gradient(ellipse 100% 70% at 0% -10%, rgba(29, 107, 50, 0.06), transparent 52%),
      radial-gradient(ellipse 90% 55% at 100% 0%, rgba(10, 111, 158, 0.05), transparent 48%);
  }

  /* HEADER */
  header {
    padding: 40px 48px 28px;
    border-bottom: 1px solid var(--border);
  }
  .logo-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .logo-heading h1 {
    min-width: 0;
  }
  .logo-block h1 {
    font-family: 'Fraunces', serif;
    font-size: clamp(2.25rem, 5vw, 3rem);
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.03em;
    line-height: 1.02;
    text-shadow: 0 0 48px rgba(159, 232, 138, 0.15);
  }
  html[data-theme="light"] .logo-block h1 {
    text-shadow: none;
  }
  .logo-block p {
    color: var(--accent);
    margin-top: 10px;
    font-size: 14px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 400;
    letter-spacing: 0.01em;
    text-transform: none;
    line-height: 1.55;
    max-width: 38rem;
  }
  .last-updated {
    color: var(--muted);
    font-size: 11px;
    text-align: right;
    font-family: 'DM Mono', monospace;
    margin-top: 14px;
    width: 100%;
  }
  .last-updated span {
    display: block;
    color: var(--accent);
    font-size: 12px;
    margin-top: 2px;
  }
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    padding: 0;
    border-radius: var(--radius-pill);
    border: 1px solid var(--border);
    background: var(--surface);
    box-shadow: var(--shadow-sm);
    color: var(--muted);
    cursor: pointer;
    transition: color 0.2s ease, border-color 0.2s ease, background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  }
  .theme-toggle:hover {
    color: var(--accent);
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
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
    background: var(--insights-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    max-width: 100%;
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
    margin-bottom: 12px;
    font-size: 14px;
  }
  .intro-disclaimer-section {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 48px;
    border-bottom: 1px solid color-mix(in srgb, var(--accent) 35%, var(--border));
    background: color-mix(in srgb, var(--accent) 75%, var(--bg));
    text-align: center;
    box-sizing: border-box;
  }
  .intro-disclaimer-section .intro-disclaimer {
    flex: 0 1 auto;
    width: 100%;
    font-size: 13px;
    font-weight: 700;
    line-height: 1.45;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #fff;
    max-width: 100%;
    margin: 0;
    padding: 0;
    border: none;
  }
  .intro-lead {
    margin-bottom: 0;
    color: var(--prose);
    font-size: 14px;
    line-height: 1.5;
  }
  .intro-details {
    margin-top: 16px;
    border: 0;
  }
  .intro-details > summary {
    cursor: pointer;
    color: var(--accent2);
    font-size: 14px;
    font-weight: 600;
    list-style: none;
    padding: 12px 18px 12px 16px;
    margin: 0 -16px;
    border-radius: var(--radius-md);
    user-select: none;
    line-height: 1.45;
  }
  .intro-details > summary:hover {
    background: var(--summary-hover-bg);
  }
  .intro-details > summary::-webkit-details-marker { display: none; }
  .intro-details > summary::before {
    content: "▸";
    display: inline-block;
    font-size: 1.85em;
    line-height: 0;
    vertical-align: -0.14em;
    margin-right: 0.32em;
    transition: transform 0.15s;
    color: var(--accent2);
  }
  .intro-details[open] > summary::before {
    transform: rotate(90deg);
  }
  .intro-details[open] > summary {
    margin-bottom: 14px;
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
    border-radius: var(--radius-md);
    padding: 18px 20px;
    box-shadow: var(--shadow-sm);
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
    padding: 6px 12px;
    border-radius: var(--radius-pill);
  }

  /* STATS BAR */
  .stats-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 20px 48px 28px;
    border-bottom: 1px solid var(--border);
  }
  .stat {
    padding: 22px 22px 20px;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface);
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  }
  .stat:hover {
    border-color: color-mix(in srgb, var(--accent) 25%, var(--border));
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }
  .stat-num {
    font-family: 'Fraunces', serif;
    font-size: clamp(2.25rem, 4vw, 2.85rem);
    font-weight: 700;
    line-height: 1;
    color: var(--text);
    letter-spacing: -0.02em;
  }
  .stat-num.green { color: var(--accent); }
  .stat-label {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 10px;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
  }

  /* NAV TABS */
  .tabs {
    display: flex;
    flex-wrap: nowrap;
    align-items: stretch;
    gap: 0;
    padding: 0 48px;
    min-height: 56px;
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--tabs-bar-bg);
    backdrop-filter: saturate(1.15) blur(14px);
    -webkit-backdrop-filter: saturate(1.15) blur(14px);
    border-bottom: 1px solid var(--border);
  }
  .tab {
    flex: 1 1 0;
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    cursor: pointer;
    color: var(--muted);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: none;
    border-radius: 0;
    transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
    background: transparent;
    border: none;
    border-right: 1px solid var(--border);
    font-family: 'Plus Jakarta Sans', sans-serif;
  }
  .tab:last-child { border-right: none; }
  .tab:hover { color: var(--text); background: color-mix(in srgb, var(--surface2) 55%, transparent); }
  .tab.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--surface) 90%, transparent);
    box-shadow: inset 0 -3px 0 0 var(--accent);
    border-right: 1px solid var(--border);
  }
  .tab.active:last-child { border-right: none; }

  /* MAIN CONTENT */
  main { padding: 32px 48px 48px; }
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
    border-radius: var(--radius-md);
    padding: 14px 18px;
    color: var(--text);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    outline: none;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }
  .search-bar input:focus {
    border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
    box-shadow: var(--shadow-md), 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent);
  }
  .search-bar input::placeholder { color: var(--muted); }

  /* CARDS */
  .card-grid { display: flex; flex-direction: column; gap: 14px; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 22px 24px;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, box-shadow 0.25s ease, transform 0.25s ease;
  }
  .card:hover {
    border-color: color-mix(in srgb, var(--accent) 30%, var(--border));
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
  }
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
    font-family: 'Plus Jakarta Sans', sans-serif;
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
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 500;
    flex-shrink: 0;
  }
  .badge-recruiting { background: color-mix(in srgb, var(--accent) 16%, transparent); color: var(--recruiting); border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); border-radius: var(--radius-pill); }
  .badge-active { background: color-mix(in srgb, var(--active) 16%, transparent); color: var(--active); border: 1px solid color-mix(in srgb, var(--active) 35%, transparent); border-radius: var(--radius-pill); }
  .badge-completed { background: color-mix(in srgb, var(--completed) 14%, transparent); color: var(--completed); border: 1px solid color-mix(in srgb, var(--completed) 28%, transparent); border-radius: var(--radius-pill); }
  .badge-other { background: color-mix(in srgb, var(--accent3) 16%, transparent); color: var(--accent3); border: 1px solid color-mix(in srgb, var(--accent3) 32%, transparent); border-radius: var(--radius-pill); }

  /* TRIAL CARDS */
  .trial-grid { display: flex; flex-direction: column; gap: 14px; }
  .trial-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 22px 24px;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, box-shadow 0.25s ease, transform 0.25s ease;
  }
  .trial-card:hover {
    border-color: color-mix(in srgb, var(--accent2) 32%, var(--border));
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
  }
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
    padding: 8px 16px;
    border-radius: var(--radius-pill);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: none;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  }
  .filter-btn:hover, .filter-btn.active {
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
    color: var(--accent);
    background: var(--filter-chip-hover-bg);
    box-shadow: var(--shadow-md);
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
    padding: 8px 14px;
    border-radius: var(--radius-pill);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  }
  .chip:hover {
    border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
    background: var(--filter-chip-hover-bg);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
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

  /* INSIGHTS: lokale heuristiek, geen API */
  .insights {
    padding: 28px 48px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--insights-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
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
    padding: 12px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent3);
    box-shadow: var(--shadow-sm);
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
    border-radius: var(--radius-md);
    padding: 14px 16px;
    margin-bottom: 10px;
    max-width: 48rem;
    box-shadow: var(--shadow-sm);
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
  .theme-cluster ul li {
    margin-bottom: 0.6rem;
  }
  .theme-cluster ul li:last-child {
    margin-bottom: 0;
  }
  .highlight-list {
    max-width: 48rem;
    margin: 0;
    padding: 16px 18px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
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
  .highlight-list ol li {
    margin-bottom: 0.7rem;
  }
  .highlight-list ol li:last-child {
    margin-bottom: 0;
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
  .card-reader-note {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.55;
    margin: 0 0 12px;
    max-width: 52rem;
  }
  .card-reader-note-label {
    font-weight: 500;
    color: var(--prose-dim);
    margin-right: 6px;
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

  @media (min-width: 769px) {
    .logo-heading {
      width: 100%;
      justify-content: flex-start;
    }
    .logo-heading .theme-toggle {
      margin-left: auto;
    }
    .intro-details-body {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      align-items: stretch;
    }
  }
  @media (max-width: 768px) {
    header {
      padding: 24px 20px;
    }
    .intro-disclaimer-section {
      padding: 10px 20px;
    }
    .intro { padding: 22px 20px; }
    .insights {
      display: none;
    }
    .stats-bar {
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      padding: 16px 20px 22px;
    }
    .stat { padding: 18px 16px; }
    .tabs { padding: 0 20px; min-height: 52px; overflow-x: auto; flex-wrap: nowrap; }
    main { padding: 22px 20px 36px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-block">
    <div class="logo-heading">
      <h1>LMNA-Monitor</h1>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-pressed="false" aria-label="Schakel naar licht thema">
        <span class="theme-toggle__icon theme-toggle__sun" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></span>
        <span class="theme-toggle__icon theme-toggle__moon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></span>
      </button>
    </div>
    <p>Onderzoek, studies en nieuws, ter informatie. Geen medisch advies.</p>
    <div class="last-updated">
      Laatst bijgewerkt<span id="ts">…</span>
    </div>
  </div>
</header>

<section class="intro-disclaimer-section" aria-label="Medische disclaimer">
  <p class="intro-disclaimer">Niet bedoeld voor zelfdiagnose; overleg altijd met je cardioloog of geneticus.</p>
</section>

<section class="intro" aria-labelledby="intro-heading">
  <h2 id="intro-heading">Voor wie</h2>
  <p class="intro-lead">Voor patiënten en gezinnen die LMNA-bronnen op één plek willen. Deze pagina toont het resultaat van een dagelijks geautomatiseerde zoekactie naar LMNA-bronnen: nieuws, publicaties en studies. Binnen deze resultaten kan verder gezocht worden naar wat voor jou relevant is.</p>
  <details class="intro-details">
    <summary>Uitleg: LMNA en het hart, en hoe je hier zoekt</summary>
    <div class="intro-details-body">
      <section class="intro-detail-section" aria-labelledby="intro-heart-title">
        <h3 id="intro-heart-title" class="intro-detail-title">LMNA en het hart</h3>
        <p class="intro-detail-text">Een mutatie in LMNA kan het hart op verschillende manieren beïnvloeden. Daarom staan er veel verschillende studies en artikelen in dit overzicht: lang niet alles is voor jou relevant.</p>
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
    <div class="stat-num" id="stat-news">…</div>
    <div class="stat-label">Nieuws</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-pubs">…</div>
    <div class="stat-label">Publicaties</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-trials">…</div>
    <div class="stat-label">Studies</div>
  </div>
  <div class="stat">
    <div class="stat-num green" id="stat-recruiting">…</div>
    <div class="stat-label">Werving open</div>
  </div>
</div>
<div class="dashboard-split">
<section class="insights" aria-labelledby="insights-heading">
  <h2 id="insights-heading">Waar begin je?</h2>
  <p class="insights-sub">Korte oriëntatie in gewone taal; geen medisch advies. Links in de tabs vind je het nieuws, de publicaties en de studies.</p>
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
    <button type="button" class="filter-btn active" onclick="setNewsSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
    <button type="button" class="filter-btn" onclick="setNewsSort('date', this)">Recent</button>
  </div>
  <div class="chip-row" aria-label="Snelfilter nieuws">
    <span class="chip-label">Snelfilter</span>
    <button type="button" class="chip" onclick="quickNews('lamin')">LMNA / lamin</button>
    <button type="button" class="chip" onclick="quickNews('cardiomyopathy')">cardiomyopathie</button>
    <button type="button" class="chip" onclick="quickNews('dilated')">DCM</button>
    <button type="button" class="chip" onclick="quickNews('conduction')">geleiding</button>
    <button type="button" class="chip" onclick="quickNews('')">alles tonen</button>
  </div>
  <div class="search-bar">
    <input type="text" id="search-news" placeholder="Zoekfilter…" oninput="filterNews()" autocomplete="off">
  </div>
  <div class="result-count" id="count-news"></div>
  <div class="card-grid" id="news-list"></div>
</div>

<!-- PUBLICATIONS -->
<div id="panel-publications" class="panel">
  <div class="sort-row" aria-label="Sorteer publicaties">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setPubSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
    <button type="button" class="filter-btn" onclick="setPubSort('date', this)">Recent</button>
  </div>
  <div class="chip-row" aria-label="Snelfilter publicaties">
    <span class="chip-label">Snelfilter</span>
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
  <p class="panel-hint">Een studie met status <strong>RECRUITING</strong> zoekt op dit moment deelnemers. Dat is géén aanbeveling om mee te doen; bespreek het met je arts en meld je alleen via de officiële studiepagina.</p>
  <div class="sort-row" aria-label="Sorteer studies">
    <span class="chip-label">Sorteer</span>
    <button type="button" class="filter-btn active" onclick="setTrialSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
    <button type="button" class="filter-btn" onclick="setTrialSort('date', this)">Startdatum</button>
  </div>
  <div class="chip-row" aria-label="Snelfilter studies">
    <span class="chip-label">Snelfilter</span>
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

/** Korte NL-regel voor patiënten/lezers (uit data). */
function readerNotePara(note) {
  const n = String(note ?? "").trim();
  if (!n) return "";
  return (
    '<p class="card-reader-note"><span class="card-reader-note-label">Voor lezers:</span> ' +
    escHtml(n) +
    "</p>"
  );
}

function themeBadgesOnly(labels) {
  const chips = (labels || []).map(l => `<span class="theme-chip">${escHtml(l)}</span>`).join("");
  return chips ? `<div class="card-badges">${chips}</div>` : "";
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
        `<span class="highlight-list__title">Vijf suggesties om mee te beginnen</span>` +
        `<p class="highlight-list__lead">Dit zijn vijf publicaties uit dit overzicht die vaak aansluiten op LMNA en het hart. Titels zijn meestal Engelstalig en formeel; dat hoort zo. Ze zijn automatisch gekozen op woorden in titel en tekst; open de link als je verder wilt lezen.</p>` +
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
        `<div class="count">${row.count} publicatie(s) in dit overzicht</div><ul>${ex}</ul></div>`
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
    el.innerHTML = '<div class="empty"><div class="empty-icon">🔬</div>Geen resultaten; pas zoek of filters aan.</div>';
    return;
  }
  el.innerHTML = sorted.map(p => {
    const badges = themeBadgesOnly(p.theme_labels);
    const note = readerNotePara(p.reader_note_nl);
    return `
    <div class="card">
      ${badges}
      <div class="card-header">
        <div class="card-title"><a href="${p.url}" target="_blank" rel="noopener">${p.title || "-"}</a></div>
        <div class="card-date">${p.pub_date || ""}</div>
      </div>
      ${note}
      <div class="card-meta">
        <strong>${p.journal || "-"}</strong>${p.authors ? " · " + p.authors : ""}
      </div>
      ${p.abstract ? `
        <div class="abstract" id="abs-${p.id}">${p.abstract}</div>
        <span class="toggle-abstract" onclick="toggleAbs('${p.id}', this)">▸ samenvatting studie (Engels)</span>
      ` : ""}
    </div>
  `;
  }).join("");
}

function toggleAbs(id, el) {
  const abs = document.getElementById("abs-" + id);
  abs.classList.toggle("open");
  el.textContent = abs.classList.contains("open") ? "▾ verberg samenvatting" : "▸ samenvatting studie (Engels)";
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
    el.innerHTML = '<div class="empty"><div class="empty-icon">🧪</div>Geen studies; pas filter of zoekterm.</div>';
    return;
  }
  el.innerHTML = sorted.map(t => {
    const tBadges = themeBadgesOnly(t.theme_labels);
    const tNote = readerNotePara(t.reader_note_nl);
    return `
    <div class="trial-card">
      ${tBadges}
      <div class="trial-header">
        <div class="trial-title"><a href="${t.url}" target="_blank" rel="noopener">${t.title || "-"}</a></div>
        <span class="badge ${badgeClass(t.status)}">${(t.status || "-").replace(/_/g," ")}</span>
      </div>
      ${tNote}
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
    el.innerHTML = '<div class="empty"><div class="empty-icon">📰</div>Geen nieuws; pas je zoekterm aan.</div>';
    return;
  }
  el.innerHTML = sorted.map(n => {
    const nBadges = themeBadgesOnly(n.theme_labels);
    const nNote = readerNotePara(n.reader_note_nl);
    return `
    <div class="card">
      ${nBadges}
      <div class="card-header">
        <div class="card-title"><a href="${n.url}" target="_blank" rel="noopener">${n.title || "-"}</a></div>
        <div class="card-date">${(n.pub_date || "").substring(0, 16)}</div>
      </div>
      ${nNote}
      <div class="card-meta"><strong>${n.source || "-"}</strong></div>
      ${n.summary ? `<details class="news-sum-wrap"><summary>Korte tekst bij het bericht</summary><div class="news-summary">${escHtml(n.summary)}</div></details>` : ""}
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
