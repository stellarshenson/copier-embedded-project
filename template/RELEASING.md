# Releasing {{ project_name }}

The version lives in `VERSION`, one file that every toolchain reads. A release increments the
patch version, moves the changelog entries under the new heading, commits both files, tags the
commit and pushes it.

## Release process

1. Run `make increment_version`
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version heading with the date
3. Commit `VERSION` and `CHANGELOG.md` with the message `chore: bump version to <version>`
4. Tag the commit `v<version>`
5. Push the commit and the tag{% if 'ci' in components %}
6. Watch the release job that the tag push starts; it checks the tag against `VERSION`, builds the
   firmware and attaches `dist/*` with the matching `CHANGELOG.md` section as the notes{% endif %}

## Rules

- Every tag carries the `v` prefix, for example `v0.1.1`
- Never delete an old tag; `copier update` resolves a template version from the tags
- Tag only after `make test`, `make test-toolchain`, `make test-functional` and `make lint` pass{% if 'ci' in components %}
- The tag must equal `v` plus the contents of `VERSION`; a mismatch fails the release job before it publishes
- A failed release job leaves the tag without a release{% endif %}
