---
name: Bug report
about: Report incorrect drift detection or a crash
title: ""
labels: bug
assignees: ""
---

**What happened**
A clear description of the problem.

**Minimal reproduction**
The samples you learned from, and the payload you checked:

```python
import contractguard as cg

contract = cg.learn([...])      # the samples
report = contract.check(...)    # the payload
print(report)
```

**Expected result**
What you expected the report to say.

**Actual result**
What the report actually said.

**Environment**
- contractguard version: (run `pip show contractguard`)
- Python version:
- OS:
