# Database design — starter and planned modules

## Foundation entities
- **User**: Django custom user; usernames are normalised to lowercase; password remains case-sensitive.
- **Branch**: code, name, contact details, active state. Start with Benin City and Auchi as seed data after migration.
- **BranchMembership**: many-to-many relationship between users and branches with a role per branch. A user can have different roles at different branches.
- **Course**: database-driven catalogue; code, title, description, duration, delivery mode, pricing, prerequisites, certification title, status.
- **AuditEvent**: actor, action, object reference, branch, before/after snapshots, IP, user-agent, timestamp.

## Implemented operational entities — Phase 2A
- **Admission**: applicant identity/contact, selected active course, branch/intake, review status, reviewer/decision timestamp, and protected link to the converted student.
- **Student**: branch-linked student profile, generated student number, demographics, contact/guardian/emergency contact, status and audit metadata. Portal account linkage is a later step.
- **Enrollment**: student + course + branch + cohort label, enrollment status, start/end dates and tuition/other-fee snapshot. A student cannot be enrolled twice in the same course and cohort.

## Planned operational entities
- **Intake/Cohort**: a formal course offering with branch, dates, fee snapshot, capacity and instructor assignments. Phase 2A currently stores a cohort/intake label on Admission and Enrollment; this will be normalised into a dedicated entity in a later stage.
- **Invoice / InvoiceLine**: student, enrolment, dates, charge description, amount and due date.
- **Payment**: unique payment reference, amount, channel, status, received_at, recorded_by; do not hard-delete posted payments.
- **PaymentAllocation**: amount allocated from a payment to an invoice; supports split/partial payments.
- **FinancialAdjustment**: discounts, waivers, corrections and reversals with approval and audit details.
- **Expense / ExpenseCategory**: branch, amount, payee, category, approval status, evidence attachment.
- **AcademicModule**: module belonging to a course or course version.
- **Assessment / AssessmentScore**: assessment definitions, weighting, student score, assessor and approval/publish status.
- **AttendanceSession / AttendanceRecord**: scheduled session and student attendance status, with amendment history.
- **Announcement / Notification**: branch/course targeting and delivery/read status.

## Relationship rules
- A user may belong to many branches through BranchMembership.
- A branch has many staff memberships, cohorts, invoices, payments and expenses.
- A course has many cohorts and versions; each cohort is delivered at one branch.
- A student has many enrolments; each enrolment belongs to a cohort.
- Invoices have multiple lines and allocations; payment references are unique.
- Assessment and attendance records belong to a specific enrolment/cohort context.
- Audit events reference the actor and optionally a branch; object type/id are stored generically to support cross-module logging.

## Financial integrity
Use Decimal fields, database transactions, immutable references, controlled void/reversal flows and reconciliation. Do not calculate balances solely from editable cached fields. Preserve course/fee snapshots on enrolment and invoice records. Use `PROTECT` or archival status for records with financial/academic history.
