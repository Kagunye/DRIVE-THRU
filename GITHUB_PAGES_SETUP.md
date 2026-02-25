# Enable GitHub Pages so the Car Simulation runs at kagunye.github.io/DRIVE-THRU

If you see **"There isn't a GitHub Pages site here"** (404), turn on GitHub Pages **once** in the repo settings:

## Steps

1. Open **https://github.com/Kagunye/DRIVE-THRU**
2. Click **Settings** (top tab).
3. In the left sidebar, click **Pages** (under "Code and automation").
4. Under **Build and deployment**:
   - **Source**: choose **Deploy from a branch**.
   - **Branch**: select **main**, folder **/ (root)**.
   - Click **Save**.
5. Wait 1–2 minutes for GitHub to build.
6. Open **https://kagunye.github.io/DRIVE-THRU/** — you should see the car simulation.

The repo has `index.html` in the **root**, so using branch **main** and folder **/ (root)** is the right choice.

## If you prefer to use the /docs folder

- Choose **main** and **/docs** instead. The same simulation is in `docs/index.html` and will be served at the same URL.

## Check deployment

- On the **Pages** settings screen, after saving you’ll see: "Your site is live at https://kagunye.github.io/DRIVE-THRU/"
- If it says "failed" or "building", wait a minute and refresh the page.
