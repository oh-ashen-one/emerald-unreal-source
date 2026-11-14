# Public source publication checks

This repository starts with a clean source-only history. The private authoring history, session notes, evidence runs, source checkouts, generated game data, concept/reference images, ROMs/saves, graphics/audio, third-party native/raw assets, binaries and packaged builds are excluded. No asset is made open source merely because it was free to acquire.

The publication inventory contains only UTF-8 source/configuration/documentation/provenance files. Every file is below 100 MB. Review both tracked bytes and every reachable Git object: `.gitignore` alone does not remove committed content. Never commit generated `Content`, `out`, `Saved`, `Intermediate`, `DerivedDataCache`, `.app` or credential files.

Gitleaks 8.30.1 uses the default provider rules plus the shared Netlify PAT rule in `.gitleaks.toml`. Three generic-api-key candidates were independently recomputed against the pinned source checkout: the SHA256 entries for `data/scripts/secret_base.inc` in both source lock files and `include/constants/secret_bases.h` in the event lock. The configuration excepts only complete JSON lines with those exact paths and 64 hexadecimal digest characters. No source-file contents or credentials are included in that exception. Recheck hashes and scope whenever those ledgers change.

Before publishing, scan staged bytes, all reachable history and an independently enumerated reachable-blob export. Review privacy, licenses, file types/sizes and commit identity separately. Keep raw scanner evidence private. The public author identity uses the account's GitHub noreply address. This audit covers the published source snapshot, not external sites or separately acquired assets.
