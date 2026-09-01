# Onyx Review 0.5.0

Onyx Review is an independent, reversible mesh-inspection workspace for Blender
5.2 LTS. It reports source and evaluated geometry statistics, identifies common
topology and transform concerns, and provides temporary viewport review modes.

It does not repair, remesh, bake, export, or alter mesh data. The extension is
self-contained and includes the free Onyx Core runtime; no separate framework
installation is required.

## Current review checks

- Base and evaluated vertices, faces, and triangles
- Triangle, quad, and ngon face composition
- 3-edge, 5-edge, and 6+-edge topology-pole counts
- Color-coded face and pole topology maps
- Focused highlights and exact selection for every face and pole class
- Open boundaries and edges connected to more than two faces
- Degenerate faces and inconsistent face winding
- Duplicate faces occupying the same vertex positions
- Loose vertices and edges, plus coincident unwelded vertices
- Additional disconnected mesh islands
- Ngons
- Negative or unapplied scale
- Missing UV maps and material slots
- Optional evaluated triangle budget
- Direct element selection for actionable topology findings
- Distinct, through-surface viewport colors for every actionable finding type
- Thicker lines and larger points for error-level findings
- Combined per-object overview of all actionable findings
- Copyable plain-text review report
- Optional debounced Live Review after mesh changes
- Automatic Live Review pause in Edit Mode and above a configurable source-vertex limit
- Explicit, undoable fixes for winding, exact duplicate faces, loose edges, and loose vertices

## Live Review

Enable **Live Review** in Review Options when you want diagnostics to follow a
modeling pass. It refreshes the same inspection-only results after detected mesh
changes settle. It does not repair or otherwise edit geometry.

Live Review pauses while a target is in Edit Mode, because the editable mesh may
not yet match its stored object data. It also pauses when the chosen scope
exceeds the **Live Vertex Limit**. Use zero only when you deliberately want no
density ceiling. The manual **Run Now** action remains available at all times.

## Simple fixes

Supported findings show a **Fix** button for four deterministic operations:

- Recalculate inconsistent face winding
- Remove redundant faces whose vertex positions match exactly
- Delete edges that are not used by a face
- Delete vertices that are not connected to an edge

Every fix is explicit, creates one Blender undo step, and refreshes the review.
There is no automatic cleanup pass. Onyx does not offer generic fixes for holes,
ngons, coincident vertices, disconnected islands, transforms, UVs, or materials.
Fixes are also refused for linked data, multi-user meshes, and meshes with shape
keys so a local cleanup cannot silently affect another asset state.

## Viewport modes

- Studio
- Silhouette
- Topology wire overlay
- Face Orientation

The first mode used in a viewport captures its settings. **Restore View** returns
those settings exactly, and disabling the extension restores every remaining
captured viewport.

## Install

Build `onyx_review-0.5.0.zip` with `tools/package_review.ps1`, then install the
archive through **Edit > Preferences > Get Extensions > Install from Disk**.
Open **Onyx > Review** in the 3D Viewport sidebar.
