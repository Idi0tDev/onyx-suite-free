# Onyx Core Release Checklist

## Versions and source

- [ ] Update the Core manifest, `api.py`, changelog, and developer guide when
  the Core package changes.
- [ ] Keep the Core package version and API version independent; change the API
  major only for an intentionally incompatible public contract.
- [ ] Update the Review manifest, runtime `VERSION`, and changelog when Review
  changes.
- [ ] Run `tools/sync_embedded_core.ps1` after every embedded Core change.

## Automated verification

- [ ] Run `tools/check_public_source.ps1` and resolve every finding.
- [ ] Run `tools/test.ps1` with Blender 5.2 LTS.
- [ ] Confirm the pure framework, Review analysis, embedded Core, Blender smoke,
  Review smoke, and Core/Review coexistence tests all pass.

## Packages

- [ ] Run `tools/build_release.ps1`.
- [ ] Confirm `dist` contains the Core ZIP, Reviewer ZIP, and
  `SHA256SUMS.txt`.
- [ ] Validate both generated ZIPs with Blender's `extension validate`.
- [ ] Install Reviewer into a clean Blender profile and run a representative
  review on a mesh with actionable findings.
- [ ] Install standalone Core alongside Reviewer and repeat the enable/disable
  cycle.
- [ ] Follow the repository-level `RELEASING.md` manual draft-release gate.
