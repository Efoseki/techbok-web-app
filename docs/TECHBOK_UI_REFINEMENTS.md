# TechBoK UI Refinements

This update preserves the supplied TechBoK logo artwork and the student portal's graduation-cap login mark.

- Staff sidebar logo: retained original image; adjusted display sizing and rendering to avoid unnecessary scaling artifacts.
- Staff sidebar brand area: remains visible at the top while the sidebar navigation scrolls.
- Student visitor header: sticky, with a contrasting navy background.
- Student signed-in header: added horizontal inset spacing so the graduation-cap mark and Sign out control do not touch the viewport edges.
- Student visitor hero: uses a photographic image of learners working together on laptops from Unsplash (requires an internet connection).
- Headline punctuation: removed the final full stop from “Practical technology skills for a changing world”.
- User-facing brand text: standardised to “TechBoK”. Internal storage keys and code identifiers remain unchanged for compatibility.

## Build check

The Python backend passed `python -m compileall`. The Vue production build was not run because the project dependencies (`vite` and Vue packages) are not installed in this environment. Run `npm install` and `npm run build` separately in each frontend folder before deployment.
