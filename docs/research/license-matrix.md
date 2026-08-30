# Upstream License and Distribution Matrix

Verified: 2026-08-28. Product intent clarified 2026-08-31. This is engineering risk classification, not legal advice. Transitive dependencies, bundled models, trademarks, and release assets require their own review before public distribution.

Development policy: the current phase is personal, non-commercial learning and exchange. Reuse existing non-visual functionality from all four upstream projects as far as each license permits, preserving required notices and modification records. Non-commercial intent does not itself waive license conditions. Public open-source distribution is a later, separate gate and must not inherit an unverified assumption from the private development phase.

| Component | Declared license | Source redistribution | Embedding in Forma AI | Required action |
|---|---|---|---|---|
| Semantica | MIT | Permitted with copyright and permission notice | Candidate | Preserve notice; audit dependency licenses and optional backends |
| holaOS | Modified Apache 2.0 with additional commercial-distribution and branding conditions | Conditional | Personal non-commercial reuse subject to license; **not cleared** for a generally distributable embedded product | Reuse permitted non-visual capability in development with notices; retain adapter boundary and obtain written clarification before public embedding |
| Herdr | Apache-2.0 | Permitted subject to Apache notice obligations | Candidate | Preserve LICENSE/NOTICE obligations; audit vendored `portable-pty` and all distributed assets |
| oMLX | Apache-2.0 | Permitted subject to Apache notice obligations | Candidate, but operationally prefer official DMG acquisition first | Preserve notices; audit transitive wheels, native kernels, updater, model licenses, and DMG signing/notarization provenance |

## Decisive holaOS constraint

The official license says a commercial license is required to embed holaOS source as a component of a product or service sold, licensed, or otherwise commercially distributed to third parties. It also prohibits removing or modifying frontend logo or copyright information. Because the current phase is personal and non-commercial but future public distribution is intended, the engineering policy is:

1. reuse holaOS non-visual workflow and application code during personal development where its license permits, preserving notices, branding obligations, and modification records;
2. keep the product-owned visual workbench independent and do not copy, modify, rebadge, or bundle restricted holaOS frontend assets in a public release;
3. maintain a versioned adapter boundary so a separately installed holaOS remains supported and public packaging can exclude uncleared material;
4. do not describe the combined product as cleared for public or commercial distribution until the exact source, assets, dependencies, notices, and distribution shape are reviewed;
5. seek written clarification before a public release includes any holaOS portion whose redistribution scope remains ambiguous.

Merely downloading holaOS during first run may still create an integrated commercial offering; it is not assumed to bypass the license. That deployment shape also needs written clearance.

## Additional unresolved license work

- Generate an SPDX-compatible software bill of materials for every shipped artifact.
- Check Semantica's heavy base dependencies and optional database/provider extras.
- Check Herdr's vendored code and plugin/integration assets.
- Check every oMLX wheel, native kernel, donor runtime, and model license separately.
- Verify trademark and logo permissions for all product-facing names and icons.
- Confirm whether upstream auto-updaters may download materially different license terms after installation.

## Primary license texts

- [Semantica MIT license](https://github.com/semantica-agi/semantica/blob/v0.6.7/LICENSE)
- [holaOS modified Apache license](https://github.com/holaboss-ai/holaOS/blob/main/LICENSE)
- [Herdr Apache-2.0 license](https://github.com/herdrdev/herdr/blob/v0.8.2/LICENSE)
- [oMLX Apache-2.0 license](https://github.com/jundot/omlx/blob/v0.6.3/LICENSE)
