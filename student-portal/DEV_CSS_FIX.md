# Student portal CSS loading fix (Vite development)

The student portal imports its stylesheet from `src/main.js` using `import './style.css'`.
The previous application version registered a service worker that could keep serving
stale cached files on `localhost:5174`, even while Vite was running.

The updated `src/main.js` now unregisters any old service worker and deletes the
old `techbok-shell-*` cache whenever Vite is running in development mode. The
production service worker is registered only in production.

## Apply and verify

1. Stop the student portal Vite server (Ctrl+C).
2. Replace the existing `student-portal/src/main.js`, `student-portal/src/style.css`,
   and `student-portal/public/sw.js` with the versions in this package.
3. Start the server again from the `student-portal` directory: `npm run dev`.
4. Open `http://localhost:5174` and refresh once.
5. If an old tab remains open, close it and open a fresh tab. The app will unregister
   the old service worker and clear its old cache on page load.

No database or Django settings need to be changed.
