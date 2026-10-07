# TidyGrid

## Run

Use Python 3.12. Extract all files into one folder, then run:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy

Upload every extracted file and folder to the root of `vivienalba/tidygrid`, including `assets`, `static`, `components`, and `.streamlit`. In Streamlit Community Cloud select branch `main`, main file **app.py**, and Python 3.12. The ZIP is a flat project root. No JavaScript build, CDN or API key is required. This delivery does not automatically publish to GitHub or Streamlit Cloud.

## Fonts

HK Grotesk headings and Metropolis body/table fonts are included in `static/fonts`, in regular, semibold and bold weights. The uploaded font ZIPs were unavailable, so the actual fonts were obtained from Hanken Design and Typehaus public distributions. Their licenses are included. Streamlit static serving is enabled in `.streamlit/config.toml`; no font CDN is used. The offline HTML embeds the fonts. PDF reports use Helvetica; Excel reports use Arial. See `assets/fonts/README.md` for provenance.

## Preserved features

CSV/TSV import retains encoding and delimiter settings. Cleaning includes headers, spaces, email casing, Philippine mobile formats and duplicates. Search, missing filters, original/cleaned previews, actual before/after examples and change logs remain available. Previews show up to 250 rows, workbook logs/gaps up to 500; exports include complete results.

Excel sheet/range selection edits only eligible plain text. Formulas, numeric values, protected content, rich text, hyperlinks and merged cells stay intact. Every original sheet, including hidden sheets, is exported with formatting definitions retained. Edited values can affect conditional formatting, charts and wrapping. Use ordinary unencrypted `.xlsx` files; `.xls` and `.xlsm` are unsupported.

The Dashboard Overview follows the supplied layout: three dataset summaries, review actions, column completeness and searchable records. Chart Builder, Expense Dashboard and Bills & Cash Flow retain grouping/count/sum/average, filters, chart summary CSV, expense breakdowns, monthly bills, snapshots and cash flow. Save workspace JSON before closing: session state is temporary. Ledger CSV and a self-contained interactive HTML dashboard are downloadable. Currency is a label, not exchange-rate conversion. Net-worth snapshots are user-entered.

Weekly, monthly, quarterly and annual activity reports retain mapping, issue review, Excel and PDF exports. Cutoffs use Asia/Manila. Historical completion timing requires a recorded completion date; current status alone cannot reconstruct it.

Ask TidyGrid uses local dataset commands. Open-ended generative AI is not connected and no data is sent to an AI provider.

## Contrast and controls

Light and dark preference variants share the same readable workspace palette. Charts explicitly use white backgrounds. Ask TidyGrid uses blue with white text, and cleaned-data exports have padded buttons with surrounding space.

## Interface limits

All eight original SVG references are retained under `assets/references`. Detailed illustrations use lossless WebP exports rather than repeatedly decoding the SVGs’ embedded raster/filter stacks. Supplied caretaker and walking illustrations retain their original pixel dimensions and transparency. Simple graphics remain vector assets.

Result summaries follow the lavender “year in numbers” reference. Tabulated results use yellow headers, a lavender label column, centered text, sharp edges and solid black grid lines. A “Sort and explore this table” disclosure retains the interactive data grid for results. Dataset previews keep the native searchable grid; Streamlit controls its canvas header alignment.

Bundled GSAP v3.15.0 handles the mobile drawer, illustration/card entrances, completeness bars, comparison rows and subtle illustration hover feedback. Anime.js v4.5.0 handles changed summary-value opacity. Both run within the supported Streamlit v2 component lifecycle, with scoped cleanup and reduced-motion support. Entrances run once per component per session and only when visible. Unchanged components are not rebuilt on ordinary reruns. Tables and chart controls remain stable. Native controls have short color feedback. Streamlit server reruns still govern page navigation; continuous whole-page morphs are not available. At 700 px and below, an accessible hamburger menu replaces the sidebar. Tables scroll horizontally. Mobile features use consistent side padding and compact, borderless action buttons.

## Verify

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

See DESIGN.md and VALIDATION.md.
