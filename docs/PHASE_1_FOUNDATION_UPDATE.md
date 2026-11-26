# TechBoK Phase 1 Foundation Update

This update incorporates the agreed presentation and navigation decisions.

## Staff console
- The application remains internal-only: unauthenticated visitors are presented with the staff sign-in screen, not a public marketing page.
- The supplied TechBoK logo is centred on the staff sign-in card.
- The supplied logo replaces the placeholder mark in the staff workspace sidebar and is aligned naturally to the left.
- Logging out clears the in-memory username and password fields, user data, error state, and local authentication tokens.
- Login fields use conservative autocomplete hints. Browser password managers may still independently offer saved credentials; the application cannot erase credentials saved by the browser.

## Student portal
- Adds a public visitor landing page with TechBoK introductory information and links to student sign-in.
- The student sign-in screen retains the existing graduation-cap icon, centred above the form.
- Logging out returns the visitor to the public landing page and clears in-memory login fields and local authentication tokens.

## Unchanged
- Existing Django API and database models.
- Existing staff/student application ports and API configuration.
- Existing student portal graduation-cap login mark.

## Verification
The archive structure and assets were checked. Run `npm install` and `npm run build` in each Vue application on the development computer, and run Django checks/migrations in the backend before deployment. Browser autofill behaviour should be tested in the target browsers.
