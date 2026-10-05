# Bundled web fonts

Font files live in `static/fonts`, served by Streamlit static serving and embedded into offline HTML exports.

- HK Grotesk Regular, Semibold, Bold: Hanken Design, https://github.com/HankenDesignCo/HK-Grotesk — SIL Open Font License 1.1, included as HK-Grotesk-OFL.txt.
- Metropolis Regular, Semibold, Bold: Typehaus distribution, https://github.com/typehaus/metropolis — public domain / Unlicense, included as Metropolis-LICENSE.md.

Each weight is a genuine WOFF2 font. Metropolis replaces Proxima Nova. No remote font request or JavaScript build is needed. Arial remains only a fallback. PDF reports use Helvetica and Excel reports use Arial.
