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
        "last_updated": datetime.now().strftime("%d %b %Y, %H:%M"),
    }
    con.close()
    return (
        [dict(r) for r in pubs],
        [dict(r) for r in trials],
        [dict(r) for r in news],
        stats
    )

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LMNA Cardiac Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,300&display=swap" rel="stylesheet">
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
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
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
    margin-top: 6px;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .last-updated {
    color: var(--muted);
    font-size: 11px;
    text-align: right;
  }
  .last-updated span {
    display: block;
    color: var(--accent);
    font-size: 13px;
    margin-top: 2px;
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
    font-size: 11px;
    letter-spacing: 0.12em;
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
    font-family: 'DM Mono', monospace;
    font-size: 13px;
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
    font-size: 11px;
    margin-bottom: 10px;
  }
  .card-meta strong { color: var(--accent2); }
  .abstract {
    color: #9aa39b;
    font-size: 12px;
    line-height: 1.7;
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
  .trial-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 11px; color: var(--muted); }
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
  .result-count { color: var(--muted); font-size: 11px; margin-bottom: 16px; }

  @media (max-width: 768px) {
    header { padding: 24px; }
    .stats-bar { grid-template-columns: repeat(2, 1fr); }
    .tabs { padding: 0 24px; overflow-x: auto; }
    main { padding: 24px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-block">
    <h1>LMNA Monitor</h1>
    <p>Cardiac Disease Intelligence Dashboard</p>
  </div>
  <div class="last-updated">
    last updated<span id="ts">—</span>
  </div>
</header>

<div class="stats-bar">
  <div class="stat">
    <div class="stat-num" id="stat-pubs">—</div>
    <div class="stat-label">Publications</div>
  </div>
  <div class="stat">
    <div class="stat-num green" id="stat-recruiting">—</div>
    <div class="stat-label">Recruiting Trials</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-trials">—</div>
    <div class="stat-label">Total Trials</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="stat-news">—</div>
    <div class="stat-label">News Items</div>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('publications', this)">Publications</button>
  <button class="tab" onclick="switchTab('trials', this)">Clinical Trials</button>
  <button class="tab" onclick="switchTab('news', this)">News</button>
</div>

<main>

<!-- PUBLICATIONS -->
<div id="panel-publications" class="panel active">
  <div class="search-bar">
    <input type="text" id="search-pubs" placeholder="Search titles, authors, abstracts..." oninput="filterPubs()">
  </div>
  <div class="result-count" id="count-pubs"></div>
  <div class="card-grid" id="pubs-list"></div>
</div>

<!-- TRIALS -->
<div id="panel-trials" class="panel">
  <div class="filter-row" id="trial-filters"></div>
  <div class="search-bar">
    <input type="text" id="search-trials" placeholder="Search trials..." oninput="filterTrials()">
  </div>
  <div class="result-count" id="count-trials"></div>
  <div class="trial-grid" id="trials-list"></div>
</div>

<!-- NEWS -->
<div id="panel-news" class="panel">
  <div class="search-bar">
    <input type="text" id="search-news" placeholder="Search news..." oninput="filterNews()">
  </div>
  <div class="result-count" id="count-news"></div>
  <div class="card-grid" id="news-list"></div>
</div>

</main>

<script>
const DATA = __DATA__;

// ── Stats ─────────────────────────────────────────────────────────────────
document.getElementById("ts").textContent = DATA.stats.last_updated;
document.getElementById("stat-pubs").textContent = DATA.stats.total_pubs;
document.getElementById("stat-trials").textContent = DATA.stats.total_trials;
document.getElementById("stat-recruiting").textContent = DATA.stats.recruiting;
document.getElementById("stat-news").textContent = DATA.stats.total_news;

// ── Tabs ──────────────────────────────────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
  btn.classList.add("active");
}

// ── Publications ──────────────────────────────────────────────────────────
let pubFilter = "";
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
  document.getElementById("count-pubs").textContent =
    `Showing ${filtered.length} of ${DATA.publications.length} publications`;
  const el = document.getElementById("pubs-list");
  if (!filtered.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🔬</div>No results found.</div>';
    return;
  }
  el.innerHTML = filtered.map(p => `
    <div class="card">
      <div class="card-header">
        <div class="card-title"><a href="${p.url}" target="_blank">${p.title || "—"}</a></div>
        <div class="card-date">${p.pub_date || ""}</div>
      </div>
      <div class="card-meta">
        <strong>${p.journal || "—"}</strong>${p.authors ? " · " + p.authors : ""}
      </div>
      ${p.abstract ? `
        <div class="abstract" id="abs-${p.id}">${p.abstract}</div>
        <span class="toggle-abstract" onclick="toggleAbs('${p.id}', this)">▸ show abstract</span>
      ` : ""}
    </div>
  `).join("");
}

function toggleAbs(id, el) {
  const abs = document.getElementById("abs-" + id);
  abs.classList.toggle("open");
  el.textContent = abs.classList.contains("open") ? "▾ hide abstract" : "▸ show abstract";
}

// ── Trials ────────────────────────────────────────────────────────────────
let trialStatusFilter = "ALL";
let trialSearch = "";

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
  el.innerHTML = `<button class="filter-btn active" onclick="setTrialFilter('ALL', this)">All</button>` +
    statuses.map(s => `<button class="filter-btn" onclick="setTrialFilter('${s}', this)">${s.replace(/_/g,' ')}</button>`).join("");
}

function setTrialFilter(status, btn) {
  trialStatusFilter = status;
  document.querySelectorAll("#trial-filters .filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderTrials();
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
  document.getElementById("count-trials").textContent =
    `Showing ${filtered.length} of ${DATA.trials.length} trials`;
  const el = document.getElementById("trials-list");
  if (!filtered.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">🧪</div>No trials found.</div>';
    return;
  }
  el.innerHTML = filtered.map(t => `
    <div class="trial-card">
      <div class="trial-header">
        <div class="trial-title"><a href="${t.url}" target="_blank">${t.title || "—"}</a></div>
        <span class="badge ${badgeClass(t.status)}">${(t.status || "—").replace(/_/g," ")}</span>
      </div>
      <div class="trial-meta">
        <span><strong>${t.nct_id}</strong></span>
        ${t.phase ? `<span>Phase: <strong>${t.phase}</strong></span>` : ""}
        ${t.start_date ? `<span>Start: <strong>${t.start_date}</strong></span>` : ""}
        ${t.primary_end ? `<span>End: <strong>${t.primary_end}</strong></span>` : ""}
        ${t.locations ? `<span>📍 ${t.locations}</span>` : ""}
        ${t.interventions ? `<span>💊 ${t.interventions}</span>` : ""}
      </div>
    </div>
  `).join("");
}

// ── News ──────────────────────────────────────────────────────────────────
let newsFilter = "";
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
  document.getElementById("count-news").textContent =
    `Showing ${filtered.length} of ${DATA.news.length} news items`;
  const el = document.getElementById("news-list");
  if (!filtered.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">📰</div>No news found.</div>';
    return;
  }
  el.innerHTML = filtered.map(n => `
    <div class="card">
      <div class="card-header">
        <div class="card-title"><a href="${n.url}" target="_blank">${n.title || "—"}</a></div>
        <div class="card-date">${(n.pub_date || "").substring(0, 16)}</div>
      </div>
      <div class="card-meta"><strong>${n.source || "—"}</strong></div>
      ${n.summary ? `<div style="color:#9aa39b;font-size:12px;line-height:1.7">${n.summary}</div>` : ""}
    </div>
  `).join("");
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
    data_js = json.dumps({"publications": pubs, "trials": trials, "news": news, "stats": stats},
                         ensure_ascii=False, default=str)
    html = HTML_TEMPLATE.replace("__DATA__", data_js)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard written to: {OUT_PATH}")
    print(f"   {stats['total_pubs']} publications · {stats['total_trials']} trials · {stats['total_news']} news")

if __name__ == "__main__":
    generate()
