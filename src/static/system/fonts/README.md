# EOD interface font assets

The canonical user-interface family is **Onest Variable**.

Acceptance candidate source:

```text
repository: https://github.com/simpals/onest
revision: f18c06a14512e43a6191849278d6f07fdaf347d6
asset: fonts/webfonts/Onest[wght].woff2
asset blob SHA: b51a07004395581db33a5213c39810c7f0427fe2
license: SIL Open Font License 1.1
```

The development candidate uses a pinned CDN representation of that exact upstream revision. Before an offline or production package is accepted, copy the exact WOFF2 asset into this directory, preserve the upstream `OFL.txt`, change `@font-face` to the local static URL and verify its SHA-256 in the release manifest.

Do not commit arbitrary desktop font files, converted files or modified files under the reserved Onest name.
