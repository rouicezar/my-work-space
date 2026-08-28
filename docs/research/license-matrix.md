# Upstream License and Distribution Matrix

Verified: 2026-08-28. This is engineering risk classification, not legal advice. Transitive dependencies, bundled models, trademarks, and release assets require their own review before public distribution.

| Component | Declared license | Source redistribution | Embedding in Mac AI Work OS | Required action |
|---|---|---|---|---|
| Semantica | MIT | Permitted with copyright and permission notice | Candidate | Preserve notice; audit dependency licenses and optional backends |
| holaOS | Modified Apache 2.0 with additional commercial-distribution and branding conditions | Conditional | **Not cleared** for a generally distributable embedded product | Obtain written commercial/redistribution clarification; until then support only a separately installed user copy through an adapter and preserve branding |
| Herdr | Apache-2.0 | Permitted subject to Apache notice obligations | Candidate | Preserve LICENSE/NOTICE obligations; audit vendored `portable-pty` and all distributed assets |
| oMLX | Apache-2.0 | Permitted subject to Apache notice obligations | Candidate, but operationally prefer official DMG acquisition first | Preserve notices; audit transitive wheels, native kernels, updater, model licenses, and DMG signing/notarization provenance |

## Decisive holaOS constraint

The official license says a commercial license is required to embed holaOS source as a component of a product or service sold, licensed, or otherwise commercially distributed to third parties. It also prohibits removing or modifying frontend logo or copyright information. Because our target is a general distributable product and future commercial status is not fixed, the safe engineering policy is:

1. do not copy, modify, rebadge, or bundle the holaOS frontend in a public release;
2. do not describe the current combined product as legally cleared for commercial distribution;
3. build a versioned adapter against a separately installed holaOS instance;
4. seek written authorization or select/implement a differently licensed unified UI before claiming a single bundled installer.

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
