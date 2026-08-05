# ЭОД — программа индустриализации платформы

> GENERATED HUMAN VIEW. Machine-readable definition: `docs/project/INDUSTRIALIZATION_PROGRAM.yaml`; work-item statuses: `docs/project/DEMO_RELEASE_PLAN.yaml`. Ручное изменение этого файла будет отклонено Documentation Contract.

**Версия:** `1.0`
**Дата:** `2026-08-05`
**Источник:** `PROJECT-SUSTAINABILITY-001`
**Статус:** `ACCEPTED`

## 1. Принципы

- **[DECISION] `modular-monolith`:** Preserve the modular Django monolith; no microservices without proven necessity.
- **[DECISION] `no-big-bang`:** Industrialize through bounded work items; do not rewrite the product wholesale.
- **[DECISION] `one-product`:** One deployable product and application version with scoped optional modules.
- **[DECISION] `history-preservation`:** Module deactivation never deletes historical data.
- **[DECISION] `github-canonical`:** GitHub remains the only canonical source; Drive is a material library.
- **[DECISION] `risk-traceability`:** Every industrialization work item must close named risk IDs and provide acceptance evidence.

## 2. Gates

### `SAFE-CONTINUATION`

Minimum prerequisites before an owner may authorize limited work in an existing accepted domain contour.

Обязательные work items:

- `PROJECT-STATE-RECONCILIATION-001`
- `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`
- `MODULE-ACTIVATION-CONTRACT-001`
- `SECRET-HYGIENE-001`
- `DEPENDENCY-PROVENANCE-001`
- `DEPLOYMENT-PROFILE-001`
- `BACKUP-RESTORE-DRILL-001`
- `SECURITY-BASELINE-001`

Post-gate policy:

```json
{
  "exception": {
    "requires": [
      "separate_ADR",
      "explicit_product_owner_decision",
      "bounded_scope_and_accepted_risks"
    ]
  },
  "limited_existing_contour_work": {
    "allowed_only_by": "explicit_product_owner_decision",
    "example": "SHIFT-HANDOVER-001"
  },
  "mass_new_journals_and_modules": {
    "allowed_after": [
      "MODULE-REGISTRY-001",
      "UX-PLATFORM-FOUNDATION-001",
      "PAGE-TEMPLATE-LIBRARY-001",
      "MODULE-SOURCE-GOVERNANCE-001"
    ]
  }
}
```


Acceptance:

- Canonical planning views agree and automated checks prevent drift.
- Module activation semantics are accepted before implementation.
- No reusable credentials are exposed by CI or documentation.
- Dependency and image inputs are reproducible and attributable.
- Pilot/production configuration contract fails closed.
- A representative backup has been restored, verified and certified.
- Risk register and industrial backlog have owners and acceptance.

### `PILOT-READY`

Mandatory evidence gate before real pilot users, operational data or a pilot facility.

Обязательные work items:

- `PROJECT-STATE-RECONCILIATION-001`
- `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`
- `MODULE-ACTIVATION-CONTRACT-001`
- `SECRET-HYGIENE-001`
- `DEPENDENCY-PROVENANCE-001`
- `DEPLOYMENT-PROFILE-001`
- `BACKUP-RESTORE-DRILL-001`
- `SECURITY-BASELINE-001`
- `MODULE-REGISTRY-001`
- `DATA-INTEGRITY-HARDENING-001`
- `MIGRATION-SAFETY-001`
- `MODULE-MIGRATION-COMPATIBILITY-001`
- `DATA-GOVERNANCE-001`
- `RELEASE-ROLLBACK-001`
- `OBSERVABILITY-001`
- `INCIDENT-RESPONSE-001`
- `AUTH-RBAC-HARDENING-001`
- `SECURITY-PIPELINE-001`
- `UX-BROWSER-GATES-001`
- `SUPPORT-HANDOVER-001`
- `PILOT-READINESS-001`

critical_risk_policy:

```json
{
  "applicable": "close_or_explicitly_accept_with_bounded_controls_owner_due_date_and_review_condition",
  "not_applicable": "document_scope_evidence_and_owner_approval"
}
```

browser_gate_policy:

```json
{
  "requires_general_ux_refactor": false,
  "route_scope": "actual_critical_pilot_routes",
  "screen_scope": [
    "existing_accepted_screens",
    "migrated_screens"
  ],
  "ux_foundation_and_page_templates_required_when": [
    "new_page_family",
    "new_journal",
    "new_module_ui",
    "other_explicitly_recorded_pilot_trigger"
  ]
}
```

residual_risk_policy:

```json
{
  "high_medium": "close_or_record_owner_controls_due_date_review_condition_and_explicit_owner_acceptance",
  "long_term_not_applicable": "does_not_block_without_pilot_specific_justification"
}
```

Scope-dependent work items:

- `UPLOAD-HARDENING-001` — Pilot enables any upload, import or file-download surface.
- `DATA-PORTABILITY-001` — Pilot contract, exit plan, disaster migration or regulatory response requires portable export.
- `LEGACY-UX-MIGRATION-001` — Pilot includes routes with unresolved legacy/overlay risk.
- `UX-PLATFORM-FOUNDATION-001` — Pilot introduces a new page family, journal or module UI, or another explicitly recorded pilot trigger requires the shared UX foundation.
- `PAGE-TEMPLATE-LIBRARY-001` — Pilot introduces a new page family, journal or module UI, or another explicitly recorded pilot trigger requires reusable page templates.
- `MODULE-SOURCE-GOVERNANCE-001` — Pilot introduces a new module/capability or requires source freshness beyond accepted evidence.
- `DRIVE-LIBRARY-GOVERNANCE-001` — Google Drive materials are used in pilot operation or acceptance.
- `PERFORMANCE-BASELINE-001` — Pilot workload exceeds a bounded single-site small-cohort profile or PSR-031 is not explicitly accepted.

Acceptance:

- Mandatory core work items are accepted.
- Every applicable CRITICAL risk is closed or explicitly accepted with bounded controls.
- Pilot-scope-dependent work is completed or formally shown not applicable.
- Residual HIGH and MEDIUM risks follow the residual-risk policy.
- Scoped module activation and history preservation are demonstrated.
- Recovery, rollback, observability, incident response and security controls are exercised.
- Actual critical pilot routes on existing accepted and migrated screens pass supported browser, viewport, theme and print gates without requiring a general UX refactor.
- Another specialist completes install, restore, upgrade and diagnosis from repository documentation.
- Product owner explicitly approves the pilot scope, residual risks and known limitations.

## 3. Risk-ranked phases

### Фаза 0 — Governance and canonical-state integrity

Restore a reliable source of truth before platform implementation.

#### `PROJECT-STATE-RECONCILIATION-001`

- Приоритет: `P0`.
- Тип: `DOCUMENTATION_AUTOMATION`.
- Риски: `PSR-001`, `PSR-002`, `PSR-034`.
- Зависимости: нет.
- Acceptance:
  - One canonical status owner and consistent derived views.
  - Documentation checker rejects stale accepted/module/work-item state.

#### `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`

- Приоритет: `P0`.
- Тип: `GOVERNANCE`.
- Риски: `PSR-034`.
- Зависимости: `PROJECT-STATE-RECONCILIATION-001`.
- Acceptance:
  - Industrial backlog, gates and risks are represented in canonical planning.

### Фаза 1 — SAFE-CONTINUATION architecture and runtime baseline

Accept module semantics and close the highest recovery, configuration and security risks.

#### `MODULE-ACTIVATION-CONTRACT-001`

- Приоритет: `P0`.
- Тип: `ARCHITECTURE`.
- Риски: `PSR-004`, `PSR-005`, `PSR-014`.
- Зависимости: `PROJECT-STATE-RECONCILIATION-001`.
- Acceptance:
  - Manifest, lifecycle, scope precedence, guards and retention semantics accepted.

#### `SECRET-HYGIENE-001`

- Приоритет: `P0`.
- Тип: `SECURITY`.
- Риски: `PSR-021`.
- Зависимости: нет.
- Acceptance:
  - No active or reusable credentials appear in logs, repository or artifacts.

#### `DEPENDENCY-PROVENANCE-001`

- Приоритет: `P0`.
- Тип: `SUPPLY_CHAIN`.
- Риски: `PSR-017`, `PSR-023`, `PSR-016`.
- Зависимости: `SECRET-HYGIENE-001`.
- Acceptance:
  - Locked hashed dependencies, pinned image digests, SBOM and build provenance.

#### `DEPLOYMENT-PROFILE-001`

- Приоритет: `P0`.
- Тип: `DEPLOYMENT`.
- Риски: `PSR-003`, `PSR-022`, `PSR-018`.
- Зависимости: `DEPENDENCY-PROVENANCE-001`.
- Acceptance:
  - Unsafe pilot/production configuration refuses to start.
  - Deploy and external TLS/session checks pass.

#### `BACKUP-RESTORE-DRILL-001`

- Приоритет: `P0`.
- Тип: `DISASTER_RECOVERY`.
- Риски: `PSR-015`, `PSR-013`.
- Зависимости: `DEPLOYMENT-PROFILE-001`.
- Acceptance:
  - Restore certificate records checksum, RPO/RTO, duration, counts and integrity.

#### `SECURITY-BASELINE-001`

- Приоритет: `P0`.
- Тип: `SECURITY_ARCHITECTURE`.
- Риски: `PSR-022`, `PSR-023`, `PSR-024`, `PSR-033`.
- Зависимости: `DEPLOYMENT-PROFILE-001`.
- Acceptance:
  - Threat model, hardening controls and negative tests accepted.

### Фаза 2 — Modular platform control plane

Implement scoped optional modules without dynamic Django app loading.

#### `MODULE-REGISTRY-001`

- Приоритет: `P0`.
- Тип: `PRODUCT_PLATFORM`.
- Риски: `PSR-004`, `PSR-005`.
- Зависимости: `MODULE-ACTIVATION-CONTRACT-001`, `SECURITY-BASELINE-001`.
- Acceptance:
  - Mixed module sets work across organizations, sites and workplaces.
  - Deactivation blocks new actions and preserves readable history.

#### `MODULE-BOUNDARY-GATES-001`

- Приоритет: `P1`.
- Тип: `ARCHITECTURE_AUTOMATION`.
- Риски: `PSR-006`, `PSR-007`.
- Зависимости: `MODULE-ACTIVATION-CONTRACT-001`.
- Acceptance:
  - Dependency graph is cycle-free and forbidden imports fail CI.
  - Maintainability hotspots have owners and new ignores require explicit decisions.

### Фаза 3 — Data reliability and controlled release

Make data integrity, upgrade and rollback auditable and repeatable.

#### `DATA-INTEGRITY-HARDENING-001`

- Приоритет: `P0`.
- Тип: `DATA_RELIABILITY`.
- Риски: `PSR-011`, `PSR-012`.
- Зависимости: `DEPLOYMENT-PROFILE-001`.
- Acceptance:
  - Least-privilege writes and periodic digest/audit integrity reports.

#### `MIGRATION-SAFETY-001`

- Приоритет: `P0`.
- Тип: `MIGRATION_ENGINEERING`.
- Риски: `PSR-013`.
- Зависимости: `BACKUP-RESTORE-DRILL-001`.
- Acceptance:
  - Representative N-1/N-2 databases upgrade with preserved invariants.

#### `MODULE-MIGRATION-COMPATIBILITY-001`

- Приоритет: `P0`.
- Тип: `MIGRATION_TESTING`.
- Риски: `PSR-013`, `PSR-014`.
- Зависимости: `MODULE-REGISTRY-001`, `MIGRATION-SAFETY-001`.
- Acceptance:
  - Active/inactive module combinations upgrade and reactivate without data loss.

#### `DATA-GOVERNANCE-001`

- Приоритет: `P1`.
- Тип: `DATA_GOVERNANCE`.
- Риски: `PSR-026`, `PSR-032`.
- Зависимости: `DATA-INTEGRITY-HARDENING-001`.
- Acceptance:
  - Classification, retention, archive, legal hold and export rules accepted.

#### `DATA-PORTABILITY-001`

- Приоритет: `P1`.
- Тип: `DATA_PORTABILITY`.
- Риски: `PSR-032`.
- Зависимости: `DATA-GOVERNANCE-001`.
- Acceptance:
  - Versioned checksummed export is round-trip verified.

#### `RELEASE-ROLLBACK-001`

- Приоритет: `P0`.
- Тип: `RELEASE_ENGINEERING`.
- Риски: `PSR-016`, `PSR-015`.
- Зависимости: `DEPENDENCY-PROVENANCE-001`, `MIGRATION-SAFETY-001`, `BACKUP-RESTORE-DRILL-001`.
- Acceptance:
  - Immutable release manifest and measured rollback rehearsal.

### Фаза 4 — Operations and security completion

Detect, diagnose and contain failures and attacks.

#### `OBSERVABILITY-001`

- Приоритет: `P0`.
- Тип: `OPERATIONS`.
- Риски: `PSR-018`, `PSR-019`.
- Зависимости: `DEPLOYMENT-PROFILE-001`, `MODULE-REGISTRY-001`.
- Acceptance:
  - Structured logs, correlation, readiness, metrics, dashboards and alerts exercised.

#### `INCIDENT-RESPONSE-001`

- Приоритет: `P0`.
- Тип: `OPERATIONS`.
- Риски: `PSR-020`.
- Зависимости: `OBSERVABILITY-001`, `RELEASE-ROLLBACK-001`.
- Acceptance:
  - Severity/escalation model and technical incident exercise completed.

#### `AUTH-RBAC-HARDENING-001`

- Приоритет: `P0`.
- Тип: `IDENTITY_SECURITY`.
- Риски: `PSR-024`, `PSR-033`.
- Зависимости: `SECURITY-BASELINE-001`, `MODULE-REGISTRY-001`.
- Acceptance:
  - Privileged assurance, access reviews, break-glass and admin guards tested.

#### `SECURITY-PIPELINE-001`

- Приоритет: `P0`.
- Тип: `SECURITY_AUTOMATION`.
- Риски: `PSR-023`.
- Зависимости: `DEPENDENCY-PROVENANCE-001`, `SECURITY-BASELINE-001`.
- Acceptance:
  - Secret, SAST, dependency and container scans are required checks.

#### `UPLOAD-HARDENING-001`

- Приоритет: `P1`.
- Тип: `APPLICATION_SECURITY`.
- Риски: `PSR-025`.
- Зависимости: `SECURITY-BASELINE-001`.
- Acceptance:
  - All upload/import surfaces enforce centralized safety and access policy.

### Фаза 5 — Unified UX platform

Migrate incrementally without accumulating overlays or a second design system.

#### `UX-PLATFORM-FOUNDATION-001`

- Приоритет: `P1`.
- Тип: `UX_PLATFORM`.
- Риски: `PSR-008`, `PSR-009`, `PSR-010`.
- Зависимости: `MODULE-ACTIVATION-CONTRACT-001`.
- Acceptance:
  - Executable primitives and standard page profiles use DEFECT and OPJ references.

#### `LEGACY-UX-MIGRATION-001`

- Приоритет: `P1`.
- Тип: `UX_MIGRATION`.
- Риски: `PSR-008`.
- Зависимости: `UX-PLATFORM-FOUNDATION-001`.
- Acceptance:
  - Route/template/static inventory and evidence-based layer removal.

#### `UX-BROWSER-GATES-001`

- Приоритет: `P1`.
- Тип: `UX_TESTING`.
- Риски: `PSR-009`.
- Зависимости: `DEPLOYMENT-PROFILE-001`, `MODULE-REGISTRY-001`.
- Acceptance:
  - Actual critical pilot routes on existing accepted and migrated screens pass supported browser, theme, viewport, keyboard and print gates.
  - Browser-gate execution does not require a preceding general UX refactor.
  - UX foundation and page templates are required only by a documented pilot trigger such as a new page family, journal or module UI.

#### `PAGE-TEMPLATE-LIBRARY-001`

- Приоритет: `P1`.
- Тип: `UX_PLATFORM`.
- Риски: `PSR-010`.
- Зависимости: `UX-PLATFORM-FOUNDATION-001`.
- Acceptance:
  - Registry, journal, specialist workspace and timeline profiles are reusable.

### Фаза 6 — Knowledge and source governance

Ensure each module starts with complete and fresh evidence.

#### `MODULE-SOURCE-GOVERNANCE-001`

- Приоритет: `P1`.
- Тип: `KNOWLEDGE_GOVERNANCE`.
- Риски: `PSR-027`.
- Зависимости: `PROJECT-STATE-RECONCILIATION-001`.
- Acceptance:
  - Missing mandatory sources block new module work-item start after this capability is implemented.

#### `DRIVE-LIBRARY-GOVERNANCE-001`

- Приоритет: `P2`.
- Тип: `KNOWLEDGE_GOVERNANCE`.
- Риски: `PSR-028`.
- Зависимости: `MODULE-SOURCE-GOVERNANCE-001`.
- Acceptance:
  - Drive originals are checksum-traceable to GitHub metadata and decisions.

### Фаза 7 — Pilot and independent support

Prove the platform can be operated and transferred safely.

#### `PERFORMANCE-BASELINE-001`

- Приоритет: `P1`.
- Тип: `PERFORMANCE`.
- Риски: `PSR-031`.
- Зависимости: `DEPLOYMENT-PROFILE-001`, `OBSERVABILITY-001`.
- Acceptance:
  - Workload, P95 latency, resource headroom and soak results accepted.

#### `SUPPORT-HANDOVER-001`

- Приоритет: `P0`.
- Тип: `OPERATIONS_HANDOVER`.
- Риски: `PSR-029`.
- Зависимости: `OBSERVABILITY-001`, `INCIDENT-RESPONSE-001`, `RELEASE-ROLLBACK-001`.
- Acceptance:
  - Another specialist installs, restores, upgrades, rolls back and diagnoses without oral guidance.

#### `PILOT-READINESS-001`

- Приоритет: `P0`.
- Тип: `INDEPENDENT_ACCEPTANCE`.
- Риски: `PSR-030`.
- Зависимости: `MODULE-MIGRATION-COMPATIBILITY-001`, `DATA-GOVERNANCE-001`, `SECURITY-PIPELINE-001`, `UX-BROWSER-GATES-001`, `SUPPORT-HANDOVER-001`.
- Acceptance:
  - Mandatory pilot core is accepted.
  - Applicable critical risks are closed or explicitly accepted with compensating controls.
  - Scope-dependent and residual risks follow the PILOT-READY policies.
  - Product owner explicitly approves pilot scope and limitations.

## 4. Consistency contract

- Work-item IDs are unique.
- Every risk-register `proposed_work_item` resolves.
- Every dependency resolves and normal phase ordering is forward-safe.
- Gate work items exist.
- `PILOT-READY` mandatory core is direct/transitively closed.
- Hidden scope-dependent mandatory dependencies are forbidden.
- Markdown/YAML gate projection and required derived views are exact.
- Work-item/module accepted status and canonical ownership are fail-closed.
