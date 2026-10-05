# Validation

29 tests pass: workbook preservation, reporting calculations, finance exports and Streamlit AppTest workflows. Coverage includes all six views, cleaning rules, search/missing filters, TSV and Windows-1252 imports, workbook downloads, four report periods, finance samples, home navigation and malformed files.

Browser verification checks native file upload, component rendering, navigation, responsive layout, reduced motion and downloads. The offline dashboard embeds data and bundled JavaScript and needs no server after download.

Remaining limits: requested font binaries absent; native canvas header alignment managed by Streamlit; whole-page transitions bounded by server reruns. Ask TidyGrid is a local command interface. The ZIP does not publish itself.

Verified after source recovery: 29 tests passed. At 1440px and 390px, the landing import heading is centered and the Upload button has zero horizontal center offset. The dashboard has no document overflow at 390px; sidebar and main offset are both 128px. Its summary surface is 297 by 195px with 16px spacing before the explanation. Reduced motion changes scroll behavior to auto. No browser JavaScript errors were observed.

Real browser downloads verified cleaned CSV, report PDF/Excel, and finance HTML/CSV/JSON. The Excel report has eight sheets, yellow headers and centered body values. The PDF was rendered for visual inspection. Offline HTML month filtering changed 46 rows to 69; Unpaid filtering showed three bills. It rendered at 390px without document overflow, JavaScript errors or external HTTP requests. Reports were also checked at 320px and finance at 390px.
