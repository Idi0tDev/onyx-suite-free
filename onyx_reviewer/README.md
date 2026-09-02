# Onyx Reviewer 0.11.0

Onyx Reviewer helps you spot mesh problems before they become annoying production
problems. It checks the editable mesh and the evaluated modifier result, then
points to useful evidence directly in Blender's 3D Viewport.

Running a review does not change the mesh. Onyx does not remesh, bake, export,
or quietly repair anything. The extension includes the free Onyx Core runtime,
so there is no second dependency to install.

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
- Previous and next navigation through the currently visible mesh problems
- All, Errors, Warnings, Fixable, and Changes finding views for dense reviews
- Session-only before-and-after Review Delta comparisons
- General, While Modeling, Topology Only, and Custom review profiles
- Optional allowances for intentionally open boundary edges and ngons
- Copyable plain-text review report
- Optional debounced Live Review after mesh changes
- Live Review in Object and Edit Mode with a configurable source-vertex safety limit
- Explicit, undoable fixes for winding, exact duplicate faces, loose edges, and loose vertices

## Review profiles

Choose a profile before running Review:

- **General** runs every current finding group.
- **While Modeling** checks topology and transforms without warning about
  unfinished UVs, materials, or a triangle budget.
- **Topology Only** focuses on mesh structure.
- **Custom** lets you choose the finding groups yourself.

Geometry totals, face mix, and pole counts remain visible in every profile.
The completed profile is shown with the result and included in **Copy Report**.
Changing the profile, scope, custom switches, or triangle budget clears the
temporary Review Delta baseline. That prevents a different set of checks from
looking like a mesh improvement.

### Allow intentional topology

Some assets are meant to be open or contain a small number of ngons. Open
**More Settings > Topology Allowances** and enter how many open boundary edges
or ngons are acceptable for the current review. Zero means flag any amount.
The matching warning disappears only while the real count is within your
allowance; the mesh statistics remain available.

## Live Review

Press **Live** beside the main Review button when you want diagnostics to follow
a modeling pass. It refreshes the same inspection-only results after detected
mesh changes settle. It does not repair or otherwise edit geometry.

Live Review reads your current editable mesh without leaving Edit Mode or
changing its selection. It waits until your latest action settles, then updates
the same diagnostics and evaluated modifier totals you get in Object Mode.

It pauses when the chosen scope exceeds the **Live Vertex Limit**. Use zero only
when you deliberately want no density ceiling. Open **More Settings** for that
limit and the refresh delay. The manual **Run Now** action remains available at
all times.

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

## Finding view

Use the compact **Show** menu when the full list feels busy. You can show everything,
only errors, only warnings, findings with a simple fix, or findings that changed
since your Review Delta baseline. **Show Problems** draws that same
focused set in the viewport.

Changing the view clears the old finding overlay so you never mistake stale
marks for the new filter. Face and pole maps stay independent. **Copy Report**
still includes every finding from the latest review.

When the current view contains problems that can be drawn on the mesh, use the
compact arrow controls to step through them. Onyx selects the right object,
opens its result card, and shows that problem's color-coded evidence. The
navigator wraps around, so you can keep checking without returning to the list.

## Review Delta

A baseline is just a before snapshot.

1. Run Review.
2. Press **Save Baseline**.
3. Make your changes.
4. Run Review again.

Onyx shows what is new, what was fixed or disappeared, what changed, and what
stayed the same. It also shows the evaluated triangle difference. **Copy Delta**
gives you a plain-text comparison for notes or handoff. **Use Current as
Baseline** starts a fresh comparison from the current result. These controls
stay folded inside **Compare Changes** until you need them.

The baseline stays in memory for this Blender session only. It does not add
anything to the scene and is not saved in the `.blend` file.

## Viewport modes

Open **Viewport Modes** to use:

- Studio
- Silhouette
- Topology wire overlay
- Face Orientation

The first mode used in a viewport captures its settings. **Restore View** returns
those settings exactly, and disabling the extension restores every remaining
captured viewport.

## Install

Build `onyx_reviewer-0.11.0.zip` with `tools/package_reviewer.ps1`, then install the
archive through **Edit > Preferences > Get Extensions > Install from Disk**.
Open **Onyx > Review** in the 3D Viewport sidebar.

Blender will show that Reviewer needs clipboard access. That permission is used
only when you press **Copy Report** or **Copy Delta**. Reviewer does not need
network or file access.
