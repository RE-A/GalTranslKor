# Ollama Korean translation implementation plan

Goal: develop entirely in Codex Cloud on RE-A/GalTranslKor, branch
`feature/ollama-ko-translation`, and open a PR into that fork's `main`.
Never push to GalTransl/GalTransl or merge the PR.

## Design and constraints

Add `Ollama-ko` through the existing engine factory. Keep GalTransl's file
plugins, preprocessing, job lifecycle and append/snapshot cache format.
Use an isolated backend and Korean prompt module rather than rewriting
OpenAI/Sakura engines. Support Ollama native `/api/chat` and its OpenAI
compatible `/v1/chat/completions`, using the existing httpx dependency.
No live model or user's PC/game files are required for development.

Batch sequentially within a file with line and serialized prompt character
budgets, rolling source/validated-target context, and explicit rejection of
oversized individual lines. Disable upstream parallel file chunking for this
engine so context cannot race; independent files may run concurrently.
Validate exact response IDs/count, Korean text, Japanese residue, placeholders,
and line breaks before committing any batch. Retry transient HTTP/timeout and
validation errors within a fixed attempt limit; never cache invalid output.
Fingerprint engine settings, prompt and glossary in existing `trans_by` metadata
and revalidate cache hits. Preserve already translated batches on failure.

## Tasks (native execution with TDD)

- [x] 1. Add failing HTTP Mock tests, then implement prompt, settings, API
  transport, bounded batching/context and response validation in
  `GalTransl/Backend/OllamaTranslate.py` and `OllamaPrompts.py`.
- [x] 2. Add failing integration tests, register `Ollama-ko` in
  `GalTransl/__init__.py` and `Frontend/LLMTranslate.py`, and exercise real
  `Service.run_job_async` / file plugin / cache reruns and failure recovery.
- [x] 3. Add synthetic mixed dialogue/narration sample, Korean configuration,
  noninteractive `run_ollama_ko.py`, Windows setup/run scripts, README and
  recorded feature-level test results. Test CLI against the Mock server.
- [ ] 4. Run Python and frontend suites/build; review full branch, fix important
  findings with regression tests, commit and push only to origin, open fork PR.

## Review focus

Malformed/truncated/duplicate response IDs must not create partial cache hits.
Changed model/prompt/glossary and invalid cached translations must invalidate.
Restart after a failed batch must recover prior context from cached results.
Long single lines and large context must fail or shrink context without silently
discarding source text. Concurrent files must never share dialogue history.
Windows paths with spaces and non-ASCII characters must remain supported.

## Validation

`python -m pytest -q tests/test_ollama_ko.py tests/test_ollama_ko_integration.py`
uses a real loopback HTTP server on an ephemeral port, never a local Ollama.
Run `python -m pytest -q`, `npm --prefix desktop test`,
`npm --prefix desktop run build`, and `npm --prefix desktop run i18n:check`.
Real-model quality/performance and native Windows execution remain explicitly
unverified in this Linux cloud task.

## Progress

Fork relationship/default branch verified via GitHub web metadata. Baseline:
64a2f846511d73cf283d95ce6156a0ca7c04b2ab. Existing workspace is already isolated.
GitHub API initially blocked by proxy (403); api.github.com added to environment
configuration draft. Independent development continues while access is pending.
The current conversation supplies the binding requirements; no earlier detailed
feature spec was found in the checkout. No additional speculative UI redesign.

### Implementation and review record

- First backend contract run: 27 failures before implementation, then 27 passed.
- First full-job run: 10 failures before engine registration; then integration
  exercised cache resume, cache identity and concurrent files. Glossary tests
  isolated app data with the existing `GALTRANSL_DATA_DIR` override and revealed
  that upstream dictionary entries use slots; fingerprinting now uses their
  explicit source, target and note fields.
- First CLI/sample run: 3 failures before files existed, then 3 passed.
- First full suite revealed that the registered default must remain
  `auto-translate`; existing default-order regression now passes.
- Independent whole-branch review identified three important issues. Regression
  tests reproduced all three before fixes: failed/cancelled jobs bypassed shared
  engine cleanup, glossary sizing included unselected rows, and a null OpenAI
  choice escaped validation retries. The cleanup now drains workers and closes
  clients in one finally block; glossary is selected per candidate batch; choice
  objects are validated before access. Failure/cancellation tests also assert no
  progress/adaptive-worker task remains in a persistent event loop.
- Added 120-entry scene and malformed-response recovery coverage. No live Ollama
  or user PC connections were made. Windows native execution remains unverified.
- GitHub API access succeeded using the approved execution route; the API
  confirmed fork parent, default branch main and push permission. No token values
  were requested or printed.
