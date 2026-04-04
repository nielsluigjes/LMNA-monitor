#!/usr/bin/env python3
"""
Heuristische relevantie, thema-clustering (trefwoord-buckets) en korte NL-samenvattingen.
Geen externe API; alleen locale tekstanalyse.
"""

from __future__ import annotations

from typing import Any

# (substring, punten): laag-drempel matches op gecombineerde kleine tekst
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

# Korte toelichting bij thema-cluster voor patiënten (zelfde id als _THEMES)
_THEME_PATIENT_BLURB: dict[str, str] = {
    "dcm": "Vaak over een zwakker wordend hart of hartfalen.",
    "conduction": "Vaak over geleiding of ritme in het hart.",
    "lmna": "Expliciet over LMNA of lamin.",
    "therapy": "Over behandeling, medicijnen of therapie-onderzoek.",
    "imaging": "Over echo, hart-MRI of andere beeldvorming.",
}

# Eén zin op kaarten: waarom dit item kan aansluiten (zelfde id als _THEMES)
_READER_NOTE_BY_THEME: dict[str, str] = {
    "dcm": "Dit lijkt vooral te gaan over een zwakker wordend hart of hartfalen.",
    "conduction": "Dit lijkt vooral te gaan over geleiding van de hartprikkel of over ritme.",
    "lmna": "Dit gaat expliciet over LMNA of lamin; vaak dicht bij de oorzaak van de aandoening.",
    "therapy": "Dit gaat waarschijnlijk over behandeling, medicijnen of nieuwe therapieën in onderzoek.",
    "imaging": "Dit gaat waarschijnlijk over echo, hart-MRI of vergelijkbare onderzoeken.",
}

_READER_NOTE_FALLBACK = (
    "Het onderwerp is niet scherp in één hokje te plaatsen; lees de titel of open de bron "
    "als je wilt beoordelen of het voor jou interessant is."
)

_RECRUITING_TRIAL_NOTE = (
    "Deze studie staat open voor werving; meedoen kan alleen via de officiële studiepagina "
    "en na overleg met je arts."
)

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


def _reader_note_nl(primary: str | None, *, recruiting_trial: bool = False) -> str:
    base = _READER_NOTE_BY_THEME.get(primary or "", _READER_NOTE_FALLBACK)
    if recruiting_trial:
        return f"{base} {_RECRUITING_TRIAL_NOTE}"
    return base


def enrich_publication(p: dict[str, Any]) -> dict[str, Any]:
    text = _norm_text(p.get("title"), p.get("journal"))
    rel = relevance_score(text)
    tids, primary = theme_hits(text)
    out = dict(p)
    out["relevance"] = rel
    out["theme_ids"] = tids
    out["theme_labels"] = _theme_labels(tids)
    out["primary_theme"] = primary
    out["reader_note_nl"] = _reader_note_nl(primary, recruiting_trial=False)
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
    out["reader_note_nl"] = _reader_note_nl(primary, recruiting_trial=recruiting)
    return out


def enrich_news(n: dict[str, Any]) -> dict[str, Any]:
    text = _norm_text(n.get("title"), n.get("source"))
    rel = relevance_score(text)
    tids, primary = theme_hits(text)
    out = dict(n)
    out["relevance"] = rel
    out["theme_ids"] = tids
    out["theme_labels"] = _theme_labels(tids)
    out["primary_theme"] = primary
    out["reader_note_nl"] = _reader_note_nl(primary, recruiting_trial=False)
    return out


def _short_title(s: str | None, max_len: int = 72) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _pub_link_item(p: dict[str, Any], *, title_max: int = 72) -> dict[str, str]:
    return {
        "title": _short_title(p.get("title"), title_max),
        "url": (p.get("url") or "").strip(),
    }


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
    for tid, lab, _ in _THEMES:
        items = by_theme[tid]
        if not items:
            continue
        top = sorted(items, key=lambda x: (-(x.get("relevance") or 0), x.get("pub_date") or ""))[:3]
        examples = [_pub_link_item(x) for x in top]
        theme_rows.append(
            {
                "id": tid,
                "label": lab,
                "blurb": _THEME_PATIENT_BLURB.get(tid, ""),
                "count": sum(1 for p in pubs if tid in (p.get("theme_ids") or [])),
                "examples": examples,
            }
        )

    overview_line = (
        f"Hier staan {len(news)} nieuwsberichten, {len(pubs)} publicaties en {len(trials)} studies, "
        f"verzameld uit openbare bronnen. Je hoeft echt niet alles te lezen: "
        f"begin gerust bij Nieuws of bij de kantlijn ‘Waar begin je?’, en gebruik zoeken en snelknoppen "
        f"om te vernauwen naar wat bij jou past."
    )
    recruiting_note: str | None = None
    if recruiting:
        n = len(recruiting)
        if n == 1:
            recruiting_note = (
                "Er is nu één studie in dit overzicht die deelnemers zoekt (status rond ‘werving’). "
                "Inschrijven kan alleen via de officiële studiepagina (ClinicalTrials.gov) en na overleg met je arts. "
                "Dit is geen aanbeveling om mee te doen."
            )
        else:
            recruiting_note = (
                f"Er zijn nu {n} studies in dit overzicht die deelnemers zoeken (status rond ‘werving’). "
                "Inschrijven kan alleen via de officiële studiepagina (ClinicalTrials.gov) en na overleg met je arts. "
                "Dit is geen aanbeveling om mee te doen."
            )
    themes_intro = (
        "Hieronder staan een paar veelvoorkomende onderwerpen onder de publicaties. "
        "De groepering is automatisch (op woorden in titel en tijdschrift); geen medische indeling, "
        "maar wel handig om te oriënteren."
    )
    empty_themes_note: str | None = None
    if not theme_rows:
        empty_themes_note = (
            "In de publicaties van dit scherm vallen geen duidelijke onderwerpgroepen te maken; "
            "gebruik de zoekbalk om gericht te zoeken."
        )

    top_pubs = sorted(pubs, key=lambda x: (-(x.get("relevance") or 0), x.get("pub_date") or ""))[:5]
    highlights = [_pub_link_item(p, title_max=80) for p in top_pubs if p.get("title")]

    theme_options = [{"id": tid, "label": lab} for tid, lab, _ in _THEMES]

    return {
        "method_note": (
            "Geen medisch advies. Wat je hier leest is automatisch geordend op titel en tijdschrift (publicaties) "
            "of titel en bron (nieuws); op elke kaart staat een korte zin voor lezers. Controleer altijd in de originele bron."
        ),
        "overview_line": overview_line,
        "recruiting_note": recruiting_note,
        "themes_intro": themes_intro,
        "empty_themes_note": empty_themes_note,
        "theme_rows": theme_rows,
        "theme_options": theme_options,
        "highlights": highlights,
        "recruiting_count": len(recruiting),
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
