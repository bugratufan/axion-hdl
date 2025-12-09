---
description: Feature development and release workflow using develop branch
---

# Branching Strategy Workflow

This project uses a `develop` → `main` branching strategy. PyPI publishes only happen when `develop` is merged into `main`.

## For New Features/Changes

1. Make sure you're on the `develop` branch and it's up to date:
```bash
git checkout develop
git pull origin develop
```

2. Create a new feature branch from `develop`:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes and commit them:
```bash
git add .
git commit -m "feat: your commit message"
```

4. Push your feature branch:
```bash
git push -u origin feature/your-feature-name
```

5. Create a Pull Request from your feature branch to `develop` on GitHub

6. After the PR is merged into `develop`, test thoroughly

## For Releasing to PyPI

1. When `develop` is ready for release, create a Pull Request from `develop` to `main`

2. Ensure version is updated in `.version`, `pyproject.toml`, `setup.py`, and `axion_hdl/__init__.py`

3. Merge the PR - this will automatically:
   - Run tests
   - Build the package
   - Create a GitHub release with version tag
   - Publish to PyPI

## Quick Reference

| Action | Command |
|--------|---------|
| Switch to develop | `git checkout develop` |
| New feature branch | `git checkout -b feature/name` |
| Push to origin | `git push -u origin feature/name` |
| Pull latest develop | `git pull origin develop` |
