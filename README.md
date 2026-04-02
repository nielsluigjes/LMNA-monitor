# LMNA Cardiac Disease Monitor

Scrapet automatisch PubMed, ClinicalTrials.gov en nieuws. Publiceert wekelijks een dashboard op GitHub Pages.

**Live URL (na setup):**
`https://nielsluigjes.github.io/LMNA-monitor/dashboard.html`

---

## Eenmalige setup (~10 minuten)

### 1. Push deze bestanden naar je repo

```bash
git clone https://github.com/nielsluigjes/LMNA-monitor.git
cd LMNA-monitor
# Kopieer alle bestanden hierheen, dan:
git add .
git commit -m "Initial setup"
git push
```

### 2. Zet GitHub Pages aan

1. Ga naar je repo → **Settings**
2. Links: klik **Pages**
3. Source: **Deploy from a branch**
4. Branch: **gh-pages** → **(root)**
5. Klik **Save**

### 3. Geef Actions schrijfrechten

1. **Settings → Actions → General**
2. Scroll naar "Workflow permissions"
3. Kies **Read and write permissions**
4. Klik **Save**

### 4. Eerste run handmatig starten

1. Tabblad **Actions** in je repo
2. Klik **Weekly LMNA Scrape & Deploy**
3. **Run workflow** → **Run workflow**
4. Wacht ~2 minuten

### 5. Klaar

`https://nielsluigjes.github.io/LMNA-monitor/dashboard.html`

Stuur deze link naar je vriend. Elke maandag 07:00 UTC automatisch bijgewerkt.

---

## Kosten: €0

- GitHub Actions: gratis (jij gebruikt ~5 min/week van 2000 gratis)
- GitHub Pages: gratis
- Alle APIs (PubMed, ClinicalTrials, RSS): gratis, geen keys nodig
