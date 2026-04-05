#!/usr/bin/env python3
"""
LMNA Monitor: Dashboard Generator
Reads lmna.db and produces dashboard.html (metadata + links; styles via /site.css;
geen abstracts of nieuwssamenvattingen in de embed).
Run after scraper.py: python3 generate_dashboard.py
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

from insight_engine import enrich_all

# Zelfde YYYY-Mon-stijl als publicatiekaarten (pub_date uit scraper / PubMed).
_EN_MONTH = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _format_last_updated(dt: datetime) -> str:
    return f"{dt.year}-{_EN_MONTH[dt.month - 1]}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"


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
        "last_updated": _format_last_updated(datetime.now()),
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
<!-- Preload: zelfde origin + crossorigin zodat ze niet dubbel worden gemist t.o.v. @font-face (geen system-ui/sans-serif → Roboto) -->
<link rel="preload" href="/fonts/plus-jakarta-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/plus-jakarta-sans-latin-ext.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/fonts/fonts.css">
<link rel="stylesheet" href="/site.css">
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
  <p class="intro-lead">Voor onderzoekers, patiënten en geïnteresseerden die LMNA-bronnen op één plek willen. Deze pagina toont het resultaat van een dagelijks geautomatiseerde zoekactie naar LMNA-bronnen: nieuws, publicaties en studies. Binnen deze resultaten kan verder gezocht worden naar wat voor jou relevant is.</p>
  <p class="intro-lead intro-lead--scope">Deze site is een hulpmiddel om op de hoogte te blijven; het is geen volledig overzicht van alles wat ooit over LMNA is gepubliceerd. Binnen vastgelegde zoektermen en tijdsvensters worden automatisch treffers verzameld; er kunnen relevante artikelen of studies ontbreken.</p>
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
      <section class="intro-detail-section" aria-labelledby="intro-scope-title">
        <h3 id="intro-scope-title" class="intro-detail-title">Wat je hier wél en niet vindt</h3>
        <p class="intro-detail-text">Dit overzicht is bedoeld als signaal, niet als uitputtende bron. Zo werkt de verzameling:</p>
        <ul class="intro-detail-list">
          <li><strong>Publicaties</strong> komen uit een PubMed-zoekopdracht met een beperkt tijdvenster (ongeveer de laatste twee jaar) en een maximum aantal resultaten.</li>
          <li><strong>Nieuws</strong> komt uit RSS-feeds: meestal recente berichten, geen volledig archief van alle tijden.</li>
          <li>Op de pagina worden per onderdeel maximaal honderd items getoond; het totaal is dus <strong>niet uitputtend</strong>. Voor systematisch onderzoek gebruik je databases en vaste zoekstrategieën.</li>
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
    <p class="filter-section__hint" id="filter-search-news-hint">Typ hierboven om te zoeken in titel of tekst. Kies hieronder een onderwerp om te verfijnen.</p>
    <div class="filter-theme-embedded" aria-labelledby="filter-theme-news-title">
      <h3 class="filter-section__title" id="filter-theme-news-title">Filter op thema</h3>
      <div class="chip-row theme-filter-row" aria-label="Filter op onderwerp" aria-describedby="filter-search-news-hint"></div>
    </div>
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
  <p class="panel-hint">Publicaties: automatisch uit PubMed op basis van vaste zoektermen en een beperkt recent tijdvenster; geen volledige literatuurlijst.</p>
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
    const url = String(n.url || "").trim();
    const hasUrl = !!url;
    const inner = `
      ${nBadges}
      <div class="card-header">
        <div class="card-title"><span class="title-link-wrap"><span class="card-title-text">${escHtml(n.title || "-")}</span>${hasUrl ? EXT_LINK_ICON : ""}</span></div>
        <div class="card-date">${escHtml(nd)}</div>
      </div>
      ${nNote}
      <div class="card-meta"><strong>${escHtml(n.source || "-")}</strong></div>
    `;
    if (hasUrl) {
      return `<a class="card card--link" href="${escAttr(url)}" target="_blank" rel="noopener">${inner}</a>`;
    }
    return `<div class="card">${inner}</div>`;
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


def _build_stamp() -> str:
    """Korte referentie voor debugging (view source op live vs git-commit)."""
    sha = os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("GITHUB_SHA") or ""
    if sha:
        return sha[:10]
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")


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
    html = html.replace("</body>", f"<!-- build:{_build_stamp()} -->\n</body>")
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard written to: {OUT_PATH}")
    print(f"   {stats['total_pubs']} publications · {stats['total_trials']} trials · {stats['total_news']} news")

if __name__ == "__main__":
    generate()
