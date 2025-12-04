---
name: Bug Report
about: Report a bug or unexpected behavior in Axion-HDL
title: '[BUG] '
labels: bug
assignees: ''
---

## Description

A clear and concise description of the bug.

## Steps to Reproduce

1. Create a VHDL file with...
2. Run `axion-hdl ...`
3. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Error Message (if applicable)

```
Paste the full error message here
```

## Environment

- **Axion-HDL Version**: (run `axion-hdl --version`)
- **Python Version**: (run `python --version`)
- **OS**: (e.g., Ubuntu 22.04, Windows 11)
- **Installation Method**: (pip, source, etc.)

## Minimal Reproducible Example

### VHDL Input

```vhdl
-- Minimal VHDL that triggers the bug
signal example : std_logic; -- @axion(...)
```

### Command Used

```bash
axion-hdl -s ./src -o ./output --all
```

## Additional Context

Add any other context about the problem here. Screenshots, logs, etc.

## Possible Fix (optional)

If you have an idea of what might be causing the issue or how to fix it.
