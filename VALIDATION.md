# Validation

29 regression tests pass on Python 3.12 and Streamlit 1.65.0. Coverage includes CSV/TSV import and encodings, cleaning calculations and rules, search/missing filters, Excel preservation and downloads, all six views, four report periods, finance calculations/exports, home navigation and malformed inputs.

Real Chromium browser checks passed for native CSV upload, cleaning toggles, navigation, local Ask commands, report PDF/XLSX downloads, ledger CSV/JSON downloads and the interactive HTML download. Browser checks observed no JavaScript errors. The offline dashboard made no external HTTP requests; changing month changed record counts from 46 to 69, and the Unpaid filter returned the expected three bills.

Visual checks at 1440px and 390px confirmed no document overflow, a centered import heading and upload button, and the permanent 128px sidebar at mobile width. Reports also fit at 320px. Both actual font families loaded successfully. Inactive sidebar labels and the upload label are white; the active sidebar label is black on yellow. Table headers are centered on yellow, label cells are centered on lavender, and grid lines are solid. These properties were checked from the rendered browser styles.

Repeated Bar/Donut selections retained the summary DOM instead of rebuilding it. Ordinary reruns do not replay entrances. Reduced-motion preferences suppress component reveals and restore automatic scroll behavior. Detailed artwork uses lossless WebP at original or high-resolution dimensions; the original eight SVG references remain included.

Remaining limits: Streamlit's native canvas controls dataset-preview header alignment and server reruns govern page changes. PDF fonts remain Helvetica, and Excel fonts Arial. Ask TidyGrid is a local command interface rather than an external generative-AI integration. This ZIP requires deployment by the owner; it does not publish itself.
