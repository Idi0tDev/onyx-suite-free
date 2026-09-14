<p align="center">
  <img src="../docs/assets/onyx-reviewer-hero.png" alt="Onyx Reviewer scanning a mesh and identifying geometry problems" width="100%">
</p>

<h1 align="center">Onyx Reviewer</h1>

<p align="center">
  Find mesh problems, see where they are, and decide how you want to fix them.
</p>

<p align="center">
  <a href="https://github.com/Idi0tDev/onyx-suite-free/releases/download/v1.0.1/onyx_reviewer-1.0.1.zip"><img alt="Download Onyx Reviewer 1.0.1" src="https://img.shields.io/badge/Download-Onyx%20Reviewer-e85d04?style=for-the-badge&logo=blender&logoColor=white"></a>
</p>

Onyx Reviewer checks the editable mesh and the evaluated modifier result, then
points to useful evidence directly in Blender's 3D Viewport. It is meant to help
you understand a mesh—not make creative decisions for you.

Running a review does not change the mesh. Reviewer does not remesh, bake,
export, or quietly repair anything. The ZIP includes the free Onyx Core runtime,
so there is no second dependency to install.

## See it in action

### Find a problem and get a useful suggestion

Run a review to see different problem types in their own colors. Rest the
pointer over a mark to see what it means and a practical way to approach it.

<p align="center">
  <img src="../docs/assets/onyx-reviewer-findings-and-guides.gif" alt="Onyx Reviewer scanning a mesh, showing color-coded problems, and explaining them on hover" width="100%">
</p>

### Keep checking while you model

Live Review follows Edit Mode changes and removes a highlight once the next
scan confirms that problem is gone.

<p align="center">
  <img src="../docs/assets/onyx-reviewer-live-review.gif" alt="Onyx Reviewer updating its findings while a topology problem is fixed in Edit Mode" width="100%">
</p>

### Look at the mesh in a few useful ways

Switch between form, silhouette, topology, and face-direction views, then put
the viewport back exactly as it was.

<p align="center">
  <img src="../docs/assets/onyx-reviewer-viewport-modes.gif" alt="Onyx Reviewer switching between its viewport inspection modes and restoring the original view" width="100%">
</p>

## Install

1. **[Download Onyx Reviewer 1.0.1](https://github.com/Idi0tDev/onyx-suite-free/releases/download/v1.0.1/onyx_reviewer-1.0.1.zip)** and leave the ZIP packed.
2. In Blender, open **Edit → Preferences → Get Extensions**.
3. Open the menu in the top-right and choose **Install from Disk**.
4. Pick the downloaded `onyx_reviewer-<version>.zip` and confirm the installation.
5. Open **Onyx → Review** in the 3D Viewport sidebar.

Blender shows that Reviewer needs clipboard access. It uses that permission only
when you press **Copy Report** or **Copy Delta**. Reviewer does not need network
or file access.

## A simple first review

1. Select a mesh.
2. Open the **Onyx** tab in the 3D Viewport sidebar.
3. Choose a review profile. **General** is a good first look.
4. Press **Run Review**.
5. Use **Show Problems** for an overview or the arrow buttons to step through
   one problem at a time.
6. Hover over a colored mark or press **Guide** when you want a suggested next
   step.

Enable **Live** when you want the results to follow a modeling pass. Turning it
on runs the first scan automatically.

### If both Reviewer editions are enabled

You can keep both editions installed. While Onyx Reviewer Pro is enabled, this
Reviewer's panel, Live Review, and viewport marks pause so the two tools never
draw or scan over each other. Nothing is deleted. Disable Pro and this panel
comes back automatically; if Live was on, Reviewer starts with a fresh scan.

## What Reviewer checks

<details open>
<summary><strong>Mesh and topology</strong></summary>

- Base and evaluated vertex, face, and triangle counts
- Triangles, quads, ngons, and 3/5/6+ edge poles
- Open holes and edges connected to more than two faces
- Degenerate, duplicate, crossing, and overlapping faces
- Bent faces whose triangles no longer agree on one flat surface
- Inconsistent winding and faces pointing against their connected neighbors
- Loose geometry, coincident unwelded vertices, and disconnected islands
- Exact selection and color-coded evidence for actionable findings

</details>

<details>
<summary><strong>Transforms, asset setup, and budget</strong></summary>

- Negative transforms and unapplied scale
- Missing UV maps and material slots
- Optional evaluated triangle budget
- Optional allowances for intentionally open holes and ngons

</details>

Review findings describe facts, not universal rules. An open hole can be a
mistake on a closed prop and completely intentional on cloth, cards, or trim.

## Review profiles

- **General** runs every current finding group.
- **While Modeling** focuses on topology and transforms without complaining
  about unfinished UVs, materials, or a triangle budget.
- **Topology Only** keeps the review on mesh structure.
- **Custom** lets you choose the finding groups yourself.

Geometry totals, face mix, and pole counts remain visible in every profile.
Changing the profile, scope, custom switches, or triangle budget clears the
temporary Review Delta baseline so two different sets of rules are not compared
as if they were the same review.

If an asset is intentionally open or contains a few ngons, open **More Settings
→ Topology Limits** and enter what is acceptable. This is also where you can
adjust the **Non-Planar Angle**. Its conservative 90° default keeps the first
scan quiet; lower it when a job needs stricter flat-face checks.

## Pick colors that work for you

Open **More Settings → Problem Colors** to choose **Onyx**, **High Contrast**,
or **Colorblind Safe**. Any marks already on the mesh change immediately, and
the little dots in the panel always show the colors you will see in the
viewport.

This is only a display choice. Switching palettes does not scan again, change
the result, or affect a saved Review Delta baseline.

## Live Review

Press **Live** beside the main Review button when you want diagnostics to follow
your changes. Reviewer waits for editing to settle, then refreshes the same
inspection-only results in Object Mode or Edit Mode without changing the mode or
selection.

A visible problem overview, focused highlight, face map, or pole map is rebuilt
from the latest scan instead of disappearing. Reviewer reuses the evidence it
just collected, so drawing the colors does not scan the mesh a second time.

Live Review pauses when the chosen scope goes over the configurable **Live
Vertex Limit**. The manual **Run Now** button remains available.

## Finding view and guides

The compact **Show** menu can display everything, only errors, only warnings,
problems that can be drawn on the mesh, or findings that changed since a saved
baseline. **Copy Report** still includes the complete review.

Use the arrow buttons to walk through visible mesh problems. Reviewer selects
the matching object, opens its result card, and draws the right evidence. The
navigator wraps around when it reaches the end.

Every finding has a plain-language **Guide**. Drawable findings show the same
advice when you hover over their colored marks in the viewport. These are
recommendations, not automatic repairs.

## Review Delta

A baseline is a temporary before snapshot:

1. Run Review.
2. Press **Save Baseline**.
3. Make your changes.
4. Run Review again.

Reviewer shows what appeared, disappeared, or changed, plus the evaluated
triangle difference. **Copy Delta** creates a plain-text comparison for notes or
handoff. The baseline stays in memory for the current Blender session and is not
saved in the `.blend` file.

## Viewport modes

Open **Viewport Modes** for Studio, Silhouette, Topology, and Face Orientation.
The first mode used in a viewport saves its settings. **Restore View** puts them
back exactly, and disabling Reviewer restores any remaining saved viewports.

## Built to leave the scene alone

- No automatic mesh repair
- No hole filling, remeshing, merging, or transform application
- No material replacement
- No export or pipeline assumptions
- No downloads, accounts, telemetry, or background network access
- No permanent viewport changes

For a relaxed first walkthrough, follow the
[beginner tutorial](docs/TUTORIAL.md). For every control and more interpretation
help, read the [full user guide](docs/USER_GUIDE.md). For common installation
and workflow questions, see
[Troubleshooting and FAQ](../docs/TROUBLESHOOTING.md).

<details>
<summary><strong>Build the current source</strong></summary>

From a clean checkout, use Blender's extension builder:

```powershell
blender --command extension build --source-dir onyx_reviewer --output-filepath onyx_reviewer-1.0.1.zip
```

The result is the same ready-to-install ZIP linked above. If `blender` is not
available as a terminal command, use the full path to your Blender executable.

</details>
