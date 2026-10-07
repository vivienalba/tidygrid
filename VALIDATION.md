# Current validation

30 regression tests pass on Python 3.12 and Streamlit 1.65.0. Coverage includes CSV/TSV import and encodings, cleaning calculations/rules, search and missing-value filters, workbook preservation and downloads, all six main views, four report periods, finance calculations/exports, home navigation and malformed inputs. The new Overview is covered for real dataset counts, record filtering, opening Chart Builder and navigating to cleaning. Python sources compile and the presentation JavaScript passes syntax checking.

Chromium checks for this revision passed with no page JavaScript errors:

- New landing action labels, removal of the workflow section and solid cream navigation.
- Desktop dashboard composition: three cards; review/completeness panels aligned at top and bottom with a 16 px gap and approximately 2:1 widths; records below.
- Overview search, Build chart action, repeated Bar/Donut changes and source import popover.
- Mobile hamburger opening/closing, Escape dismissal, restored focus, landing anchor navigation, Dashboard callback navigation and Back to Home callback.
- Reduced-motion menu behavior and switching to desktop while the drawer is open.
- Illustration hover uses a scoped GSAP transform and resets when reduced motion is enabled.
- No document overflow at 320, 390 or 700 px in the mobile workspace; desktop layout checked at 1440 px.
- Mobile capabilities: measured 24 px side padding, 16 px description/button gaps, 40 px between features, 14 px action labels and borderless buttons at least 44 px tall.
- Landing import heading and upload button centers match the panel center with zero measured horizontal deviation at 390 px.

# Previously verified functionality retained

Earlier browser passes verified actual CSV upload, cleaning toggles, local Ask commands, report PDF/XLSX downloads, ledger CSV/JSON downloads and the interactive HTML download. The self-contained exported dashboard made no external HTTP requests. Those data/export implementations are unchanged by this revision and remain covered by the regression suite.

Actual HK Grotesk and Metropolis font files are included locally. The light and dark preference variants share readable black text and white working surfaces. Charts explicitly use a white background. The Ask form action remains blue with white text; cleaned-data exports retain surrounding space and 16 px vertical / 28 px horizontal button padding.

# Limits

Browser checks used Chromium emulating narrow viewports, not a physical iPhone. Streamlit's native canvas controls dataset-preview header alignment, and server reruns govern page changes. PDF fonts remain Helvetica and Excel fonts Arial. Ask TidyGrid is a local dataset-command interface. This complete project still needs to be uploaded/deployed by the owner; the archive does not publish itself.
