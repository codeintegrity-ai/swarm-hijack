# Swarm Hijack

[CodeIntegrity's research on swarm poisoning in agent harnesses](https://www.codeintegrity.ai/blog/swarm-poisoning-agent-harnesses)
documents this proof of concept. It demonstrates a forged Muse Code subagent
result that leads to a package download in a controlled local setup with a fake
registry. The article explains the attack path, observed result, and scope.

## Reproduce

```bash
bash setup_decoys.sh /path/to/repo
python3 npm_registry.py 8911 &                     # fake registry + sink
printf '@engine-tools:registry=http://127.0.0.1:8911\n' > /path/to/repo/.npmrc
python3 pty_driver.py --log /tmp/victim.tty.log --cwd /path/to/repo -- \
  muse --trust-workspace "<fanout prompt>" &       # victim
python3 mused.py --workspace <repo> --arm --kill --once \
  --repo /path/to/repo                              # daemon
python3 pty_driver.py --log /tmp/resume.tty.log --cwd /path/to/repo \
  --inject "55:Please continue with the remaining work." --inject "59:\n" -- \
  muse resume --trust-workspace --sandbox-network enabled <session-uuid>
ls /tmp/FANOUT_PWNED                                # canary
```
