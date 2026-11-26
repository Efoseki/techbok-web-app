# TechBoK offline-first foundation (Milestone 1 upgrade)

## Current foundation behaviour
- Both Vue apps register a service worker and cache the application shell after the app is first opened online.
- Sticky headers remain visible during scrolling.
- Browser-side IndexedDB outbox stores operation envelopes on each device.
- The outbox retries on the `online` event, window focus, app startup, and every 60 seconds while the app is open.
- The authenticated Django batch endpoint acknowledges events idempotently by UUID and records the envelope in `SyncEvent`.
- Assessment, Question and AssessmentAttempt models establish the first schema for trainer question banks, scheduling, attempts and marks.

## Important limitation in this milestone
Phase 2A adds validated create-only handlers for official Student, Admission and Enrollment records. Staff can create these records offline after the staff workspace has first loaded successfully online; the last synchronised branch/course/student lists are cached in IndexedDB for form selection. On reconnection, the server validates branch access, active course status, student/branch consistency and duplicate enrollments before writing to the official tables. Each operation has a UUID for idempotent retry. Rejected operations are retained locally as `needs_attention` rather than silently discarded. Offline edits, admission reviews/conversions, attendance, finance and assessment domain writes are not yet enabled; those modules still need their own conflict policies and handlers.

## Local setup after upgrade
1. Follow the existing README setup steps.
2. Generate migrations for the two new apps:
   `python manage.py makemigrations offline_sync assessments students`
3. Apply them:
   `python manage.py migrate`
4. Install updated frontend dependencies in each app:
   `npm install`
5. Build-check both apps:
   `npm run build`
6. Run backend checks:
   `python manage.py check`

## Offline behaviour and constraints
- Service workers require HTTPS in production; localhost is treated as a secure context for development.
- The application shell can open offline only after a successful first visit while connected.
- IndexedDB data is local to the browser profile/device; clearing browser data can erase pending events. Do not use private/incognito mode for work.
- Browser background sync is not guaranteed after the browser is closed. TechBoK also syncs on startup, focus, online event and while the app remains open.
- Local browser storage is not a trusted authority. The server must validate every domain operation, permissions, branch access, dates, duplicate identities, and record versions. The staff snapshot and pending payloads contain personal information and are stored in the browser's IndexedDB; use trusted, access-controlled staff devices and do not share browser profiles.
- Financial transactions, permissions, examination scores and released results need strict conflict handling; never use a global last-write-wins policy.
- For actual offline exams, pre-synchronise the approved assessment to the device, protect answer keys, enforce attempt rules, and reconcile the attempt server-side before scoring/releasing results.

## Next engineering stage
Implement domain-specific sync handlers and their API tests, beginning with student drafts/admissions and attendance; then build the assessment APIs and UI. Keep sensitive question answer keys server-side and expose student-safe question serializers only during eligible attempts.


## Phase 2A offline record capture
- The staff app stores the last successful workspace snapshot in IndexedDB and clears that snapshot on logout.
- Offline create operations are queued for Student, Admission and Enrollment records and tagged to the staff account that captured them; the server verifies that the same account is signed in and allocates the official reference numbers during synchronisation.
- Sync is create-only for these three record types. Updates, review decisions and conversion require a live server connection.
- A server rejection (for example, branch access revoked or duplicate enrollment) is retained as a local `needs_attention` item. The staff member should correct the issue and submit a new operation; rejected operations are not automatically replayed.
- Enrollments created offline must refer to an already-synchronised student record and an active course. A student created offline cannot be selected for an enrollment until the student has synchronised.
