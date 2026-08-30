# Upstream License and Distribution Matrix

Verified: 2026-08-28. Product intent clarified 2026-08-31. This is engineering risk classification, not legal advice. Transitive dependencies, bundled models, trademarks, and release assets require their own review before public distribution.

Development policy: the current phase is personal, non-commercial learning and exchange. Reuse existing non-visual functionality from all four upstream projects as far as each license permits, preserving required notices and modification records. Non-commercial intent does not itself waive license conditions. Public open-source distribution is a later, separate gate and must not inherit an unverified assumption from the private development phase.

| Component | Reviewed revision | Declared license | Public source publication | Binary embedding/distribution | Required action |
|---|---|---|---|---|---|
| Semantica | v0.6.7 / `ecb33a5b7d1c232da77527da89d861e2b10e9c42` | MIT | Permitted with copyright and permission notice | Candidate, subject to the same notice and dependency review | Preserve the upstream license/notice in source and binary notices; audit heavy base dependencies and optional backends |
| holaOS | `4684714ee133794cdbb86630e42b7d93447fb2e2` | Modified Apache 2.0 with additional commercial-distribution and frontend-branding conditions | Conditional; an open repository does not itself clear every combined or future commercial distribution shape | Personal non-commercial reuse is subject to the license; **not cleared** for a generally distributable embedded Forma AI product | Reuse eligible non-visual capability in development with notices; retain adapter boundary; exclude frontend/assets; obtain written clarification before public embedding |
| Herdr | v0.8.2 / `9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c` | Apache-2.0 | Permitted subject to Apache obligations | Candidate using the official digest-bound binary or compliant source build | Ship license/attribution, mark source modifications, retain applicable notices, and audit vendored `portable-pty`, integration/plugin assets, and trademarks |
| oMLX | v0.6.3 / `85708e4b9a585df42241c826b6be2b4dba018406` | Apache-2.0 | Permitted subject to Apache obligations | Candidate; operationally prefer verified official DMG acquisition until reproducible source build is proved | Ship license/attribution; audit transitive wheels, vendored/model code, private-runtime kernels, updater, model licenses, and signing/notarization provenance |

## Release modes are separate decisions

| Release mode | Current status | Gate |
|---|---|---|
| Private personal development | Allowed for the currently selected reuse decisions, with notices and source/revision records retained | No public claim; secrets and external accounts remain local and uncommitted |
| Public Forma AI source without upstream source copied in-tree | Candidate | Publish third-party manifest, adapter contracts, build instructions, SPDX SBOM, notices, and exact exclusions; verify no restricted assets or secrets are present |
| Public source containing copied or modified upstream code | Not globally cleared | Perform file-level provenance and license review; include licenses/notices and modification markers; holaOS requires a specific review of the copied non-visual paths and intended distribution shape |
| Binary distribution bundling Semantica, Herdr, or oMLX | Candidate, not release-ready | Bind exact artifacts/digests, include notices/SBOM/source-offer information where required, audit all transitive and model licenses, and pass clean install/update/rollback/uninstall gates |
| Binary distribution bundling holaOS source/frontend | Blocked pending written clearance | Do not ship frontend, logo, branded shell, or embedded source under an assumed non-commercial/open-source exception |
| Separately installed holaOS adapter | Preferred public fallback, still gated | Do not auto-download as a licensing workaround; require explicit install/origin/version fingerprint and confirm the combined deployment interpretation before release |
| Commercial hosted or commercially distributed Forma AI | Blocked for holaOS embedding without authorization; other components still require normal release review | Obtain written holaOS authorization or exclude it; repeat the complete dependency, trademark, privacy, and security review |

“Open source,” “free of charge,” “personal learning,” and “non-commercial” are not interchangeable legal categories. Publishing Forma AI's source does not automatically authorize copying or embedding every upstream component, and charging no fee does not remove notice, trademark, dependency, or modified-license obligations.

## Decisive holaOS constraint

The official license says a commercial license is required to embed holaOS source as a component of a product or service sold, licensed, or otherwise commercially distributed to third parties. It also prohibits removing or modifying frontend logo or copyright information. Because the current phase is personal and non-commercial but future public distribution is intended, the engineering policy is:

1. reuse holaOS non-visual workflow and application code during personal development where its license permits, preserving notices, branding obligations, and modification records;
2. keep the product-owned visual workbench independent and do not copy, modify, rebadge, or bundle restricted holaOS frontend assets in a public release;
3. maintain a versioned adapter boundary so a separately installed holaOS remains supported and public packaging can exclude uncleared material;
4. do not describe the combined product as cleared for public or commercial distribution until the exact source, assets, dependencies, notices, and distribution shape are reviewed;
5. seek written clarification before a public release includes any holaOS portion whose redistribution scope remains ambiguous.

Merely downloading holaOS during first run may still create an integrated commercial offering; it is not assumed to bypass the license. That deployment shape also needs written clearance.

## Additional unresolved license work

- Create a file-level provenance manifest distinguishing original Forma AI code, modified upstream source, unmodified binary artifacts, models, documentation, and visual assets.
- Generate a complete third-party notices file from the reviewed provenance rather than relying only on top-level repository license labels.
- Generate an SPDX-compatible software bill of materials for every shipped artifact.
- Check Semantica's heavy base dependencies and optional database/provider extras.
- Check Herdr's vendored code and plugin/integration assets.
- Check every oMLX wheel, native kernel, donor runtime, and model license separately.
- Verify trademark and logo permissions for all product-facing names and icons.
- Confirm whether upstream auto-updaters may download materially different license terms after installation.

## Primary license texts

- [Semantica MIT license](https://github.com/semantica-agi/semantica/blob/v0.6.7/LICENSE)
- [holaOS modified Apache license at reviewed commit](https://github.com/holaboss-ai/holaOS/blob/4684714ee133794cdbb86630e42b7d93447fb2e2/LICENSE)
- [Herdr Apache-2.0 license at reviewed commit](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/LICENSE)
- [oMLX Apache-2.0 license at reviewed commit](https://github.com/jundot/omlx/blob/85708e4b9a585df42241c826b6be2b4dba018406/LICENSE)
