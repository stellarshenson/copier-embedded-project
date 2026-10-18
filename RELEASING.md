# Releasing copier-embedded-project

## Version scheme

The project uses semantic versioning: `MAJOR.MINOR.PATCH`, with the patch incremented for each
release.

## Release process

1. **Increment the version**

   ```bash
   make increment_version
   ```

2. **Update CHANGELOG.md** - move the `Unreleased` entries under the new version heading with the
   release date

3. **Commit and tag**

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to $(grep -oP 'version = "\K[^"]+' pyproject.toml)"
   git tag v$(grep -oP 'version = "\K[^"]+' pyproject.toml)
   ```

4. **Push**

   ```bash
   git push origin main --tags
   ```

## Rules

- Never delete an old tag; `copier update` resolves a template version from the tags
- Every tag carries the `v` prefix, for example `v1.0.13`
- Tag only after `make test`, `make test-toolchain`, `make test-functional` and `make lint` pass
- The first release tags the initial commit; it needs no version increment when `pyproject.toml`
  already names the release version
