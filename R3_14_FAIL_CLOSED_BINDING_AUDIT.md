# R3.14 Fail-Closed Binding Audit

Local candidate test environment result:

`BLOCKED_R314_EXACT_V061_SEALED_PAYLOAD_NOT_FOUND`

This is expected in the current ChatGPT runtime because the historical v0.6.1 sealed byte payload is not mounted. The blocker is evidence that R3.14 correctly refuses to substitute the development/book-era preview boundary.

The same candidate passed **18/18** immediate R3.14 + R3.13 + R3.12 tests and **59/59** formal candidate audit checks.

No biology was advanced. No scientific authority was changed.

The Windows runner searches the current project root and its parent Arcana directories, including ZIP members, and accepts a source only after all five frozen hashes match. A wider location can be supplied with `-SearchRoot`.
