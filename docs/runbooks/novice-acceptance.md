# Forma AI Novice-User Acceptance Script

Status: target final-release acceptance script. Passing this script requires a release candidate with every referenced capability enabled and independently verified. The existence of this document is not a pass.

## Participant and test conditions

- Participant has not contributed to Forma AI implementation and has not received undocumented help.
- Test device is a supported Apple Silicon Mac in a clean or documented equivalent state.
- Participant receives only the installer, the appropriate language guide, and test accounts/data.
- Observer may ask the participant to think aloud but must not explain hidden steps.
- Secrets, paid calls, and external writes use dedicated test credentials and reversible fixtures.

## Pass rules

- Every required journey is completed from public UI and documentation without Terminal.
- No task is marked complete when its verification failed or is missing.
- The participant can explain local versus cloud routing before approving a cloud call.
- The participant can identify what will change before an external write.
- No secret appears in logs, screenshots, task text, audit export, or diagnostics.
- Any critical safety, data-loss, permission, accessibility, or recovery failure is an overall failure.

## Journey 1: Understand the product

Ask the participant to read the overview and explain in their own words:

1. What Forma AI is.
2. What local-first means.
3. Why multiple agents are visible and controllable.
4. What governed memory means.
5. Two things Forma AI cannot guarantee or do.

Pass: the participant does not describe it as a generic chatbot, an autonomous authority, or an always-cloud product.

## Journey 2: Install and complete first launch

1. Install from the supported artifact.
2. Complete hardware and compatibility checks.
3. Review storage/download impact and approve the recommended local profile.
4. Interrupt and resume one safe installation step.
5. Run the verified sample task.

Pass: the participant reaches Local AI ready; the app distinguishes unknown, unsupported, interrupted, and verified states; no terminal knowledge is required.

## Journey 3: Run a private local task

Use three supplied documents. Ask for facts, opinions, unverified claims, and a cited one-page summary. Explicitly forbid cloud use and source-file changes.

Pass: result is local, sources are visible, originals are unchanged, audit correlation is available, and missing evidence is not presented as fact.

## Journey 4: Govern memory

1. Propose one source-linked project fact.
2. Confirm it as long-term memory.
3. Retrieve it in a new task.
4. Correct it using a second source.
5. Inspect history, export it, and delete it.

Pass: candidate and confirmed states are distinct; provenance and versions are visible; deleted content is no longer retrievable as authoritative memory.

## Journey 5: Run and control multiple agents

Start a task with independent research, comparison, and review workstreams.

1. Identify each agent, state, owner, and artifact.
2. Pause or cancel one safe workstream.
3. Resume eligible work.
4. Reopen the app and recover the task.
5. Review synthesis and unresolved disagreements.

Pass: no preview fixture is used; stable task/run identities survive restart; cancellation and recovery states are truthful; synthesis exposes missing evidence.

## Journey 6: Approve a cloud request

Use a non-sensitive task that is intentionally outside the verified local boundary.

1. Observe the capability explanation.
2. Review provider, model, exact data class/size, processing location, privacy notice, maximum output, estimated cost, expiry, and correlation ID.
3. Reject the first proposal and confirm nothing was sent.
4. Create a second proposal and approve it once.
5. Review output, actual usage/cost, and audit.

Pass: the rejected payload is not sent; approval applies only to the exact second request; no credential or prompt body appears in ordinary logs; no silent provider fallback occurs.

## Journey 7: Connect and use a real tool

1. Connect the selected release-acceptance connector with read-only scope.
2. Run a read-only task.
3. Request a reversible write.
4. Review the target, change, impact, and verification method.
5. Approve once, verify the external result, reverse it, and revoke access.

Pass: scopes remain separate; denial and revocation work; the correlated audit reflects preview, approval, action, verification, and reversal.

## Journey 8: Recover from failure

Inject one documented component failure and one interrupted task.

Pass: Forma AI states the cause, affected capability, safe action, and data risk; the participant uses recovery or rollback without deleting unknown state; no failed work appears complete.

## Journey 9: Review privacy and diagnostics

1. Find credential status without revealing the credential.
2. Inspect data routes and retention settings.
3. Export a diagnostic bundle.
4. Review its redaction summary.

Pass: secrets and unredacted task bodies are absent; the participant can revoke cloud and connector access.

## Journey 10: Update and uninstall

1. Complete a supported update preserving governed data.
2. Exercise rollback using the release fixture.
3. Start uninstall and choose an explicit keep/export/delete policy.
4. Confirm the uninstall summary.

Pass: retained and removed data are enumerated; externally owned caches are not silently deleted; the app and managed services are removed according to policy.

## Accessibility and usability observations

- Complete primary journeys using keyboard navigation.
- Verify meaningful labels, focus order, status announcements, contrast, text scaling, and reduced-motion behavior.
- Record every place where the participant hesitates for more than 20 seconds, mispredicts an action, or needs undocumented help.

## Evidence record

Record:

- release candidate version and signature/notarization result;
- device profile and clean-install condition;
- participant profile without personal data;
- start/end time for each journey;
- pass/fail and exact blocker;
- task/correlation IDs and redacted screenshots;
- external-action reversal evidence;
- accessibility findings;
- remediation owner and retest result.

Final acceptance requires every critical journey to pass after remediation. A partial run, developer-assisted completion, synthetic-only provider response, or screenshot without verified action evidence is not novice-user acceptance.
