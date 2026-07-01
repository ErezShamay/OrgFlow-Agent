# docs/

The main [`README.md`](../README.md) links to several planning/spec documents
that were referenced under this directory (`PRODUCT-SPEC-LOCKED.md`,
`FIELD-REPORT-FINALIZE-PIPELINE.md`, `COMPETITIVE-LAYER-SPEC.md`, and others).

Those files were never committed to git: the previous `.gitignore` ignored
the entire `docs/` directory as a folder (`docs/`) before an attempted
`!docs/*.md` negation — a well-known git gitignore limitation where a fully
ignored directory is never traversed, so negation rules for files inside it
are silently never evaluated. As a result the documents existed only in
someone's local working copy (if at all) and are not recoverable from git
history.

The `.gitignore` pattern has been fixed (`docs/*` + `!docs/*.md` instead of
`docs/` + `!docs/*.md`) so that `.md` files placed here from now on will be
tracked correctly. If the original planning documents still exist somewhere
(a teammate's machine, a shared drive, Notion, etc.), please add them back
here.
