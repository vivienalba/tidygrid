# TidyGrid

## Run

Use Python 3.12. Extract all files into one folder, then run:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

Upload every extracted file and folder to the root of `vivienalba/tidygrid`, including `assets`, `components`, and `.streamlit`. In Streamlit Community Cloud select branch `main`, main file **app.py**, and Python 3.12. The ZIP is a flat project root. No JavaScript build, CDN or API key is required. This delivery does not automatically publish to GitHub or Streamlit Cloud.

## Fonts

The requested HK Grotesk and Proxima Nova binaries were not supplied. **Arial is the temporary web fallback.** Add licensed files using the filenames in `assets/fonts/README.md`, then restart the app. Fonts are embedded locally in the app, components and offline dashboard. PDF reports use Helvetica; Excel reports use Arial.

## Preserved features

CSV/TSV import retains encoding and delimiter settings. Cleaning includes headers, spaces, email casing, Philippine mobile formats and duplicates. Search, missing filters, original/cleaned previews, actual before/after examples and change logs remain available. Previews show up to 250 rows, workbook logs/gaps up to 500; exports include complete results.

Excel sheet/range selection edits only eligible plain text. Formulas, numeric values, protected content, rich text, hyperlinks and merged cells stay intact. Every original sheet, including hidden sheets, is exported with formatting definitions retained. Edited values can affect conditional formatting, charts and wrapping. Use ordinary unencrypted `.xlsx` files; `.xls` and `.xlsm` are unsupported.

Dashboards include grouping/count/sum/average, filters, chart summary CSV, expense breakdowns, monthly bills, snapshots and cash flow. Save workspace JSON before closing: session state is temporary. Ledger CSV and a self-contained interactive HTML dashboard are downloadable. Currency is a label, not exchange-rate conversion. Net-worth snapshots are user-entered.

Weekly, monthly, quarterly and annual activity reports retain mapping, issue review, Excel and PDF exports. Cutoffs use Asia/Manila. Historical completion timing requires a recorded completion date; current status alone cannot reconstruct it.

Ask TidyGrid uses local dataset commands. Open-ended generative AI is not connected and no data is sent to an AI provider.

## Interface limits

All eight original SVG references are retained under `assets/references`. Illustrations are vector crops with rectangular backgrounds and unwanted arrows omitted. Tables have sharp edges, neutral rules and centered values. Streamlit native canvas headers keep their native alignment: the supported API does not expose reliable header centering. Static table headers are centered.

Bundled Anime.js v4.5.0 runs within Streamlit's supported v2 component lifecycle with cleanup. Illustrations, summary reveals and comparison values use restrained motion. Native controls use short CSS feedback. Reduced-motion preferences disable motion. Server reruns prevent continuous whole-page morphing; supported component reveals provide the closest reliable transition. The permanent sidebar remains available at small widths; tables scroll horizontally.

## Verify

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

See DESIGN.md and VALIDATION.md.
