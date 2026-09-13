# bingenroo apps — self-hosted SideStore source

Public distribution point for two **private** apps. Source code never lands here;
only unsigned `.ipa` release assets and the `source.json` that points at them.

## Add to SideStore

Settings → Sources → **+** → paste:

```
https://raw.githubusercontent.com/bingenroo/sidestore-apps/main/source.json
```

## What lives here

| Path | Purpose |
| --- | --- |
| `source.json` | The AltStore-format source SideStore reads. Patched by CI on every release. |
| `apps.template.json` | Static per-app metadata. CI copies an entry in the first time an app is published. |
| `scripts/patch_source.py` | Called by CI to insert a new version and refuse a non-increasing one. |
| `icons/` | App icons referenced by `iconURL`. |
| Releases | The `.ipa` files themselves, one release per version tag. |

## Apps

| App | Bundle ID | Source repo (private) | Framework |
| --- | --- | --- | --- |
| Slote | `io.slote` | `bingenroo/slote` | Flutter |
| hd-reborn | `com.hdreborn.game` | `bingenroo/hd-reborn` | Godot 4.7.1 |

## Versioning

Versions are `0.0.N`, starting at **0.0.1** and only ever counting up. The git tag
`v0.0.N` in the source repo is the single source of truth; the workflow injects it
into `pubspec.yaml` / `export_presets.cfg` at build time.

**Rollbacks ship old code under a higher version.** To go back to the code in
`v0.0.7` you publish it as `v0.0.12` — you never re-publish a lower number.
`patch_source.py` hard-fails if you try, because SideStore compares version
strings and would simply not offer the downgrade as an update.

## The IPAs are unsigned

That is deliberate. SideStore re-signs on device with your free Apple ID. Do not
try to install these with anything that expects a signed payload.
