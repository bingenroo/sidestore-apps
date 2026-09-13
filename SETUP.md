# Setup and operations

Everything here is done once, from the Mac, **before** travelling. After that the
loop is phone-only.

---

## 1. The fine-grained PAT

The two private repos push release assets into this public repo, which is a
cross-repository write, so `GITHUB_TOKEN` cannot do it. One fine-grained PAT
covers both.

Create it at **Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token**.

| Field | Value |
| --- | --- |
| Token name | `sidestore-dist` |
| Resource owner | `bingenroo` |
| Expiration | Custom — set it past your return date |
| Repository access | **Only select repositories** → `bingenroo/sidestore-apps` |

Permissions — **Repository permissions** only, and only these two:

| Permission | Access | Why |
| --- | --- | --- |
| **Contents** | **Read and write** | Creates the release, uploads the `.ipa` asset, commits the patched `source.json` |
| **Metadata** | Read-only | Mandatory; GitHub adds it automatically and it cannot be removed |

Leave **everything else on "No access"**. In particular you do *not* need
Actions, Workflows, Administration, Pull requests, Issues, Deployments, Secrets,
Packages, Pages, or any Account permission. The token never touches the private
source repos — only this public one — so a leak exposes nothing that was not
already public.

Then store it as a secret in **each private repo** (paste the token when
prompted; it is never echoed):

```sh
gh secret set DIST_REPO_TOKEN --repo bingenroo/slote
gh secret set DIST_REPO_TOKEN --repo bingenroo/hd-reborn
```

**Set a calendar reminder for the expiry date.** An expired PAT fails the
publish step *after* the build has already burned its macOS minutes.

---

## 2. Cost: how many builds fit in the free allowance

GitHub Free gives 2,000 included Actions minutes per month on a personal
account. Private repositories consume them; macOS runners bill at a **10x
multiplier**, and every job is **rounded up to the whole minute**.

```
2,000 included units ÷ 10 (macOS multiplier) = 200 macOS wall-minutes / month
```

Both pipelines were timed on an Apple Silicon Mac before these numbers were
written. GitHub's `macos-15` runners are 3-core and meaningfully slower, so the
CI column below is the local measurement scaled up, plus checkout, cache
restore, toolchain setup and upload.

| App | Measured locally | Expected on `macos-15` | Units charged |
| --- | --- | --- | --- |
| Slote (Flutter) | 67 s compile → 22 MB `.ipa` | 6–9 min warm, 11–14 min cold | 60–140 |
| hd-reborn (Godot) | 4 s export + 4 s link → 26 MB `.ipa` | 4–6 min warm, 12–16 min cold | 40–160 |

Slote dominates the budget: Flutter compiles a large Dart/ObjC tree, while
Godot ships a prebuilt static library so Xcode has almost nothing to compile.
hd-reborn's cost is almost entirely *downloading* Godot and its iOS export
template, which is exactly what the cache exists to avoid.

**Realistic combined budget: 20–30 builds per month**, and comfortably 15+ even
if every cache is cold. The caches carry the Flutter SDK, pub packages,
CocoaPods, and the Godot editor + iOS template; the template download is
trimmed from the full 1.9 GB `.tpz` to just `ios.zip` + ICU data (~200 MB) so
the cache restores quickly. Caches evict after 7 days unused, so a month of two
widely spaced builds costs noticeably more than a month of six.

**Your Actions spending limit is $0, which is correct and should stay that way.**
It means that when the 2,000 units are gone, workflow runs on the private repos
are *rejected* rather than billed. You will see "run failed to start", not an
invoice. Check the remaining balance from your phone at
**github.com → Settings → Billing and licensing**.

Two notes on keeping inside it:

- Tag-push-only triggering is the main saving. Nothing builds on an ordinary
  commit, and `concurrency` stops two tags racing into two parallel macOS jobs.
- `timeout-minutes` (45 for Slote, 60 for hd-reborn) is a blast-radius cap, not
  a target. A hung job would otherwise run for 6 hours and eat 3,600 units —
  eighteen times your monthly allowance in one go.

---

## 3. The phone-only build loop

No Mac, no local git, no terminal:

1. github.com → the private repo → **Actions** → **Build iOS IPA (SideStore)**
2. **Run workflow** → optionally type release notes → **Run workflow**
3. The workflow works out the next version itself (highest `v0.0.N` + 1),
   creates and pushes the tag, builds, uploads the `.ipa` to this repo's
   releases, and patches `source.json`
4. On the device: SideStore → **Sources** → pull to refresh → the app shows an
   **Update**

The mobile GitHub *app* does not expose `Run workflow`; use **github.com in
Safari** and request the desktop site if the button does not appear.

From a Mac, the same thing with history and rollback support:

```sh
bin/bump-ios.sh                     # build HEAD as the next version
bin/bump-ios.sh --rollback v0.0.3   # re-ship v0.0.3's code as the next version
bin/bump-ios.sh --dry-run           # show what would happen
```

---

## 4. Versioning and rollbacks

Versions are `0.0.N`, starting at **0.0.1**, and they only count up. The git tag
in the source repo is the single source of truth; the workflow stamps it into
`pubspec.yaml` (Slote) or the iOS preset of `export_presets.cfg` (hd-reborn) at
build time, so the committed version numbers are placeholders and never need
hand-editing.

A rollback **never lowers the number**. To go back to what shipped as `v0.0.7`
when `v0.0.11` is current, you publish `v0.0.7`'s tree as **`v0.0.12`**.
`bin/bump-ios.sh --rollback v0.0.7` does exactly that: it resets the tree to the
old commit's content, commits that as a normal forward commit, and tags it with
the next number.

This is not stylistic. SideStore decides an update exists by comparing version
strings, so a lower number is simply never offered, and the old build stays on
the device with no way to move it. `scripts/patch_source.py` refuses a
non-increasing version as a second line of defence, failing the publish step
loudly rather than writing a `source.json` that looks fine and does nothing.

---

## 5. Pre-departure verification

Do all of this **on both the iPhone and the iPad**, on your home network, while
the Mac is still reachable. Every one of these is a thing that fails silently
later.

### Signing and SideStore health

- [ ] SideStore is installed on both devices and both show the **same Apple ID**.
- [ ] Each device has a valid **pairing file** loaded in SideStore. This is the
      one thing that genuinely needs the Mac to create, and it is the single
      most common reason a refresh fails abroad. Regenerate both now even if
      they look fine.
- [ ] **StosVPN** (or your anisette/WireGuard equivalent) is installed,
      enabled, and connects on cellular data with Wi-Fi turned off — not just on
      home Wi-Fi. Hotel and airport networks block far more than your home
      router does.
- [ ] Tap **Refresh All** in SideStore on each device and watch it complete.
      Certificates last 7 days; confirm you can renew without a computer *before*
      you are somewhere without one.
- [ ] Note the **certificate expiry date** shown in SideStore on each device.

### App-slot budget — you are exactly at the limit

A free Apple ID allows **3 sideloaded apps per device**, and **SideStore itself
counts as one**. SideStore + Slote + hd-reborn = 3. There is no spare slot.

- [ ] Confirm no other sideloaded app is installed on either device. If one is,
      remove it now — discovering this when an install silently fails in a hotel
      is the bad version of this problem.
- [ ] Remember the **10 App IDs per 7 days** cap. Installing both apps on both
      devices costs App IDs on first install only; refreshing an app that is
      already installed reuses its App ID and costs nothing. Do not spend the
      budget experimenting the day before you fly.

### End-to-end dry run

- [ ] Add the source on both devices:
      `https://raw.githubusercontent.com/bingenroo/sidestore-apps/main/source.json`
- [ ] Install **both apps on both devices** from the source and launch each one.
- [ ] Trigger one real `workflow_dispatch` build **from the phone**, with the
      Mac untouched, and confirm the new version appears and installs as an
      update on both devices. This rehearses the exact loop you will rely on.
- [ ] Confirm the apps still launch after a device **reboot** — a reboot is what
      surfaces a bad signature.

### Things that will not fix themselves abroad

- [ ] **PAT expiry** is after your return date (section 1).
- [ ] Enough **Actions minutes** remain for the trip (section 2). Note the
      monthly reset date.
- [ ] **hd-reborn talks to a server.** Confirm the client points at a host that
      is reachable from outside your home network, or that the build you carry
      works offline. A LAN address baked into the build is useless in a hotel.
- [ ] Both apps' data survives a reinstall, or you have exported anything you
      cannot lose. A failed re-sign is sometimes resolved by deleting and
      reinstalling, which takes the app's data with it.
