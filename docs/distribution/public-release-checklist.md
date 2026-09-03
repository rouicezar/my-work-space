# Forma AI Public Release Checklist

Status: **release gate document** (P9-T01). A checked box here is not automatic evidence of pass. Every item requires linked verification evidence, command output, or an explicitly recorded blocker with owner and recovery action.

Related documents:

- Upstream pins and distribution policy: `config/upstreams.json`
- User-facing acceptance standard: `docs/runbooks/novice-acceptance.md`
- Bilingual target guides: `docs/guides/forma-ai-user-guide.en.md`, `docs/guides/forma-ai-user-guide.zh-CN.md`
- License notices (P9-T02): `docs/distribution/notices.md` *(pending)*
- Clean-install runbook (P9-T04): `docs/runbooks/clean-install.md` *(pending)*

## How to use this checklist

1. Complete items in order unless a documented dependency allows parallel work.
2. Record evidence path, command, commit SHA, and verifier for every `[x]` item.
3. Do not mark an item complete from screenshots, health endpoints, or Preview UI alone.
4. Any critical failure in security, data loss, recovery, accessibility, or novice acceptance is an **overall release block**.
5. Open development-only paths, personal fixtures, and gitignored control docs must not ship in public artifacts.

## Gate A — Product identity and legal readiness

| ID | Item | Evidence required | Status |
| --- | --- | --- | --- |
| A1 | Forma AI product license finalized for public distribution | SPDX identifier + `LICENSE` file in release artifact | [ ] |
| A2 | Trademark, branding, and icon redistribution rights confirmed | Written clearance or owned assets list | [ ] |
| A3 | README and shipped docs state **in-development vs release** honestly | Release notes + README diff review | [ ] |
| A4 | Bilingual user guides present with section parity | `docs/guides/forma-ai-user-guide.en.md` + `.zh-CN.md` review record | [ ] |
| A5 | Support matrix published for supported Apple Silicon tiers | Supported macOS + hardware matrix file | [ ] |

## Gate B — Upstream redistribution and notices

Source of truth: `config/upstreams.json`.

| ID | Component | Distribution policy | Release requirement | Status |
| --- | --- | --- | --- | --- |
| B1 | Semantica (`v0.6.7`, MIT) | `bundle_candidate` | NOTICE + transitive dependency audit; pinned managed runtime proof | [ ] |
| B2 | Herdr (`v0.8.2`, Apache-2.0) | `bundle_candidate` | Official binary SHA-256 match; NOTICE; lifecycle API compatibility proof | [ ] |
| B3 | oMLX (`v0.6.3`, Apache-2.0) | `official_dmg_first_run_candidate` | Verified DMG acquisition path; model license review; no silent bundling of unreviewed weights | [ ] |
| B4 | holaOS | `external_install_only_pending_written_clearance` | **Must not** bundle frontend/source/assets/trademarks; adapter-only or external-install documentation | [ ] |
| B5 | Aggregated `NOTICE` / third-party attributions complete | `docs/distribution/notices.md` + shipped `NOTICE` file | [ ] |
| B6 | SBOM or equivalent dependency manifest generated for release artifact | SBOM file path + generator command | [ ] |

## Gate C — Secrets, credentials, and private development isolation

| ID | Item | Command / procedure | Status |
| --- | --- | --- | --- |
| C1 | No secrets, tokens, cookies, or personal credentials in Git history for release tag | Secrets scan command (P9-T03) | [ ] |
| C2 | No developer-specific paths in shipped configuration defaults | Config diff + install inspection | [ ] |
| C3 | Keychain/cloud credentials require explicit user setup; none pre-seeded | First-run + settings review | [ ] |
| C4 | Audit logs redact or exclude secret material | Audit export sample review | [ ] |
| C5 | `.gitignore` private doc paths (`docs/plans/`, `docs/TASK_HANDOFF.md`, `evidence/`) excluded from public artifact | Release packaging manifest | [ ] |

## Gate D — Install, upgrade, rollback, uninstall, recovery

| ID | Item | Evidence required | Status |
| --- | --- | --- | --- |
| D1 | Clean install on supported tier succeeds without Terminal | Clean-install runbook execution record | [ ] |
| D2 | Upgrade from previous public release preserves user data and settings | Upgrade test record | [ ] |
| D3 | Rollback path documented and tested | Rollback runbook + result | [ ] |
| D4 | Uninstall removes product-owned state without orphaning secrets unsafely | Uninstall checklist | [ ] |
| D5 | Interrupted install/resume handled honestly (no false "ready") | First-run interruption test | [ ] |
| D6 | Task history recovery works with persisted metadata + live Herdr | P8 recovery proof + optional manual sign-off | [ ] |

## Gate E — Runtime, security, and policy behavior

| ID | Item | Evidence required | Status |
| --- | --- | --- | --- |
| E1 | Local inference proven with real completion or embedding call (not health-only) | oMLX inference proof evidence | [ ] |
| E2 | Cloud escalation requires credential state, preview, explicit approval, cost ceiling, audit | DeepSeek / cloud adapter proof | [ ] |
| E3 | External writes and destructive actions require preview + approval + audit | Policy integration test + manual review | [ ] |
| E4 | Semantica remains sole governed memory authority; no competing store shipped | P7 slice + ledger review | [ ] |
| E5 | Herdr remains core multi-agent runtime; no product-owned duplicate state machine | P8 slice + ledger review | [ ] |
| E6 | Tool/skill execution respects sandbox, approval, and audit gates | P6 end-to-end tool proof | [ ] |

## Gate F — Quality, accessibility, usability, and novice acceptance

| ID | Item | Evidence required | Status |
| --- | --- | --- | --- |
| F1 | Full Python test suite passes on release commit | `python3 -m unittest discover -s tests` | [ ] |
| F2 | Full Swift packaging test suite passes | `swift test --package-path prototypes/packaging` | [ ] |
| F3 | Bilingual UI review complete (separate Chinese and English window evidence) | Screenshot/review record | [ ] |
| F4 | Keyboard navigation and text scaling spot-check pass | Accessibility review notes | [ ] |
| F5 | Novice-user acceptance script executed by non-contributor | `docs/runbooks/novice-acceptance.md` signed result | [ ] |
| F6 | Open manual gates explicitly listed with owner (e.g. P8-T06 History recovery checklist) | Handoff / release notes | [ ] |

## Gate G — Release packaging and publication

| ID | Item | Evidence required | Status |
| --- | --- | --- | --- |
| G1 | Release artifact checksums published | SHA-256 list | [ ] |
| G2 | Version, build ID, and upstream pin manifest match `config/upstreams.json` | Manifest diff | [ ] |
| G3 | `git diff --check` clean on release branch | Command output | [ ] |
| G4 | Release tag created from verified commit; no unverified dirty work included | Tag + CI record | [ ] |
| G5 | Public repository scrubs private development docs and evidence paths | Tree inspection of published artifact/repo | [ ] |

## Release sign-off

| Role | Name | Date | Commit / tag | Notes |
| --- | --- | --- | --- | --- |
| Engineering verifier | | | | |
| Security reviewer | | | | |
| Release owner | | | | |

**Overall release decision:** [ ] Blocked  [ ] Approved for publication

Blockers (if any):

```text
- 
```

## P9 task cross-reference

| Task | This checklist section | Separate deliverable |
| --- | --- | --- |
| P9-T01 | Entire document | *(this file)* |
| P9-T02 | Gate B5–B6 | `docs/distribution/notices.md` |
| P9-T03 | Gate C1 | Secrets scan command in release docs |
| P9-T04 | Gate D1–D5 | `docs/runbooks/clean-install.md` |
| P9-T05 | Gate A4, F5 | User guides + novice script *(verified)* |
| P9-T06 | Gate F1–F2 | Final suite run record |
| P9-T07 | Gate G3–G4 | Distribution hardening commit |
