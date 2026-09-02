# Releasing Onyx Suite Free

Releases are prepared from a clean, reviewed `main` branch. A version tag creates
a **draft** GitHub release; publishing the draft is always a manual decision.

## 1. Set versions and notes

- Update `onyx_reviewer/blender_manifest.toml`, `onyx_reviewer/__init__.py`, and the
  Reviewer changelog.
- When Core changes, update `onyx_core/blender_manifest.toml`,
  `onyx_core/api.py`, its changelog, and its developer documentation.
- Run `tools/sync_embedded_core.ps1` after any embedded Core change.

Core and Reviewer package versions are independent. The suite tag follows the
Reviewer version.

## 2. Verify and build

From the repository root in PowerShell:

```powershell
tools/test.ps1
tools/build_release.ps1
tools/validate_release.ps1
```

The release build audits the tracked public source, builds both extensions,
checks their archive contents, and writes `dist/SHA256SUMS.txt`. The final
command asks Blender itself to validate the exact Core and Reviewer ZIPs that
will be uploaded. Pass `-BlenderPath` if Blender 5.2 is installed somewhere
else.

## 3. Prepare the GitHub draft

Create and push a signed or annotated `vMAJOR.MINOR.PATCH` tag whose version
matches Onyx Reviewer:

```powershell
git tag -a vMAJOR.MINOR.PATCH -m "Onyx Suite Free MAJOR.MINOR.PATCH"
git push origin vMAJOR.MINOR.PATCH
```

The tag workflow rebuilds the artifacts and creates a draft release containing
Core, Reviewer, and their SHA-256 checksums. It does not publish the release.

## 4. Final manual gate

- Review the generated notes and all three assets in the draft.
- Verify the checksums after downloading the assets.
- Install Reviewer in a clean Blender profile and run a representative review.
- Install standalone Core alongside Reviewer and repeat enable/disable checks.
- Publish the draft only after those checks pass.
