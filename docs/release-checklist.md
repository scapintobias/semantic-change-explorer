# v0.1 release checklist

## Local candidate evidence

- [x] Real generated `.blend` pair compared through CLI.
- [x] Source hashes unchanged; autoexec sentinel absent; repeat extraction deterministic.
- [x] Rename inference, ambiguity, authored/evaluated separation and meaningful domain changes.
- [x] Both GLBs load; index/viewport selection linked; A/B/overlay/crossfade tested.
- [x] Public protocol examples, schemas, tests, docs and private learning notes present.
- [x] Actual screenshot, reproducible fixture and demo procedure.

Final test counts and packaging evidence are recorded in build-log/performance. A checked local item does not mean a public release exists.

## Before publishing

- [ ] Configure genuine Git author identity; review and commit coherent changes. Do not invent an author.
- [ ] Settle/check a public project name across GitHub/PyPI/npm and trademark context. Current name is provisional.
- [ ] Create/configure the chosen public repository only on explicit instruction, and enable private security reporting.
- [ ] Replace SECURITY.md's pending contact with the actual reporting URL.
- [ ] Run the supplied hosted workflows and review results; local passes are not hosted CI evidence.
- [x] Review supported-version claims against actual LTS/OS/browser results.
- [x] Inspect wheel/sdist for license notices, complete corresponding source, and absence of private notes.
- [x] Test installing the distribution in a fresh environment and generating a real report.
- [x] Review README claims and golden changes; document remaining limitations.
- [ ] Tag/publish only when these checks are complete and publishing has been requested.
