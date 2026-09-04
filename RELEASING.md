# Releasing Onyx Suite Free

Releases start from a clean, reviewed `main` branch. A suite version tag creates
a **draft** GitHub release. Publishing that draft is always a manual decision.

## 1. Update the products that changed

- Update each changed product's `blender_manifest.toml`, runtime version, and
  changelog.
- When Core changes, update its API version, developer guide, and changelog,
  then run `tools/sync_embedded_core.ps1`.
- Make sure every public product is listed once in
  `tools/public_products.txt`, with Core first.

Product versions are independent. The suite tag is the version of the combined
GitHub release, so it does not have to match Reviewer, Core, or any future addon.

## 2. Verify and build

From the repository root in PowerShell:

```powershell
tools/test.ps1
tools/build_release.ps1
tools/validate_release.ps1
```

The release build audits the tracked public source, packages every product in
`tools/public_products.txt`, inspects every archive, and writes
`dist/SHA256SUMS.txt`. The final command asks Blender to validate those exact
ZIPs. Pass `-BlenderPath` if Blender 5.2 is installed somewhere else.

## 3. Create the draft

Choose the next suite version and push a signed or annotated
`vMAJOR.MINOR.PATCH` tag:

```powershell
git tag -a vMAJOR.MINOR.PATCH -m "Onyx Suite Free MAJOR.MINOR.PATCH"
git push origin vMAJOR.MINOR.PATCH
```

The tag workflow rebuilds the complete public suite and creates a draft release
with one labeled ZIP per product plus the SHA-256 checksums. It does not publish
the release.

## 4. Final manual check

- Review the generated notes and every asset in the draft.
- Download the ZIPs and verify their checksums.
- Install each changed artist-facing product in a clean Blender profile and run
  a representative workflow.
- Install standalone Core beside the products and repeat enable/disable checks.
- Check that the root README direct-download links point to the new assets.
- Publish the draft only after those checks pass.

## Adding another free addon later

Give it an `onyx_<name>` directory, a valid Blender manifest, a README that says
Core is included, and a bundled `_onyx_core` runtime. Add its ID to
`tools/public_products.txt` and add its product page and direct download to the
root README.

The generic packager handles a standard product automatically. Add a focused
`tools/package_<name>.ps1` wrapper only when that addon needs extra required-file
checks. The CI artifact and GitHub release workflows discover it from the public
product catalog.
