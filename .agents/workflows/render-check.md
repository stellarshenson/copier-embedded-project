---
description: Render the template matrix and run the fast template tests
---

Render and test `copier-embedded-project`.

1. Run `make test` in the template repository.
2. When it fails, read the failing render under the temporary directory or rerun the single test
   with `-k`.
3. If the failure is in a rendered file, fix `template/` or `scripts/post_gen.py`; never edit a
   rendered project.
4. Report the test summary and the first failure with its message.
