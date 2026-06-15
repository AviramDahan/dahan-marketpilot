# Licensing

Dahan MarketPilot source code is licensed under the MIT License unless a file
states otherwise. The root `LICENSE` file contains the project license text.

The repository uses strict attribution from day one:

- `NOTICE` records project identity and direct-copy status.
- `THIRD_PARTY_NOTICES.md` records third-party source code, examples, snippets,
  or substantial logic reused by the project.
- Substantial third-party logic must not be copied until the source, license,
  reuse scope, attribution requirement, and affected files are recorded.

QuantConnect LEAN and official QuantConnect examples are Apache-2.0 sources.
They may be used as official references, but copied source or substantial
adapted logic must be attributed according to Apache-2.0 requirements and
recorded in `THIRD_PARTY_NOTICES.md`.

Do not claim that Dahan MarketPilot as a whole is Apache-2.0 merely because it
integrates with or references QuantConnect materials. Re-check license
requirements before copying code from any third-party source.

## Release Attribution Review

Before a release ships, review every direct-copy item and every substantially
adapted third-party source introduced since the previous release.

Required review phrase: substantially adapted third-party source.

For each copied or substantially adapted source, update `NOTICE` and
`THIRD_PARTY_NOTICES.md` before or in the same commit that introduces the reused
material. Record the source URL, version or commit when available, license,
reuse type, required attribution text, and affected project files.

If no third-party source was copied or substantially adapted, keep
`THIRD_PARTY_NOTICES.md` explicit that third-party source code has not been
directly copied.
