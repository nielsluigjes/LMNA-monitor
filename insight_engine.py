#!/usr/bin/env python3
"""
Heuristische relevantie, thema-clustering (trefwoord-buckets) en korte NL-samenvattingen.
Geen externe API — alleen locale tekstanalyse.
"""

from __future__ import annotations

from typing import Any

# (substring, punten) — laag-drempel matches op gecombineerde kleine tekst
_SCORE_TERMS: list[tuple[str, int]] = [
    ("lmna", 22),
    ("lamin a", 18),
    ("laminopathy", 18),
    ("laminopathies", 18),
    ("lamin", 12),
    ("edmd", 10),
    ("hutchinson-gilford", 10),
    ("dilated cardiomyopathy", 20),
    ("cardiomyopathy", 14),
    ("cardiac lamin", 16),
    ("heart failure", 14),
    ("dc ", 8),
    (" dcm", 8),
    ("dc,", 8),
    ("left ventricular", 8),
    ("lvef", 8),
    ("atrioventricular block", 18),
    ("av block", 14),
    ("heart block", 12),
    ("conduction", 12),
    ("bradycardia", 10),
    ("arrhythmia", 10),
    ("pacemaker", 8),
    ("pacing", 8),
    ("icd ", 6),
    ("sudden cardiac", 10),
    ("clinical trial", 6),
    ("randomized", 5),
    ("gene therapy", 8),
    ("crispr", 6),
    ("fibrosis", 6),
    ("magnetic resonance", 4),
    ("cmr", 4),
]

# thema-id, weergavenaam NL, zoekfragmenten (kleine letters)
_THEMES: list[tuple[str, str, tuple[str, ...]]] = [
    ("dcm", "DCM / cardiomyopathie", ("dilated", "cardiomyopathy", "heart failure", "lvef", "systolic", " hf", "dcm")),
    ("conduction", "Geleiding / ritme", ("conduction", "av block", "heart block", "bradycardia", "arrhythmia", "pacing", "pacemaker", "atrioventricular")),
    ("lmna", "LMNA / lamin", ("lmna", "lamin a", "laminopathy", "lmn1")),
    ("therapy", "Therapie & interventies", ("therapy", "treatment", "intervention", "drug", "gene", "crispr", "stem cell")),
    ("imaging", "Beeldvorming", ("cmr", "mri", "echo", "echocardiograph", "cardiac magnetic")),
]


def _norm_text(*parts: str | None) -> str:
    return " ".join(p or "" for p in parts).lower()


def relevance_score(text: str, *, recruiting_bonus: bool = False) -> int:
    t = text.lower()
    s = 0
    for needle, pts in _SCORE_TERMS:
        if needle in t:
            s += pts
    if recruiting_bonus:
        s += 18
    return min(100, s)


def theme_hits(text: str) -> tuple[list[str], str | None]:
    """Returns (list of theme ids with ≥1 hit, primary theme id or None)."""
    t = text.lower()
    scores: list[tuple[str, int]] = []
    for tid, _label, needles in _THEMES:
        c = sum(1 for n in needles if n in t)
        if c:
            scores.append((tid, c))
    if not scores:
        return [], None
    scores.sort(key=lambda x: (-x[1], x[0]))
    ids = [tid for tid, _ in scores]
    return ids, scores[0][0]


def _theme_labels(ids: list[str]) -> list[str]:
    m = {tid: lab for tid, lab, _ in _THEMES}
    return [m[i] for i in ids if i in m]


def enrich_publication(p: dict[str, Any]) -> dict[str, Any]:
    text = _norm_text(p.get("title"), p.get("abstract"), p.get("journal"))
    rel = relevance_score(text)
    tids, primary = theme_hits(text)
    out = dict(p)
    out["relevance"] = rel
    out["theme_ids"] = tids
    out["theme_labels"] = _theme_labels(tids)
    out["primary_theme"] = primary
    return out


def enrich_trial(t: dict[str, Any]) -> dict[str, Any]:
    text = _norm_text(t.get("title"), t.get("conditions"), t.get("interventions"))
    st = (t.get("status") or "").upper()
    recruiting = "RECRUIT" in st
    rel = relevance_score(text, recruiting_bonus=recruiting)
    tids, primary = theme_hits(text)
    out = dict(t)
    out["relevance"] = rel
    out["theme_ids"] = tids
    out["theme_labels"] = _theme_labels(tids)
    out["primary_theme"] = primary
    return out


def enrich_news(n: dict[str, Any]) -> dict[str, Any]:
    text = _norm_text(n.get("title"), n.get("summary"), n.get("source"))
    rel = relevance_score(text)
    tids, primary = theme_hits(text)
    out = dict(n)
    out["relevance"] = rel
    out["theme_ids"] = tids
    out["theme_labels"] = _theme_labels(tids)
    out["primary_theme"] = primary
    return out


def _short_title(s: str | None, max_len: int = 72) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def build_digest(
    pubs: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    news: list[dict[str, Any]],
) -> dict[str, Any]:
    """Template-gebaseerde NL-teksten + thema-clusteroverzicht."""
    recruiting = [t for t in trials if "RECRUIT" in (t.get("status") or "").upper()]

    by_theme: dict[str, list[dict[str, Any]]] = {tid: [] for tid, _, _ in _THEMES}
    for p in pubs:
        for tid in p.get("theme_ids") or []:
            if tid in by_theme and len(by_theme[tid]) < 8:
                by_theme[tid].append(p)

    theme_rows = []
    id_to_label = {tid: lab for tid, lab, _ in _THEMES}
    for tid, lab, _ in _THEMES:
        items = by_theme[tid]
        if not items:
            continue
        top = sorted(items, key=lambda x: (-(x.get("relevance") or 0), x.get("pub_date") or ""))[:3]
        titles = [_short_title(x.get("title")) for x in top]
        theme_rows.append(
            {
                "id": tid,
                "label": lab,
                "count": sum(1 for p in pubs if tid in (p.get("theme_ids") or [])),
                "examples": titles,
            }
        )

    paragraphs = []
    paragraphs.append(
        f"In dit scherm staan {len(news)} recente nieuwsberichten, {len(pubs)} publicaties en "
        f"{len(trials)} klinische studies (zoals nu in de database zitten). "
        f"Hieronder een automatische indeling op onderwerp — ter oriëntatie, geen medisch oordeel."
    )
    if recruiting:
        paragraphs.append(
            f"Er zijn nu {len(recruiting)} studie(s) met status gericht op werving (zoals RECRUITING). "
            f"Bekijk details op ClinicalTrials.gov en bespreek met je zorgteam of dit iets voor jullie is."
        )
    if theme_rows:
        paragraphs.append(
            "Thema’s bij de publicaties in dit overzicht (op basis van trefwoorden in titel en abstract):"
        )
    else:
        paragraphs.append(
            "Er zijn geen duidelijke thema-treffers in de publicaties van dit overzicht; "
            "gebruik de zoekbalk om gericht te filteren."
        )

    top_pubs = sorted(pubs, key=lambda x: (-(x.get("relevance") or 0), x.get("pub_date") or ""))[:5]
    highlight_titles = [_short_title(p.get("title"), 80) for p in top_pubs if p.get("title")]

    return {
        "paragraphs": paragraphs,
        "theme_rows": theme_rows,
        "highlights": highlight_titles,
        "recruiting_count": len(recruiting),
        "method_note": (
            "Relevantiescore en thema’s zijn heuristisch (trefwoorden). "
            "Controleer altijd de originele bron."
        ),
    }


def enrich_all(
    pubs: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    news: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ep = [enrich_publication(p) for p in pubs]
    et = [enrich_trial(t) for t in trials]
    en = [enrich_news(n) for n in news]
    digest = build_digest(ep, et, en)
    return ep, et, en, digest
