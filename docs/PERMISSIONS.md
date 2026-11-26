# Permission architecture

## Principles
1. Authentication is JWT-based for the API; all API routes require authentication unless explicitly public.
2. System administrator is represented by Django `is_superuser` and can manage all branches.
3. Branch roles are assigned through `BranchMembership`; membership can differ by branch.
4. The backend filters querysets and validates every write. Frontend route guards are usability aids, not security controls.
5. Students may only access their own profile, enrolments, invoices, attendance and released results.
6. Finance permissions should be split into view, record payment, approve adjustment, reverse payment, manage expenses and export reports before finance is shipped.
7. Audit events are read-only through the API and visible only to system administrators in this starter. Production policy may grant a designated auditor read-only access.

## Starter role matrix
| Action | System admin | Branch manager | Finance | Admissions | Instructor | Student |
|---|---:|---:|---:|---:|---:|---:|
| Create/deactivate branch | Yes | No | No | No | No | No |
| View assigned branches | All | Assigned | Assigned | Assigned | Assigned | Assigned |
| Manage course catalogue | Yes | Yes* | No | Yes* | No | No |
| View active courses | Yes | Yes | Yes | Yes | Yes | Yes |
| Read audit trail | Yes | No | No | No | No | No |

`*` Course catalogue is institute-wide in this starter; edit permissions are deliberately conservative and will be refined into dedicated permissions/groups before production.

## Production hardening
- Add granular Django permissions for every sensitive action.
- Ensure branch scoping is applied to every branch-owned object and nested endpoint.
- Use object-level permission tests for cross-branch IDOR attempts.
- Never trust a branch ID from the browser without verifying the user's membership.
- Configure throttling, secure transport, secrets, session/token lifecycle, and logs.
