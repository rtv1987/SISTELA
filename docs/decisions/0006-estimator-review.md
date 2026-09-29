# 0006 — Explicit review snapshots and a shared handoff validator

Accepted 2026-09-29.

Keep source quantities in EstimateLine. Persist explicit target conversions and
local human review decisions in a JSON review_data snapshot on the same versioned
row. Decimal values in JSON are strings. Conversion validity checks compare the
snapshot with source values and the known m/100m rule; source edits invalidate
confirmation. Project/row duplication clears approvals. Existing mapping history
remains the source of explicit mapping confirmations.

Central validation owns blocking vs warning decisions, readiness and entry
eligibility. GET reports are read-only; explicit POST validation persists project
status. An entered flag is a user's declaration, not an integration receipt.

Working XLSX appends target/review columns without changing existing import column
positions. Stale target values are omitted. XLSX reimport does not restore trust.

Metrics are local current-row aggregates and persisted human decision categories,
not a remote analytics service or a lifetime event warehouse. Known constraints
and real-device acceptance procedure are in estimator-workflow.md.
