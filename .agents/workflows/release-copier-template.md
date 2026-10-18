# Release Copier Template

Release a new version of the copier-embedded-project template.

## Instructions

1. Read `pyproject.toml` and find the current version.
2. Run `make increment_version` to increment the patch version.
3. Move the `Unreleased` entries of `CHANGELOG.md` under the new version heading with the release
   date.
4. Commit `pyproject.toml` and `CHANGELOG.md` with `chore: bump version to <new_version>`.
5. Create the tag `v<new_version>`.
6. Push the commit and the tag to `origin main`.

**IMPORTANT**: Never delete an old tag. `copier update` resolves template versions from the tags.

Ask the Star Colonel for approval before the commit, the tag and the push. Each needs explicit
approval.
