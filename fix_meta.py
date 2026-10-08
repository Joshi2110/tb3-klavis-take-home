import re, pathlib
p = pathlib.Path("tasks/telemetry-archive-reconcile/README.md")
if not p.exists():
    p = pathlib.Path("README.md")
s = p.read_text()
s = re.sub(r"\n## Task Metadata\n.*?(?=\n## |\Z)", "\n", s, flags=re.S).rstrip("\n") + "\n"
meta = """## Task Metadata

- **Author:** Josh Adjedj (joshuaadjedj@gmail.com)
- **Category:** `Software`
- **Tags:** <code>distributed-systems</code> <code>state-machine</code> <code>crash-recovery</code> <code>ground-segment</code>
- **Expert time:** 6 hours
- **Agent timeout:** 8 hours
- **CPUs:** 4
- **Memory:** 8 GB

See [instruction.md](instruction.md) for the full task instruction. Additional information on the task environment and verifier can be found in [task.toml](task.toml).

"""
s = s.replace("\n## Difficulty explanation", "\n" + meta + "## Difficulty explanation", 1)
p.write_text(s)
print("ok", p)
