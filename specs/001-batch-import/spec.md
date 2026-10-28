# Feature Specification: Batch file import

**Feature Branch**: `001-batch-import`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Plants upload a batch file to the API. Every rule in docs/rules.md runs on it. If all batches pass, they are loaded and the answer says how many. If any batch breaks a rule, nothing is loaded and the answer lists each failing batch with the rule it broke. A file that can't be read is refused with a reason."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load a clean batch file (Priority: P1)

A plant uploads the day's batch file. Every batch passes every rule, so all of them are loaded and the plant is told how many.

**Why this priority**: Loading good data is the reason the feature exists.

**Independent Test**: Upload the 48 batches of `data/batch_2026-10-01.csv` that break no rule; the store grows by 48.

**Acceptance Scenarios**:

1. **Given** the history of 1,943 batches, **When** a plant uploads a file of 48 batches that break no rule, **Then** the answer is "accepted: 48" and 1,991 batches are loaded.
2. **Given** that file has been loaded, **When** the same file is uploaded again, **Then** nothing is loaded and all 48 batches fail "BatchId is not already loaded".

---

### User Story 2 - Reject a file that breaks rules, and say why (Priority: P2)

A plant uploads a file with problems. Nothing is loaded, and the answer lists every failing batch with the rule it broke, so the plant can fix the file and send it again.

**Why this priority**: Without the reasons, a rejected plant has to guess what to fix.

**Independent Test**: Upload `data/batch_2026-10-01.csv` as it is.

**Acceptance Scenarios**:

1. **Given** the history, **When** a plant uploads `data/batch_2026-10-01.csv`, **Then** nothing is loaded and the answer lists 5 failures, the counts in `docs/rules.md`.
2. **Given** the same upload, **When** the plant reads the answer, **Then** it includes batch X00004 with the rule "Square feet are not negative".

---

### Edge Cases

- A file that isn't a batch CSV (wrong columns, a word where a number belongs) is refused with a reason, and nothing is loaded.
- A file with a header and no batches is refused: there is nothing to load.
- A batch that breaks two rules appears once for each rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The API MUST accept a batch file upload in the CSV layout of `data/batch_2026-10-01.csv`.
- **FR-002**: Every rule in `docs/rules.md` MUST run on every uploaded file.
- **FR-003**: If every batch passes, all of them MUST be loaded and the answer MUST give the number loaded.
- **FR-004**: If any batch breaks a rule, no batch from the file MAY be loaded, and the answer MUST list each failing batch with the rule it broke.
- **FR-005**: A file that can't be read, or has no batches, MUST be refused with a reason.

### Key Entities

- **Batch file**: one plant's batches for a day, in the CSV layout above.
- **Failure**: a batch and the name of the rule it broke.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uploading `data/batch_2026-10-01.csv` loads nothing and returns its 5 failures.
- **SC-002**: Uploading its 48 clean batches loads exactly 48, and uploading them again loads nothing.
- **SC-003**: Every scenario above is an automated test that passes in CI.
