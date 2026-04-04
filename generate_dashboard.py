#!/usr/bin/env python3
"""
LMNA Monitor: Dashboard Generator
Reads lmna.db and produces a self-contained dashboard.html (metadata + links;
geen abstracts of nieuwssamenvattingen in de embed).
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
        SELECT id, title, authors, journal, pub_date, url, fetched_at
        FROM publications ORDER BY pub_date DESC LIMIT 100
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
        SELECT id, title, source, pub_date, url, fetched_at
        FROM news ORDER BY fetched_at DESC LIMIT 100
    """).fetchall()
    news = [dict(row) for row in news_rows]

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
<meta name="robots" content="noindex, nofollow">
<script>(function(){var k="lmna-theme",r=document.documentElement,s=localStorage.getItem(k),l=window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches;if(s==="light"||(s!=="dark"&&l))r.setAttribute("data-theme","light");})();</script>
<title>LMNA-Monitor: overzicht</title>
<link rel="stylesheet" href="fonts/fonts.css">
<style>
  :root {
    --radius-sm: 10px;
    --radius-md: 16px;
    --radius-lg: 22px;
    --radius-pill: 9999px;
    --shadow-sm: 0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 20px rgba(0,0,0,0.22);
    --shadow-md: 0 1px 0 rgba(255,255,255,0.05) inset, 0 12px 40px rgba(0,0,0,0.35);
    --shadow-hover: 0 1px 0 rgba(255,255,255,0.06) inset, 0 16px 48px rgba(0,0,0,0.4);
    /* Merkpalet: 01 donkergroen/mint; 02 grijzen + steun; 03 accent per functie */
    --bg: #002520;
    --surface: #04332d;
    --surface2: #0a4038;
    --surface-elevated: #0f4d42;
    --border: rgba(123, 232, 178, 0.1);
    /* Primair: mint; secundair: lichtblauw (info); tertiair: lichtoranje (aandacht) */
    --accent: #7be8b2;
    --accent2: #90c8e9;
    --accent3: #f9c48b;
    --danger: #f39b8b;
    --text: #f1f2f2;
    --muted: #9b9c9d;
    --recruiting: var(--accent);
    --completed: #7e7f81;
    --active: var(--accent2);
    --prose: #dcddde;
    --prose-dim: #9b9c9d;
    --intro-grad: linear-gradient(165deg, color-mix(in srgb, var(--surface-elevated) 52%, transparent) 0%, transparent 55%);
    --insights-bg: color-mix(in srgb, var(--surface) 50%, transparent);
    --chip-accent-bg: color-mix(in srgb, var(--accent) 14%, transparent);
    --chip-accent-border: color-mix(in srgb, var(--accent) 24%, transparent);
    --filter-chip-hover-bg: color-mix(in srgb, var(--accent) 10%, transparent);
    --summary-hover-bg: color-mix(in srgb, var(--accent2) 10%, transparent);
    --tabs-bar-bg: color-mix(in srgb, var(--bg) 78%, transparent);
    --link-muted-underline: color-mix(in srgb, var(--accent2) 34%, transparent);
    --theme-chip-border: color-mix(in srgb, var(--accent2) 38%, var(--border));
    /* Thema’s (zelfde id’s als insight_engine): eigen subkleur per categorie */
    --theme-cat-dcm: #e53935;
    --theme-cat-conduction: #b69cd9;
    --theme-cat-lmna: #00a671;
    --theme-cat-therapy: #f47b20;
    --theme-cat-imaging: #90c8e9;
    --logo-glow: color-mix(in srgb, var(--accent) 18%, transparent);
    --band-text: #ffffff;
    /* Zelfde als .dashboard-split op brede schermen: intro uitlijnen met hoofdkolom */
    --dashboard-grid-cols: minmax(0, 1fr) minmax(280px, 400px);
    --site-max-width: 1200px;
    /* Zelfde als .intro-disclaimer-section (topbanner + footer) */
    --band-accent-bg: color-mix(in srgb, var(--accent) 75%, var(--bg));
    /* Night: zelfde basis als .site-shell (o.a. header); day: --band-accent-bg */
    --outer-bg: var(--bg);
    --text-base: clamp(18px, 0.24vw + 17.25px, 19px);
    --text-sm: 17px;
    --text-xs: 16px;
    --text-2xs: 15px;
    --text-micro: 14px;
    --leading-body: 1.625;
    --leading-snug: 1.35;
  }
  html[data-theme="light"] {
    color-scheme: light;
    --shadow-sm: 0 1px 0 rgba(255,255,255,0.85) inset, 0 4px 24px rgba(0, 37, 32, 0.06);
    --shadow-md: 0 1px 0 rgba(255,255,255,0.9) inset, 0 12px 40px rgba(0, 37, 32, 0.08);
    --shadow-hover: 0 1px 0 rgba(255,255,255,0.95) inset, 0 20px 50px rgba(0, 37, 32, 0.1);
    --bg: #f1f2f2;
    --surface: #ffffff;
    --surface2: #c4f2d7;
    --surface-elevated: #ffffff;
    --border: rgba(0, 86, 67, 0.12);
    --accent: #005643;
    --accent2: #004b7e;
    --accent3: #f47b20;
    --danger: #802e27;
    --text: #002520;
    --muted: #7e7f81;
    --completed: #9b9c9d;
    --prose: #002520;
    --prose-dim: #7e7f81;
    --intro-grad: linear-gradient(165deg, color-mix(in srgb, var(--surface) 92%, transparent) 0%, transparent 50%);
    --insights-bg: color-mix(in srgb, var(--surface) 72%, transparent);
    --tabs-bar-bg: color-mix(in srgb, var(--bg) 82%, transparent);
    --outer-bg: var(--band-accent-bg);
    --theme-cat-dcm: #c62828;
    --theme-cat-conduction: #372770;
    --theme-cat-lmna: #005643;
    --theme-cat-therapy: #f47b20;
    --theme-cat-imaging: #004b7e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html {
    font-size: var(--text-base);
    scroll-behavior: smooth;
    scroll-padding-top: 1rem;
    background-color: var(--outer-bg);
    min-height: 100%;
  }
  @media (prefers-reduced-motion: reduce) {
    html {
      scroll-behavior: auto;
    }
    .card,
    .stat,
    .trial-card,
    .tab,
    .theme-toggle,
    .filter-btn,
    .chip,
    .intro-details > summary,
    .abstract {
      transition-duration: 0.001ms !important;
    }
  }
  body {
    background-color: var(--outer-bg);
    color: var(--text);
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    font-size: 1rem;
    font-weight: 400;
    line-height: var(--leading-body);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }
  .skip-link {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
  .skip-link:focus,
  .skip-link:focus-visible {
    position: fixed;
    left: 16px;
    top: 16px;
    z-index: 10001;
    width: auto;
    height: auto;
    margin: 0;
    clip: auto;
    overflow: visible;
    white-space: normal;
    padding: 10px 18px;
    background: var(--surface);
    color: var(--accent2);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: var(--text-micro);
    font-weight: 600;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
    text-decoration: none;
  }
  button:focus:not(:focus-visible),
  a:focus:not(:focus-visible) {
    outline: none;
  }
  button:focus-visible,
  a:focus-visible,
  summary:focus-visible {
    outline: 2px solid var(--accent2);
    outline-offset: 2px;
  }
  .site-shell {
    max-width: var(--site-max-width);
    margin-inline: auto;
    width: 100%;
    min-height: 100vh;
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse 100% 70% at 0% -10%, color-mix(in srgb, var(--accent) 9%, transparent), transparent 52%),
      radial-gradient(ellipse 90% 55% at 100% 0%, color-mix(in srgb, var(--accent2) 7%, transparent), transparent 48%),
      radial-gradient(ellipse 70% 45% at 50% 110%, color-mix(in srgb, var(--accent3) 5%, transparent), transparent 55%);
  }
  html[data-theme="light"] .site-shell {
    background-image:
      radial-gradient(ellipse 100% 70% at 0% -10%, color-mix(in srgb, var(--accent) 6%, transparent), transparent 52%),
      radial-gradient(ellipse 90% 55% at 100% 0%, color-mix(in srgb, var(--accent2) 5%, transparent), transparent 48%),
      radial-gradient(ellipse 70% 45% at 50% 110%, color-mix(in srgb, var(--accent3) 4%, transparent), transparent 55%);
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
    text-shadow: 0 0 48px var(--logo-glow);
  }
  html[data-theme="light"] .logo-block h1 {
    text-shadow: none;
  }
  .logo-block p {
    color: var(--accent);
    margin-top: 10px;
    font-size: var(--text-xs);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 400;
    letter-spacing: 0.01em;
    text-transform: none;
    line-height: 1.55;
    max-width: 38rem;
  }
  .last-updated {
    color: var(--muted);
    font-size: var(--text-micro);
    text-align: right;
    font-family: 'DM Mono', monospace;
    margin-top: 14px;
    width: 100%;
  }
  .last-updated span {
    display: block;
    color: var(--accent);
    font-size: var(--text-micro);
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
  .intro-lead-align {
    display: block;
  }
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
    font-size: var(--text-xs);
  }
  .intro-disclaimer-section {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 48px;
    border-bottom: 1px solid color-mix(in srgb, var(--accent) 35%, var(--border));
    background: var(--band-accent-bg);
    text-align: center;
    box-sizing: border-box;
  }
  .intro-disclaimer-section .intro-disclaimer {
    flex: 0 1 auto;
    width: 100%;
    font-size: var(--text-xs);
    font-weight: 500;
    line-height: 1.55;
    letter-spacing: 0;
    text-transform: none;
    color: var(--band-text);
    max-width: 56rem;
    margin: 0;
    padding: 0;
    border: none;
  }
  /* Smalle banner onder de header: waarschuwingsstrip in hoofdletters */
  .intro-disclaimer-section:not(.intro-disclaimer-section--footer) > .intro-disclaimer {
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    font-weight: 700 !important;
    font-size: var(--text-2xs) !important;
    line-height: 1.45 !important;
    max-width: 100% !important;
    font-variant: normal;
  }
  .intro-disclaimer-section--footer {
    flex-direction: column;
    gap: 14px;
    align-items: center;
    border-top: 1px solid color-mix(in srgb, var(--accent) 35%, var(--border));
    border-bottom: none;
    padding-top: 40px;
    padding-bottom: 40px;
  }
  .intro-disclaimer-section--footer > .intro-disclaimer {
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-variant: normal;
  }
  .intro-disclaimer-section--footer > .intro-disclaimer.intro-disclaimer--medical {
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    font-size: var(--text-2xs) !important;
    line-height: 1.45 !important;
  }
  .intro-disclaimer-section--footer .intro-disclaimer a {
    color: inherit;
    text-decoration: underline;
  }
  .intro-lead {
    margin-bottom: 0;
    color: var(--prose);
    font-size: var(--text-xs);
    line-height: 1.55;
  }
  .intro-details {
    margin-top: 16px;
    border: 0;
  }
  .intro-details > summary {
    cursor: pointer;
    color: var(--accent2);
    font-size: var(--text-xs);
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
    font-size: var(--text-2xs);
    color: var(--muted);
    line-height: 1.55;
    margin: 0 0 12px;
  }
  .intro-detail-list {
    margin: 0;
    padding-left: 1.25rem;
    font-size: var(--text-2xs);
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
    font-size: var(--text-2xs);
    font-weight: 500;
    color: var(--text);
    margin: 0 0 8px;
    line-height: 1.35;
  }
  .intro-search-hint dd {
    margin: 0;
    font-size: var(--text-micro);
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
    font-size: var(--text-micro);
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    margin-right: 4px;
  }
  .intro-search-term {
    font-family: 'DM Mono', monospace;
    font-size: var(--text-micro);
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
    font-size: var(--text-micro);
    letter-spacing: 0.1em;
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
    background: transparent;
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
    font-size: var(--text-xs);
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
  .panel[hidden] {
    display: none !important;
  }
  .panel:not([hidden]) {
    display: block;
  }

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
    font-size: var(--text-sm);
    outline: none;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }
  .search-bar input:focus-visible {
    border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
    box-shadow: var(--shadow-md), 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent);
    outline: none;
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
  .title-link-wrap {
    display: inline-flex;
    align-items: baseline;
    gap: 0.4em;
    flex-wrap: wrap;
    max-width: 100%;
    min-width: 0;
  }
  .title-link-wrap > a {
    min-width: 0;
  }
  .ext-link-icon {
    flex-shrink: 0;
    color: var(--muted);
    opacity: 0.72;
    display: inline-flex;
    vertical-align: middle;
  }
  .ext-link-icon svg {
    display: block;
  }
  .card-title a { color: inherit; text-decoration: none; }
  .card-title a:hover { color: var(--accent); }
  .card-date {
    color: var(--muted);
    font-size: var(--text-micro);
    white-space: nowrap;
    flex-shrink: 0;
  }
  .card-meta {
    color: var(--muted);
    font-size: var(--text-micro);
    font-family: 'DM Mono', monospace;
    margin-bottom: 10px;
  }
  .card-meta strong { color: var(--accent2); }
  .abstract {
    color: var(--prose-dim);
    font-size: var(--text-2xs);
    font-family: 'Plus Jakarta Sans', sans-serif;
    line-height: 1.75;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }
  .abstract.open { max-height: 400px; }
  .toggle-abstract {
    color: var(--muted);
    font-size: var(--text-micro);
    cursor: pointer;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 8px;
    display: inline-block;
  }
  .toggle-abstract:hover { color: var(--accent); }

  /* BADGES */
  .badge {
    display: inline-block;
    padding: 5px 11px;
    border-radius: var(--radius-pill);
    font-size: var(--text-micro);
    letter-spacing: 0.08em;
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
  .trial-title .title-link-wrap a:hover { color: var(--accent2); }
  .trial-title a { color: inherit; text-decoration: none; }
  .trial-title a:hover { color: var(--accent2); }
  .trial-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: var(--text-micro); font-family: 'DM Mono', monospace; color: var(--muted); }
  .trial-meta span strong { color: var(--text); }

  /* EMPTY */
  .empty {
    text-align: center;
    padding: 80px 20px;
    color: var(--muted);
  }
  .empty-icon {
    margin-bottom: 16px;
    color: var(--muted);
    display: flex;
    justify-content: center;
  }
  .empty-icon svg {
    width: 3rem;
    height: 3rem;
    opacity: 0.55;
  }

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
    font-size: var(--text-micro);
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

  /* RESULT COUNT (waarden worden in toolbar gezet) */
  .result-count { color: var(--muted); font-size: var(--text-micro); }

  /* QUICK SEARCH CHIPS */
  .chip-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
  }
  .chip-label {
    font-size: var(--text-micro);
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
    font-size: var(--text-micro);
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
  /* Snelfilter: rust = vroeger hover; hover = vroeger rust (themafilter / “Alles tonen” ongewijzigd) */
  .chip-row:not(.theme-filter-row) .chip:not(.theme-chip):not(.chip--all):not(.active):not([aria-pressed="true"]) {
    background: var(--filter-chip-hover-bg);
    border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
  }
  .chip-row:not(.theme-filter-row) .chip:not(.theme-chip):not(.chip--all):not(.active):not([aria-pressed="true"]):hover {
    background: var(--surface2);
    border-color: var(--border);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.active,
  .chip[aria-pressed="true"] {
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
    color: var(--accent);
    background: var(--filter-chip-hover-bg);
    box-shadow: var(--shadow-md);
    transform: none;
  }
  /* Neutraal: “Alles tonen” / reset (geen accent) */
  .chip.chip--all {
    border: 1px solid var(--border);
    color: var(--text);
    background: var(--surface2);
    box-shadow: none;
  }
  .chip.chip--all:hover {
    border-color: color-mix(in srgb, var(--muted) 38%, var(--border));
    background: color-mix(in srgb, var(--surface) 65%, var(--surface2));
    color: var(--text);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.chip--all.active,
  .chip.chip--all[aria-pressed="true"] {
    border-color: color-mix(in srgb, var(--muted) 48%, var(--border));
    color: var(--text);
    background: var(--surface);
    box-shadow: var(--shadow-md);
    transform: none;
  }

  /* Filterblokken: zoeken (veld + snelkeuze) vs thema (taxonomy) */
  .filter-section {
    margin-bottom: 0;
  }
  .filter-section--search {
    /* Donkerder dan --bg: 10% zwart voor subtiele diepte */
    background: color-mix(in srgb, var(--bg) 90%, #000 10%);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 16px 18px 18px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-sm);
  }
  .filter-section--search .search-bar {
    margin-bottom: 12px;
  }
  .filter-section--search .chip-row {
    margin-bottom: 14px;
  }
  .filter-section--search .filter-row {
    margin-top: 0;
    margin-bottom: 0;
  }
  .filter-section__title {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 10px;
    line-height: 1.3;
  }
  .filter-section__hint {
    font-size: var(--text-micro);
    color: var(--muted);
    margin: 0 0 12px;
    line-height: 1.45;
    max-width: 42rem;
  }
  .filter-section--theme {
    margin-top: 4px;
    margin-bottom: 8px;
    padding-top: 18px;
    border-top: 1px solid var(--border);
  }
  .filter-section--theme .filter-section__title {
    margin-bottom: 12px;
  }
  .theme-filter-row {
    padding-top: 0;
    margin-top: 0;
    margin-bottom: 0;
    border-top: none;
  }

  .panel-hint {
    font-size: var(--text-micro);
    color: var(--muted);
    margin-bottom: 12px;
    max-width: 40rem;
    line-height: 1.5;
  }

  .news-sum-wrap {
    margin-top: 8px;
    border: 0;
  }
  .news-sum-wrap summary {
    cursor: pointer;
    color: var(--accent2);
    font-size: var(--text-micro);
    font-weight: 500;
    list-style: none;
    user-select: none;
  }
  .news-sum-wrap summary::-webkit-details-marker { display: none; }
  .news-sum-wrap .news-summary {
    color: var(--prose-dim);
    font-size: var(--text-micro);
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
    font-size: var(--text-micro);
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 14px;
    max-width: 48rem;
  }
  .insights-method {
    font-size: var(--text-micro);
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
    font-size: var(--text-micro);
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
    font-size: var(--text-2xs);
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
  .theme-cluster[data-theme="dcm"] { border-left: 3px solid var(--theme-cat-dcm); }
  .theme-cluster[data-theme="conduction"] { border-left: 3px solid var(--theme-cat-conduction); }
  .theme-cluster[data-theme="lmna"] { border-left: 3px solid var(--theme-cat-lmna); }
  .theme-cluster[data-theme="therapy"] { border-left: 3px solid var(--theme-cat-therapy); }
  .theme-cluster[data-theme="imaging"] { border-left: 3px solid var(--theme-cat-imaging); }
  .theme-cluster h3,
  .theme-cluster-heading {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--accent2);
    margin-bottom: 4px;
  }
  .theme-cluster-heading {
    margin-top: 0;
  }
  .theme-cluster-title-btn {
    font: inherit;
    color: inherit;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    text-align: left;
    text-decoration: underline;
    text-decoration-style: dashed;
    text-underline-offset: 3px;
  }
  .theme-cluster-title-btn:hover {
    filter: brightness(1.12);
  }
  .theme-cluster[data-theme="dcm"] .theme-cluster-title-btn { color: var(--theme-cat-dcm); }
  .theme-cluster[data-theme="conduction"] .theme-cluster-title-btn { color: var(--theme-cat-conduction); }
  .theme-cluster[data-theme="lmna"] .theme-cluster-title-btn { color: var(--theme-cat-lmna); }
  .theme-cluster[data-theme="therapy"] .theme-cluster-title-btn { color: var(--theme-cat-therapy); }
  .theme-cluster[data-theme="imaging"] .theme-cluster-title-btn { color: var(--theme-cat-imaging); }
  .theme-cluster-blurb {
    font-size: var(--text-micro);
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 8px;
  }
  .theme-cluster .count {
    font-family: 'DM Mono', monospace;
    font-size: var(--text-micro);
    color: var(--muted);
    margin-bottom: 8px;
  }
  .theme-cluster ul {
    margin: 0;
    padding-left: 1.15rem;
    color: var(--prose-dim);
    font-size: var(--text-2xs);
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
    font-size: var(--text-micro);
    color: var(--muted);
    line-height: 1.45;
    margin: 0 0 10px;
  }
  .highlight-list ol {
    margin: 0;
    padding-left: 1.2rem;
    color: var(--prose);
    font-size: var(--text-2xs);
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
    border-bottom: 1px solid var(--link-muted-underline);
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
  .sort-row .chip-label {
    color: var(--muted);
    font-weight: 500;
  }
  .panel-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px 20px;
    flex-wrap: wrap;
    margin-top: 20px;
    margin-bottom: 16px;
    padding-top: 20px;
    border-top: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  }
  .panel-toolbar .result-count {
    margin-top: 0;
    margin-bottom: 0;
    flex: 1 1 auto;
    min-width: min(100%, 12rem);
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px 10px;
    font-size: var(--text-micro);
    color: var(--muted);
  }
  .result-count__label {
    font-weight: 600;
    color: var(--prose-dim);
    letter-spacing: 0.02em;
  }
  .result-count__value {
    font-weight: 700;
    color: var(--text);
    font-size: var(--text-sm);
  }
  .panel-toolbar .sort-row {
    margin-bottom: 0;
    margin-left: auto;
    justify-content: flex-end;
    flex: 0 1 auto;
  }
  .card-reader-note {
    font-size: var(--text-micro);
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
  /* Inline thema-tags (span.theme-chip, o.a. nieuwskaarten): volle kleur, wit, geen rand */
  .theme-chip:not(.chip) {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    border: none;
    padding: 3px 9px;
    border-radius: var(--radius-pill);
    margin-right: 3px;
    margin-top: 3px;
    line-height: 1.25;
    vertical-align: middle;
  }
  .theme-chip[data-theme="dcm"] {
    background: var(--theme-cat-dcm);
  }
  .theme-chip[data-theme="conduction"] {
    background: var(--theme-cat-conduction);
  }
  .theme-chip[data-theme="lmna"] {
    background: var(--theme-cat-lmna);
  }
  .theme-chip[data-theme="therapy"] {
    background: var(--theme-cat-therapy);
  }
  .theme-chip[data-theme="imaging"] {
    background: var(--theme-cat-imaging);
  }
  /* Thema-filter: volle categoriekleur, wit — niet op .chip--all (die volgt .chip.chip--all) */
  .chip.theme-chip:not(.chip--all) {
    border: none;
    color: #fff;
    box-shadow: none;
  }
  .chip.theme-chip:not(.chip--all):hover {
    border: none;
  }
  .chip.theme-chip[data-theme-id="dcm"] {
    background: var(--theme-cat-dcm);
  }
  .chip.theme-chip[data-theme-id="dcm"]:hover {
    background: color-mix(in srgb, var(--theme-cat-dcm) 82%, #000);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.theme-chip[data-theme-id="dcm"].active,
  .chip.theme-chip[data-theme-id="dcm"][aria-pressed="true"] {
    background: color-mix(in srgb, var(--theme-cat-dcm) 68%, #000);
    color: #fff;
    box-shadow: var(--shadow-md);
    transform: none;
  }
  .chip.theme-chip[data-theme-id="conduction"] {
    background: var(--theme-cat-conduction);
  }
  .chip.theme-chip[data-theme-id="conduction"]:hover {
    background: color-mix(in srgb, var(--theme-cat-conduction) 82%, #000);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.theme-chip[data-theme-id="conduction"].active,
  .chip.theme-chip[data-theme-id="conduction"][aria-pressed="true"] {
    background: color-mix(in srgb, var(--theme-cat-conduction) 68%, #000);
    color: #fff;
    box-shadow: var(--shadow-md);
    transform: none;
  }
  .chip.theme-chip[data-theme-id="lmna"] {
    background: var(--theme-cat-lmna);
  }
  .chip.theme-chip[data-theme-id="lmna"]:hover {
    background: color-mix(in srgb, var(--theme-cat-lmna) 82%, #000);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.theme-chip[data-theme-id="lmna"].active,
  .chip.theme-chip[data-theme-id="lmna"][aria-pressed="true"] {
    background: color-mix(in srgb, var(--theme-cat-lmna) 68%, #000);
    color: #fff;
    box-shadow: var(--shadow-md);
    transform: none;
  }
  .chip.theme-chip[data-theme-id="therapy"] {
    background: var(--theme-cat-therapy);
  }
  .chip.theme-chip[data-theme-id="therapy"]:hover {
    background: color-mix(in srgb, var(--theme-cat-therapy) 82%, #000);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.theme-chip[data-theme-id="therapy"].active,
  .chip.theme-chip[data-theme-id="therapy"][aria-pressed="true"] {
    background: color-mix(in srgb, var(--theme-cat-therapy) 68%, #000);
    color: #fff;
    box-shadow: var(--shadow-md);
    transform: none;
  }
  .chip.theme-chip[data-theme-id="imaging"] {
    background: var(--theme-cat-imaging);
  }
  .chip.theme-chip[data-theme-id="imaging"]:hover {
    background: color-mix(in srgb, var(--theme-cat-imaging) 82%, #000);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }
  .chip.theme-chip[data-theme-id="imaging"].active,
  .chip.theme-chip[data-theme-id="imaging"][aria-pressed="true"] {
    background: color-mix(in srgb, var(--theme-cat-imaging) 68%, #000);
    color: #fff;
    box-shadow: var(--shadow-md);
    transform: none;
  }
  .card-badges { margin-bottom: 8px; }

  /* Insights + tabs/inhoud: twee kolommen op brede schermen */
  .dashboard-split {
    display: block;
  }
  .dashboard-split__main {
    min-width: 0;
    /* Zelfde vlak als .card (o.a. card-meta staat op dit oppervlak) */
    background: var(--surface);
  }
  @media (min-width: 960px) {
    .intro-lead-align {
      display: grid;
      grid-template-columns: var(--dashboard-grid-cols);
      align-items: start;
    }
    .intro-lead-align .intro-lead {
      grid-column: 1;
      min-width: 0;
    }
    .dashboard-split {
      display: grid;
      grid-template-columns: var(--dashboard-grid-cols);
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
    .intro-disclaimer-section--footer {
      padding: 40px 20px;
    }
    .intro { padding: 22px 20px; }
    .dashboard-split {
      display: flex;
      flex-direction: column;
    }
    .dashboard-split__main {
      order: 1;
    }
    .insights {
      order: 2;
      border-top: 1px solid var(--border);
      padding: 24px 20px 28px;
    }
    .card-title,
    .trial-title {
      font-weight: 500;
    }
    .stats-bar {
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      padding: 16px 20px 22px;
    }
    .stat { padding: 18px 16px; }
    .tabs { padding: 0 20px; min-height: 52px; overflow-x: auto; flex-wrap: nowrap; }
    .filter-section--theme { padding-top: 14px; }
    main { padding: 22px 20px 36px; }
  }
</style>
</head>
<body>
<a class="skip-link" href="#main-content">Ga naar inhoud</a>

<div class="site-shell">
<header>
  <div class="logo-block">
    <div class="logo-heading">
      <h1>LMNA-Monitor</h1>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-pressed="true" aria-label="Schakel naar licht thema">
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
  <div class="intro-lead-align">
  <p class="intro-lead">Voor patiënten en gezinnen die LMNA-bronnen op één plek willen. Deze pagina toont het resultaat van een dagelijks geautomatiseerde zoekactie naar LMNA-bronnen: nieuws, publicaties en studies. Binnen deze resultaten kan verder gezocht worden naar wat voor jou relevant is.</p>
  </div>
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
<section class="insights" id="insights" aria-labelledby="insights-heading">
  <h2 id="insights-heading">Waar begin je?</h2>
  <p class="insights-sub">Korte oriëntatie in gewone taal; geen medisch advies. Links in de tabs vind je het nieuws, de publicaties en de studies.</p>
  <p class="insights-method" id="insights-method"></p>
  <div id="insights-body"></div>
</section>

<div class="dashboard-split__main">
<div class="tabs" role="tablist" aria-label="Nieuws, publicaties en studies">
  <button type="button" class="tab active" role="tab" id="tab-news" data-tab="news" aria-selected="true" aria-controls="panel-news" tabindex="0" onclick="switchTab('news', this)">Nieuws</button>
  <button type="button" class="tab" role="tab" id="tab-publications" data-tab="publications" aria-selected="false" aria-controls="panel-publications" tabindex="-1" onclick="switchTab('publications', this)">Publicaties</button>
  <button type="button" class="tab" role="tab" id="tab-trials" data-tab="trials" aria-selected="false" aria-controls="panel-trials" tabindex="-1" onclick="switchTab('trials', this)">Studies</button>
</div>

<main id="main-content" tabindex="-1">

<!-- NEWS -->
<div id="panel-news" class="panel" role="tabpanel" aria-labelledby="tab-news">
  <p class="panel-hint">Bronnen: officiële RSS-feeds (o.a. PubMed-zoekalerts, ClinicalTrials.gov, Circulation, open access). Geen commercieel nieuwsaggregaat.</p>
  <div class="filter-section filter-section--search" aria-labelledby="filter-search-news-title">
    <h3 class="filter-section__title" id="filter-search-news-title">Zoek in de resultaten</h3>
    <div class="search-bar">
      <input type="text" id="search-news" placeholder="Typ om te zoeken in titel of tekst…" oninput="filterNews()" autocomplete="off" aria-describedby="filter-search-news-hint">
    </div>
    <p class="filter-section__hint" id="filter-search-news-hint">De knoppen hieronder vullen het zoekveld met een veelgebruikte term.</p>
    <div class="chip-row" aria-label="Veelgebruikte zoektermen" aria-describedby="filter-search-news-hint">
      <span class="chip-label">Snel zoeken</span>
      <button type="button" class="chip chip--all" onclick="quickNews('')">Alles tonen</button>
      <button type="button" class="chip" onclick="quickNews('lamin')">LMNA / lamin</button>
      <button type="button" class="chip" onclick="quickNews('cardiomyopathy')">cardiomyopathie</button>
      <button type="button" class="chip" onclick="quickNews('dilated')">DCM</button>
      <button type="button" class="chip" onclick="quickNews('conduction')">geleiding</button>
    </div>
  </div>
  <div class="filter-section filter-section--theme" aria-labelledby="filter-theme-news-title">
    <h3 class="filter-section__title" id="filter-theme-news-title">Filter op thema</h3>
    <div class="chip-row theme-filter-row" aria-label="Filter op onderwerp"></div>
  </div>
  <div class="panel-toolbar">
    <div class="result-count" id="count-news">
      <span class="result-count__label">Resultaat</span>
      <span class="result-count__value" id="count-news-value"></span>
    </div>
    <div class="sort-row" aria-label="Sorteer nieuws">
      <span class="chip-label">Sorteer</span>
      <button type="button" class="filter-btn active" aria-pressed="true" onclick="setNewsSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
      <button type="button" class="filter-btn" aria-pressed="false" onclick="setNewsSort('date', this)">Recent</button>
    </div>
  </div>
  <div class="card-grid" id="news-list"></div>
</div>

<!-- PUBLICATIONS -->
<div id="panel-publications" class="panel" role="tabpanel" aria-labelledby="tab-publications" hidden>
  <div class="filter-section filter-section--search" aria-labelledby="filter-search-pubs-title">
    <h3 class="filter-section__title" id="filter-search-pubs-title">Zoeken in titel, auteurs en tijdschrift</h3>
    <div class="search-bar">
      <input type="text" id="search-pubs" placeholder="Typ om te zoeken in titel, auteurs of tijdschrift…" oninput="filterPubs()" autocomplete="off" aria-describedby="filter-search-pubs-hint">
    </div>
    <p class="filter-section__hint" id="filter-search-pubs-hint">De knoppen hieronder vullen het zoekveld met een veelgebruikte term.</p>
    <div class="chip-row" aria-label="Veelgebruikte zoektermen" aria-describedby="filter-search-pubs-hint">
      <span class="chip-label">Snel zoeken</span>
      <button type="button" class="chip chip--all" onclick="quickPub('')">Alles tonen</button>
      <button type="button" class="chip" onclick="quickPub('dilated cardiomyopathy')">DCM</button>
      <button type="button" class="chip" onclick="quickPub('LMNA')">LMNA</button>
      <button type="button" class="chip" onclick="quickPub('heart failure')">hartfalen</button>
      <button type="button" class="chip" onclick="quickPub('conduction')">geleiding</button>
      <button type="button" class="chip" onclick="quickPub('arrhythmia')">aritmie</button>
      <button type="button" class="chip" onclick="quickPub('pacing')">pacemaker</button>
    </div>
  </div>
  <div class="filter-section filter-section--theme" aria-labelledby="filter-theme-pubs-title">
    <h3 class="filter-section__title" id="filter-theme-pubs-title">Filter op thema</h3>
    <div class="chip-row theme-filter-row" aria-label="Filter op onderwerp"></div>
  </div>
  <div class="panel-toolbar">
    <div class="result-count" id="count-pubs">
      <span class="result-count__label">Resultaat</span>
      <span class="result-count__value" id="count-pubs-value"></span>
    </div>
    <div class="sort-row" aria-label="Sorteer publicaties">
      <span class="chip-label">Sorteer</span>
      <button type="button" class="filter-btn active" aria-pressed="true" onclick="setPubSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
      <button type="button" class="filter-btn" aria-pressed="false" onclick="setPubSort('date', this)">Recent</button>
    </div>
  </div>
  <div class="card-grid" id="pubs-list"></div>
</div>

<!-- TRIALS -->
<div id="panel-trials" class="panel" role="tabpanel" aria-labelledby="tab-trials" hidden>
  <p class="panel-hint">Een studie met status <strong>RECRUITING</strong> zoekt op dit moment deelnemers. Dat is géén aanbeveling om mee te doen; bespreek het met je arts en meld je alleen via de officiële studiepagina.</p>
  <div class="filter-section filter-section--search" aria-labelledby="filter-search-trials-title">
    <h3 class="filter-section__title" id="filter-search-trials-title">Zoeken in titel, aandoening en interventie</h3>
    <div class="search-bar">
      <input type="text" id="search-trials" placeholder="Typ om te zoeken in titel, aandoening of interventie…" oninput="filterTrials()" autocomplete="off" aria-describedby="filter-search-trials-hint">
    </div>
    <p class="filter-section__hint" id="filter-search-trials-hint">De knoppen hieronder vullen het zoekveld met een veelgebruikte term. Daaronder filter je op studiestatus.</p>
    <div class="chip-row" aria-label="Veelgebruikte zoektermen" aria-describedby="filter-search-trials-hint">
      <span class="chip-label">Snel zoeken</span>
      <button type="button" class="chip chip--all" onclick="quickTrial('')">Alles tonen</button>
      <button type="button" class="chip" onclick="quickTrial('LMNA')">LMNA</button>
      <button type="button" class="chip" onclick="quickTrial('cardiomyopathy')">cardiomyopathie</button>
      <button type="button" class="chip" onclick="quickTrial('dilated')">DCM</button>
      <button type="button" class="chip" onclick="quickTrial('conduction')">geleiding</button>
      <button type="button" class="chip" onclick="quickTrial('lamin')">lamin</button>
    </div>
    <div class="filter-row" id="trial-filters"></div>
  </div>
  <div class="filter-section filter-section--theme" aria-labelledby="filter-theme-trials-title">
    <h3 class="filter-section__title" id="filter-theme-trials-title">Filter op thema</h3>
    <div class="chip-row theme-filter-row" aria-label="Filter op onderwerp"></div>
  </div>
  <div class="panel-toolbar">
    <div class="result-count" id="count-trials">
      <span class="result-count__label">Resultaat</span>
      <span class="result-count__value" id="count-trials-value"></span>
    </div>
    <div class="sort-row" aria-label="Sorteer studies">
      <span class="chip-label">Sorteer</span>
      <button type="button" class="filter-btn active" aria-pressed="true" onclick="setTrialSort('relevance', this)" title="Items die het beste aansluiten op LMNA en het hart eerst">Best passend eerst</button>
      <button type="button" class="filter-btn" aria-pressed="false" onclick="setTrialSort('date', this)">Startdatum</button>
    </div>
  </div>
  <div class="trial-grid" id="trials-list"></div>
</div>

</main>
</div>
</div>

<section class="intro-disclaimer-section intro-disclaimer-section--footer" aria-label="Afsluiting: bronnen, disclaimer en contact">
  <p class="intro-disclaimer">Deze site verzamelt alleen titels en links naar openbaar beschikbare artikelen en klinische studies over LMNA-gerelateerde aandoeningen, samengesteld uit openbare RSS-feeds van databases en uitgevers (geen volledige artikelen of nieuwssamenvattingen hierin). Voor de volledige inhoud volg je de link naar de uitgever of officiële studiepagina. Rechten op de onderliggende inhoud berusten bij de respectieve rechthebbenden.</p>
  <p class="intro-disclaimer intro-disclaimer--medical">Dit is geen medisch advies. Raadpleeg altijd een arts voor persoonlijke medische vragen.</p>
  <p class="intro-disclaimer">Vragen of verwijderverzoeken: <a href="mailto:lmna.monitor@gmail.com">lmna.monitor@gmail.com</a></p>
</section>
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
    btn.setAttribute("aria-pressed", light ? "false" : "true");
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

var EXT_LINK_ICON =
  '<span class="ext-link-icon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></span>';

var EMPTY_STATE_ICON =
  '<div class="empty-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="8" y1="11" x2="14" y2="11"/></svg></div>';

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

function themeBadgesOnly(themeIds, labels) {
  const ids = themeIds || [];
  const labs = labels || [];
  const chips = labs
    .map((l, i) => {
      const tid = (ids[i] != null ? String(ids[i]) : "").trim();
      const attr = tid ? ` data-theme="${escAttr(tid)}"` : "";
      return `<span class="theme-chip"${attr}>${escHtml(l)}</span>`;
    })
    .join("");
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
        `<p class="highlight-list__lead">Dit zijn vijf publicaties uit dit overzicht die vaak aansluiten op LMNA en het hart. Titels zijn meestal Engelstalig en formeel; dat hoort zo. Ze zijn automatisch gekozen op woorden in titel en tijdschrift; open de link als je verder wilt lezen.</p>` +
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
        `<div class="theme-cluster" data-theme="${escAttr(row.id)}"><h3 class="theme-cluster-heading"><button type="button" class="theme-cluster-title-btn" data-theme-id="${escAttr(row.id)}">${escHtml(row.label)}</button></h3>${blurb}` +
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

let themeFilterId = "";

function matchesTheme(item) {
  if (!themeFilterId) return true;
  const ids = item.theme_ids || [];
  return ids.indexOf(themeFilterId) !== -1;
}

function syncThemeChipButtons() {
  document.querySelectorAll(".theme-filter-row .theme-chip").forEach(function (btn) {
    const id = btn.getAttribute("data-theme-id") || "";
    const on = themeFilterId === id;
    btn.classList.toggle("active", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
}

function setThemeFilter(id) {
  themeFilterId = id || "";
  syncThemeChipButtons();
  renderNews();
  renderPubs();
  renderTrials();
}

function buildThemeFilterRow() {
  const rows = document.querySelectorAll(".theme-filter-row");
  if (!rows.length) return;
  const opts = (DATA.insights && DATA.insights.theme_options) || [];
  const parts = [
    '<button type="button" class="chip theme-chip chip--all" data-theme-id="" aria-pressed="true">Alles tonen</button>',
  ];
  for (const o of opts) {
    parts.push(
      `<button type="button" class="chip theme-chip" data-theme-id="${escAttr(o.id)}" aria-pressed="false">${escHtml(o.label)}</button>`
    );
  }
  const html = parts.join("");
  rows.forEach(function (el) {
    el.innerHTML = html;
    el.querySelectorAll(".theme-chip").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setThemeFilter(btn.getAttribute("data-theme-id") || "");
      });
    });
  });
  syncThemeChipButtons();
}

// ── Stats ─────────────────────────────────────────────────────────────────
document.getElementById("ts").textContent = DATA.stats.last_updated;
document.getElementById("stat-pubs").textContent = DATA.stats.total_pubs;
document.getElementById("stat-trials").textContent = DATA.stats.total_trials;
document.getElementById("stat-recruiting").textContent = DATA.stats.recruiting;
document.getElementById("stat-news").textContent = DATA.stats.total_news;
renderInsights();
buildThemeFilterRow();

// ── Tabs ──────────────────────────────────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll(".panel").forEach(function (p) {
    p.hidden = p.id !== "panel-" + name;
  });
  document.querySelectorAll(".tab").forEach(function (t) {
    var selected = t === btn;
    t.classList.toggle("active", selected);
    t.setAttribute("aria-selected", selected ? "true" : "false");
    t.setAttribute("tabindex", selected ? "0" : "-1");
  });
}

(function initTabKeyboard() {
  var tablist = document.querySelector('[role="tablist"]');
  if (!tablist) return;
  tablist.addEventListener("keydown", function (e) {
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    var i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    var next = i;
    if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
    else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    else return;
    e.preventDefault();
    var tabBtn = tabs[next];
    var tabName = tabBtn.getAttribute("data-tab");
    if (tabName) switchTab(tabName, tabBtn);
    tabBtn.focus();
  });
})();

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

/** Leesbare datum voor nieuwskaarten (nl-NL), geen ruwe ISO zoals 2026-04-02T00:00. */
function formatNlNewsDate(raw) {
  const s = String(raw || "").trim();
  if (!s) return "";
  let d = new Date(s);
  if (Number.isNaN(d.getTime())) {
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  }
  if (Number.isNaN(d.getTime())) {
    return s.length > 28 ? s.slice(0, 28) + "…" : s;
  }
  return d.toLocaleDateString("nl-NL", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// ── Publications ──────────────────────────────────────────────────────────
let pubFilter = "";
let pubSort = "relevance";

function setPubSort(mode, btn) {
  pubSort = mode;
  const row = btn.closest(".sort-row");
  if (row) {
    row.querySelectorAll(".filter-btn").forEach(function (b) {
      b.classList.remove("active");
      b.setAttribute("aria-pressed", "false");
    });
  }
  btn.classList.add("active");
  btn.setAttribute("aria-pressed", "true");
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
    matchesTheme(p) &&
    ((p.title || "").toLowerCase().includes(pubFilter) ||
    (p.authors || "").toLowerCase().includes(pubFilter) ||
    (p.journal || "").toLowerCase().includes(pubFilter))
  );
  const sorted = sortPubsList(filtered);
  document.getElementById("count-pubs-value").textContent =
    `${sorted.length} / ${DATA.publications.length} publicaties`;
  const el = document.getElementById("pubs-list");
  if (!sorted.length) {
    el.innerHTML =
      '<div class="empty">' +
      EMPTY_STATE_ICON +
      "Geen resultaten; pas zoek of filters aan.</div>";
    return;
  }
  el.innerHTML = sorted.map(p => {
    const badges = themeBadgesOnly(p.theme_ids, p.theme_labels);
    const note = readerNotePara(p.reader_note_nl);
    return `
    <div class="card">
      ${badges}
      <div class="card-header">
        <div class="card-title"><span class="title-link-wrap"><a href="${escAttr(p.url)}" target="_blank" rel="noopener">${escHtml(p.title || "-")}</a>${EXT_LINK_ICON}</span></div>
        <div class="card-date">${escHtml(p.pub_date || "")}</div>
      </div>
      ${note}
      <div class="card-meta">
        <strong>${escHtml(p.journal || "-")}</strong>${p.authors ? " · " + escHtml(p.authors) : ""}
      </div>
    </div>
  `;
  }).join("");
}

// ── Trials ────────────────────────────────────────────────────────────────
let trialStatusFilter = "ALL";
let trialSearch = "";
let trialSort = "relevance";

function setTrialSort(mode, btn) {
  trialSort = mode;
  const row = btn.closest(".sort-row");
  if (row) {
    row.querySelectorAll(".filter-btn").forEach(function (b) {
      b.classList.remove("active");
      b.setAttribute("aria-pressed", "false");
    });
  }
  btn.classList.add("active");
  btn.setAttribute("aria-pressed", "true");
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
    return matchStatus && matchSearch && matchesTheme(t);
  });
  const sorted = sortTrialsList(filtered);
  document.getElementById("count-trials-value").textContent =
    `${sorted.length} / ${DATA.trials.length} studies`;
  const el = document.getElementById("trials-list");
  if (!sorted.length) {
    el.innerHTML =
      '<div class="empty">' +
      EMPTY_STATE_ICON +
      "Geen studies; pas filter of zoekterm.</div>";
    return;
  }
  el.innerHTML = sorted.map(t => {
    const tBadges = themeBadgesOnly(t.theme_ids, t.theme_labels);
    const tNote = readerNotePara(t.reader_note_nl);
    return `
    <div class="trial-card">
      ${tBadges}
      <div class="trial-header">
        <div class="trial-title"><span class="title-link-wrap"><a href="${escAttr(t.url)}" target="_blank" rel="noopener">${escHtml(t.title || "-")}</a>${EXT_LINK_ICON}</span></div>
        <span class="badge ${badgeClass(t.status)}">${escHtml((t.status || "-").replace(/_/g," "))}</span>
      </div>
      ${tNote}
      <div class="trial-meta">
        <span><strong>${escHtml(t.nct_id)}</strong></span>
        ${t.phase ? `<span>Fase: <strong>${escHtml(t.phase)}</strong></span>` : ""}
        ${t.start_date ? `<span>Start: <strong>${escHtml(t.start_date)}</strong></span>` : ""}
        ${t.primary_end ? `<span>Einde: <strong>${escHtml(t.primary_end)}</strong></span>` : ""}
        ${t.locations ? `<span>Locatie: <strong>${escHtml(t.locations)}</strong></span>` : ""}
        ${t.interventions ? `<span>Interventie: <strong>${escHtml(t.interventions)}</strong></span>` : ""}
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
  if (row) {
    row.querySelectorAll(".filter-btn").forEach(function (b) {
      b.classList.remove("active");
      b.setAttribute("aria-pressed", "false");
    });
  }
  btn.classList.add("active");
  btn.setAttribute("aria-pressed", "true");
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
    matchesTheme(n) &&
    ((n.title || "").toLowerCase().includes(newsFilter) ||
    (n.source || "").toLowerCase().includes(newsFilter))
  );
  const sorted = sortNewsList(filtered);
  document.getElementById("count-news-value").textContent =
    `${sorted.length} / ${DATA.news.length} nieuws`;
  const el = document.getElementById("news-list");
  if (!sorted.length) {
    el.innerHTML =
      '<div class="empty">' +
      EMPTY_STATE_ICON +
      "Geen nieuws; pas je zoekterm aan.</div>";
    return;
  }
  el.innerHTML = sorted.map(n => {
    const nBadges = themeBadgesOnly(n.theme_ids, n.theme_labels);
    const nNote = readerNotePara(n.reader_note_nl);
    const nd = formatNlNewsDate(n.pub_date || n.fetched_at);
    return `
    <div class="card">
      ${nBadges}
      <div class="card-header">
        <div class="card-title"><span class="title-link-wrap"><a href="${escAttr(n.url)}" target="_blank" rel="noopener">${escHtml(n.title || "-")}</a>${EXT_LINK_ICON}</span></div>
        <div class="card-date">${escHtml(nd)}</div>
      </div>
      ${nNote}
      <div class="card-meta"><strong>${escHtml(n.source || "-")}</strong></div>
    </div>
  `;
  }).join("");
}

// ── Init ──────────────────────────────────────────────────────────────────
(function initInsightThemeNav() {
  const insights = document.getElementById("insights");
  if (!insights) return;
  insights.addEventListener("click", function (e) {
    const btn = e.target.closest(".theme-cluster-title-btn");
    if (!btn) return;
    const tid = btn.getAttribute("data-theme-id");
    if (tid == null || tid === "") return;
    setThemeFilter(tid);
    const pubTab = document.getElementById("tab-publications");
    if (pubTab) switchTab("publications", pubTab);
  });
})();

renderPubs();
buildTrialFilters();
renderTrials();
renderNews();
</script>
</body>
</html>
"""

def _omit_key(records: list[dict], key: str) -> list[dict]:
    """Drop fields that must not appear in the published dashboard embed."""
    return [{k: v for k, v in r.items() if k != key} for r in records]


def generate():
    pubs, trials, news, stats = load_data()
    pubs, trials, news, insights = enrich_all(pubs, trials, news)
    payload = {
        "publications": _omit_key(pubs, "abstract"),
        "trials": trials,
        "news": _omit_key(news, "summary"),
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
