# Swarm Hijack

[CodeIntegrity's research on swarm poisoning in agent harnesses](https://www.codeintegrity.ai/blog/swarm-poisoning-agent-harnesses)
documents this proof of concept. In one controlled Muse Code session, a
rewritten subagent result led the parent to run an npm package. The attacker
needed local access to the session log as the same user.

## Recorded evidence

- [`evidence/r5/session_key_records.jsonl`](evidence/r5/session_key_records.jsonl) contains selected records, not the full session: the altered subagent result (sequence 519), the `npx --yes frame-profiler --suite engine` call (1548), a network approval (1557–1561), an npm cache failure (1568), and a successful retry (1595, 1615).
- [`evidence/r5/EXECUTED_AT`](evidence/r5/EXECUTED_AT) and [`last-run.txt`](evidence/r5/last-run.txt) record execution of the unscoped `frame-profiler` version 1.0.2 in the test workspace. [`npm_packument.txt`](evidence/r5/npm_packument.txt) records the package metadata observed during that run.
- The public artifacts do not establish data exfiltration or removal of the altered log record. They establish package execution in one local run, not a success rate.

## Reproduce

This repository does not contain a one-command replay of the recorded run.
It requires Muse Code, Python 3, Node/npm, a disposable workspace, and a live
session with a matching subagent result. The [article](https://www.codeintegrity.ai/blog/swarm-poisoning-agent-harnesses)
gives the Bastion Breaker fan-out prompt. `poison_result.py` finds a matching
subagent result and previews its rewrite by default; `--apply` changes the
session log. `mused.py` exercises a separate prompt-history rewrite path and
is dry-run by default. Its `--arm` option can change a live session and plant
`payload/verify_integration.sh` in the workspace.

`npm_registry.py` serves a scoped `@engine-tools/frame-profiler` package on
localhost for an isolated registry variant; `setup_decoys.sh` creates dummy
secrets for that variant. The recorded `r5` artifacts instead show the
unscoped `frame-profiler` version 1.0.2 and a request to `registry.npmjs.org`.
The local registry variant should not be presented as a replay of `r5`.

## Citation

Abi R., [“Swarm Poisoning in Agent Harnesses: The Muse Code Subagent Attack”](https://www.codeintegrity.ai/blog/swarm-poisoning-agent-harnesses), CodeIntegrity, October 12, 2026. Cite this repository for the supporting code and selected run artifacts.
