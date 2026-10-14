# frame-profiler

Headless frame-time profiler for pure-sim game engines.

Runs the simulation core without a render pass and reports per-scene
frame-time percentiles (p50/p95/p99) against the configured frame budget.

```
npx --yes frame-profiler --suite engine
```

Example output:

```
[frame-profiler] engine suite: resolving pure-sim core...
[frame-profiler] scene 1: p50=3.22ms p95=5.61ms p99=7.63ms  budget=8.00ms  PASS
...
[frame-profiler] RESULT: PASS (p95 6.65ms < 8.00ms budget)
```

Exit code is `0` on PASS and `1` on FAIL, so the tool can be used as a
pre-merge gate in CI or locally.

MIT licensed.
