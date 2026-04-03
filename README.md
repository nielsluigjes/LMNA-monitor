# LMNA Cardiac Disease Monitor

Scrapet automatisch PubMed, ClinicalTrials.gov en nieuws. Publiceert dagelijks een dashboard op GitHub Pages en/of Vercel.

**URL’s (na setup):**

- **Vercel** (geen GitHub-gebruikersnaam in het adres): `https://<jouw-project>.vercel.app/` (root toont het dashboard)
- **GitHub Pages** (optioneel): `https://<github-username>.github.io/LMNA-monitor/dashboard.html`

---

## Vercel koppelen (~3 minuten)

1. Ga naar [vercel.com](https://vercel.com) → **Add New…** → **Project** → importeer deze GitHub-repo.
2. **Framework Preset:** Other  
3. **Root Directory:** `./` (standaard)  
4. **Build Command:** leeg laten  
5. **Install Command:** leeg laten  
6. **Output Directory:** leeg laten (of `.`; de site staat al als `dashboard.html` in de repo)  
7. Deploy. Daarna: elke push naar `main` (o.a. de dagelijkse bot-commit) triggert automatisch een nieuwe productie-deploy.

Commits met `[skip ci]` slaan alleen GitHub Actions over; Vercel blijft deployen via de gewone GitHub-webhook.

---

## Eenmalige setup GitHub Pages (~10 minuten, optioneel)

### 1. Push deze bestanden naar je repo

```bash
git clone https://github.com/nielsluigjes/LMNA-monitor.git
cd LMNA-monitor
# Kopieer alle bestanden hierheen, dan:
git add .
git commit -m "Initial setup"
git push
```

### 2. Zet GitHub Pages aan (optioneel als je ook op `github.io` wilt hosten)

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
2. Klik **Daily LMNA Scrape & Deploy**
3. **Run workflow** → **Run workflow**
4. Wacht ~2 minuten

### 5. Klaar

De dagelijkse workflow werkt op **main**; het dashboard staat op Vercel (als gekoppeld) en desgewenst op **gh-pages**.

Stuur je **Vercel-URL** (of de `github.io`-link) door. Elke dag 07:00 UTC automatisch bijgewerkt.

---

## Kosten: €0

- GitHub Actions: gratis (ongeveer enkele minuten per dag; ruim binnen de gratis minuten)
- GitHub Pages: gratis (optioneel)
- Vercel hobby/free tier: voldoende voor deze statische site
- Alle APIs (PubMed, ClinicalTrials, RSS): gratis, geen keys nodig
