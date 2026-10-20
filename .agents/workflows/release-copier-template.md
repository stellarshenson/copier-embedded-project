# Release Copier Template

Release a new version of the copier-embedded-project template.

## Instructions

1. Read `pyproject.toml` and find the current version.
2. When the working tree has uncommitted changes that the `[Unreleased]` section of `CHANGELOG.md`
   does not describe, add a bullet for them under `[Unreleased]`.
3. Run `make increment_version` to increment the patch version.
4. Move the `Unreleased` entries of `CHANGELOG.md` under the new version heading with the release
   date.
5. Commit every uncommitted change with `chore: bump version to <new_version>`.
6. Create the tag `v<new_version>`.
7. Push the commit and the tag to `origin main`.

**IMPORTANT**: Never delete an old tag. `copier update` resolves template versions from the tags.

Running this command approves the version bump, the commit, the tag and the push of this release.
Do all seven steps without asking. Stop and ask only when something unexpected happens:

- there is nothing to release: the working tree is clean and `[Unreleased]` is missing or empty
- `main` has diverged from `origin/main`
- a command fails or the push is rejected
