# Enable GitHub Pages so the Car Simulation runs at kagunye.github.io/DRIVE-THRU

If you see **"There isn't a GitHub Pages site here"** (404), follow the steps below.

---

## 1. Make sure the repo is **Public**

- **Private repos** on a free GitHub account **do not** get a public Pages site (that’s a paid feature).
- Open **https://github.com/Kagunye/DRIVE-THRU** → **Settings** → **General**.
- Scroll to **Danger Zone** (or find "Visibility").
- If the repo is **Private**, change it to **Public** and save.
- Then go back to **Settings → Pages** and continue.

---

## 2. Turn on GitHub Pages

**→ [Open GitHub Pages settings](https://github.com/Kagunye/DRIVE-THRU/settings/pages)**

On that page:

1. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
2. Under **Branch**:
   - First dropdown: choose **main**.
   - Second dropdown: choose **/ (root)** (not "None" and not "/docs" unless you want to use docs).
3. Click **Save**.

---

## 3. Wait and test

- Wait **2–5 minutes** (first deploy can be slow).
- Open: **https://kagunye.github.io/DRIVE-THRU/**
- If it still shows 404, wait another 2–3 minutes and try again, or try in an incognito/private window.

---

## 4. Check that it’s actually enabled

- On **Settings → Pages**, after saving you should see a green box like:  
  **"Your site is live at https://kagunye.github.io/DRIVE-THRU/"**
- If you see **"GitHub Pages is currently disabled"** or **"None"** as the source, Pages is not enabled — repeat step 2 and click **Save** again.

---

## If you prefer to use the /docs folder

- In **Branch**, choose **main** and **/docs**. The same simulation is in `docs/index.html`.

## Check deployment

- If the green box says "failed" or "building", wait a minute and refresh the Pages settings page.
- The repo has `index.html` in the root and a `.nojekyll` file so GitHub serves the site as plain static files.
