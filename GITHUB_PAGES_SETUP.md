# Get the Car Simulation online (fix 404)

If **https://kagunye.github.io/DRIVE-THRU/** shows 404, use one of the options below.

---

## ✅ Option 1: Netlify (works in ~2 minutes)

Use Netlify to host the same site. No GitHub Pages setup needed.

### One-click deploy

1. Click: **[Deploy to Netlify](https://app.netlify.com/start/deploy?repository=https://github.com/Kagunye/DRIVE-THRU)**
2. Log in with GitHub if asked and authorize Netlify.
3. Leave **Build command** empty; set **Publish directory** to `.` (a single dot) or leave as is if it already shows root.
4. Click **Deploy site**.
5. In 1–2 minutes you’ll get a URL like `https://something-random.netlify.app` — that’s your live car simulation.

You can change the site name later in Netlify (e.g. `kfc-drive-thru.netlify.app`).

---

## Option 2: GitHub Pages (GitHub Actions)

### 1. Repo must be **Public**

**Settings** → **General** → **Visibility** → **Public**.

### 2. Use **GitHub Actions** as the Pages source

- **[GitHub Pages settings](https://github.com/Kagunye/DRIVE-THRU/settings/pages)**
- **Build and deployment** → **Source** → **GitHub Actions**. Save.

### 3. Run the deploy workflow

- **[Actions tab](https://github.com/Kagunye/DRIVE-THRU/actions)** → **Deploy to GitHub Pages** → **Run workflow** → **Run workflow**.

### 4. First-time environment (if asked)

- If GitHub asks to approve the **github-pages** environment, go to **Settings** → **Environments** → **github-pages** and allow deployment.

### 5. Wait and open

- Wait 2–3 minutes, then open **https://kagunye.github.io/DRIVE-THRU/**.

---

## Option 3: GitHub Pages (Deploy from a branch)

1. **[GitHub Pages settings](https://github.com/Kagunye/DRIVE-THRU/settings/pages)** → **Source**: **Deploy from a branch**.
2. **Branch**: **main** → **/ (root)**. Save.
3. Wait 2–5 minutes. Open **https://kagunye.github.io/DRIVE-THRU/**.

---

## If GitHub Pages still shows 404

- Confirm repo is **Public**.
- Confirm **Source** is set (GitHub Actions or Deploy from a branch) and **Save** was clicked.
- For **GitHub Actions**: in **Actions**, check that **Deploy to GitHub Pages** run finished with a green check.
- Use **Option 1 (Netlify)** above to get the site live regardless of GitHub.
