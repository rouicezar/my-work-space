# DeepSeek cloud-provider evidence — 2026-08-30

This is a time-bounded product-integration record, not a permanent capability or
pricing claim. Re-check the cited official pages before shipping or refreshing the
provider catalog.

## Direct official evidence

- The OpenAI-compatible origin is `https://api.deepseek.com`; bearer authentication
  uses a user-created API key.
- The current documented model identifiers are `deepseek-v4-flash`,
  `deepseek-v4-pro`, and an experimental vision model. The ordinary first acceptance
  route excludes the experimental vision model.
- Chat Completions supports text messages, thinking configuration, JSON output, and
  function-call proposals. Tool calls do not authorize product tool execution.
- The official pricing page has separate cache-hit, cache-miss, output, peak, and
  off-peak prices and explicitly warns that prices may change.
- Documented HTTP outcomes include invalid format (400), authentication failure
  (401), insufficient balance (402), invalid parameters (422), rate limiting (429),
  server error (500), and overload (503).
- The provider privacy policy updated 2026-02-10 says user input can be collected,
  retention varies by purpose and legal requirements, and personal data is directly
  processed and stored in the People's Republic of China. It describes a right to
  opt out of model-training/technology-optimization use; the product cannot assume
  that account setting is enabled.
- The Open Platform terms place disclosure, lawful-basis/consent, end-user rights,
  and security duties on the downstream application operator. They also prohibit
  misleading claims of official partnership or endorsement.

## Product consequences

- Cloud is disabled by default and never a hidden fallback.
- Model IDs, features, prices, effective timestamps, and policy links belong in a
  replaceable signed catalog, not application constants.
- Every outbound payload needs a content manifest, redaction result, exact digest,
  cost range, provider-policy disclosure, and one-shot approval.
- The first route blocks credentials and designated sensitive data; it does not claim
  that a warning alone makes transmission safe or lawful.
- Logs and normal audit events store metadata and digests, not prompt/response bodies.
- Actual usage and cost are reconciled after completion; estimate and actual remain
  separate facts.

## Official sources

- https://api-docs.deepseek.com/
- https://api-docs.deepseek.com/quick_start/pricing/
- https://api-docs.deepseek.com/quick_start/error_codes/
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://api-docs.deepseek.com/api/list-models/
- https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html
- https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html
