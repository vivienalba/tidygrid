# Reference mapping

HOME.svg guides the illustrated hero, cream editorial sections, white capabilities, lavender summaries and overall spacing. The former yellow “From a file to a fresh perspective” section has been removed. Its original reference assets remain in the project.

| Reference | Adaptation |
|---|---|
| HOME | Landing composition and rhythm |
| r | Cleaning, dashboard and report graphics |
| r1 | Everyday-work map section |
| r2 | Original workflow artwork, retained as source assets |
| r3 | Landing hero |
| r4 | Ask light bulb and report pencil |
| r6 | Report preparation and introduction |
| r7 | Export completion |
| IMG_3064.JPG | Dashboard composition: sidebar, compact header, three summary cards, wide review panel, narrow completeness panel, full-width records table |

The dashboard reference supplies spatial relationships only. TidyGrid retains its own palette and existing heading/body typography. All counts, completeness bars and records reflect the active cleaned dataset. Review actions open real app views. Chart Builder, Expense Dashboard and Bills & Cash Flow remain available from the workspace selector.

Original SVGs remain intact. Simple graphics retain vector quality. Complex embedded-image SVGs use high-resolution lossless WebP exports to avoid repeated filter compositing. The supplied caretaker and walking illustrations retain their original pixel dimensions and transparency.

Result summaries retain the lavender “year in numbers” structure. Tabulated results retain yellow headers, lavender row labels, white cells and black grid lines. Reference figures and years are not copied into the data. Native dataset previews remain virtualized and scroll horizontally.

# Color and type

Navigation uses solid black #000000 with white #ffffff text on desktop and mobile. Purple #72559f marks the active workspace destination and blue #205182 marks hover. The workspace keeps its cream #f5f7ee background. Lavender #d4c2ef identifies landing actions and selected summary surfaces. Yellow #f6d46b supports the hero and table headers. Purple #72559f identifies completeness bars and the Ask introduction. Blue #205182 provides focus outlines and the Ask form action. Landing buttons use #fff3db on hover. Gradients remain concentrated in artwork and scenario panels.

HK Grotesk headings and Metropolis body/table text are served locally in weights 400, 600 and 700. Actual font files and their licenses are included. Font styling has not been copied from the dashboard photo.

# Responsive layout

At 700 px and below, a black mobile header replaces the desktop navigation with a hamburger menu. Its modal drawer uses native dialog focus trapping, Escape dismissal, focus restoration and buttons at least 44 px tall. Workspace destinations use the Streamlit component trigger callback; landing destinations scroll to real section anchors. The desktop sidebar returns above that breakpoint.

The mobile capabilities section has 24 px horizontal padding, 16 px gaps within features, 40 px between features, 40 px top padding and 44 px bottom padding. Headings and descriptions are centered, with compact borderless lavender action buttons and 14 px labels. Native Markdown's negative bottom margin is reset within this section so the description/button gap is real.

The import heading, panel and upload control are centered. The hidden native heading-anchor wrapper is removed from layout because its margin otherwise offsets the heading. Import Settings and Try a Sample Dataset sit side by side in workspace import controls on wider screens and stack on narrow screens. Dashed gray borders remain on import surfaces.

# Motion ownership

GSAP owns short, once-only opacity entrances, completeness-bar reveals and the mobile drawer. The drawer opens in 200 ms and closes in 120 ms. Navigation callbacks fire at the click, without waiting for the closing tween. Decorative illustration hover movement and the native page-title entrance have been removed. Summary cards and comparison rows fade briefly without moving their text; completeness bars reveal over 220 ms. Content remains visible before animation initializes.

Anime.js owns a 100 ms opacity transition on changed summary values. It does not animate GSAP's targets. Both engines are bundled and run within the public Streamlit v2 component lifecycle. Stable component data reuses existing local DOM/listeners where the lifecycle permits; the latest trigger callback is retained. Cleanup removes observers/listeners and reverts scoped animations. Reduced-motion preferences remove motion, including when changed at runtime. IntersectionObserver limits entrances to visible content, and session state avoids replaying entrances on ordinary filters and navigation.

Tables and native controls do not move. There are no ambient loops, animated counters, scroll-jacking or dependencies on a CDN. Streamlit server reruns still determine page-navigation latency; whole-page morphs are not attempted.

# Native control contrast

The native table toolbar retains visible black icons on a white surface. The former blanket rule that hid dataframe SVGs has been removed. Select controls explicitly keep their open/close indicators black. Include `.streamlit/config.toml` when deploying: its light and dark themes provide yellow canvas-table headers with black header text. Native canvas colors cannot be corrected by DOM CSS alone.

Dashboard composition follows IMG_3064 2.JPG: grouped rail, slim toolbar, three metrics, 2:1 activity/completeness panels, records underneath. Keep existing TidyGrid fonts and palette. Native data actions remain functional; no simulated approvals or invented clinical statistics.
