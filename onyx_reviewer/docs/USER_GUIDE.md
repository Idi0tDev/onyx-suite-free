# Onyx Reviewer User Guide

## Quick start

1. Select a mesh object.
2. Open the 3D Viewport sidebar and choose **Onyx > Review**.
3. Use the two small menus below the mesh name to choose the scope and review
   profile. **Active** and **General** are good for a first run.
4. Click **Run Review**.
5. Press **Next** to see each visual mesh problem, or open the reviewed object's
   card to browse the full list.

If **Run Review** is greyed out, the message at the top tells you what is
missing, such as an active mesh or a selected mesh.

The everyday controls stay visible. Less common controls are folded away:

- **More Settings** contains custom checks, the triangle budget, and Live
  Review timing limits.
- **Compare Changes** contains the temporary before-and-after baseline.
- **Viewport Modes** contains Studio, Silhouette, Topology, Orientation, and
  Restore View.
- Each object keeps **Mesh Statistics** and **Topology Tools** collapsed until
  you need them.

Running a review only reads the mesh. It does not change objects, modifiers,
materials, selection, or mesh elements.

## Review profiles

A profile answers “what matters at this point in the work?” It changes which
findings appear, but it never changes the mesh.

| Profile | What it checks |
| --- | --- |
| General | Topology, transforms, UVs and materials, and the triangle budget |
| While Modeling | Topology and transforms, without setup or budget warnings |
| Topology Only | Mesh-structure findings only |
| Custom | The finding groups you switch on yourself |

Use **While Modeling** when an asset is still taking shape and missing UVs or
materials are expected. Use **General** for a broader handoff check. Choose
**Custom** when a particular job has its own needs.

Face mix, pole counts, dimensions, and source versus evaluated geometry stay
visible in every profile. The completed profile is shown with the result and in
**Copy Report**. If you change the scope, profile, custom switches, or triangle
budget after a review, the panel says the options changed and asks you to run
Review again.

Those changes also clear a saved Review Delta baseline. A baseline made with
General should not be compared with a Topology Only result, because missing
findings could come from the profile instead of a mesh edit.

### Allow intentional open edges or ngons

Some models are meant to have open edges. A cloth panel, hair card, trim sheet,
or other flat asset should not need a noisy warning on every review. The same
can be true for a small number of deliberate ngons.

Open **More Settings > Topology Allowances** and set:

- **Allowed Open Edges** — how many boundary edges can exist before the open-edge
  warning appears; and
- **Allowed Ngons** — how many faces with more than four sides can exist before
  the ngon warning appears.

Both start at zero, which means flag any amount. A count exactly equal to the
allowance is accepted; the warning returns as soon as the mesh goes over it.
These values change only the warnings. Face mix and the other mesh statistics
stay visible, and no geometry is edited. Changing either allowance marks an old
review as out of date and clears its temporary comparison baseline.

## Live Review

**Live Review** is optional and off by default. Press **Live** beside the main
Review button when you want the results to refresh as a watched mesh changes. The active,
selected, or collection scope is shared with manual review, so both paths report
the same checks and counts.

Open **More Settings** to adjust Live Review. The **Debounce** value controls how long Onyx waits after the latest detected
change. This prevents a new review from starting for every intermediate update
while Blender is still evaluating a mesh or modifier stack. **Run Now** remains
available whenever an immediate manual refresh is useful.

Two safeguards keep the workflow predictable:

- Live Review works in Object Mode and Edit Mode. In Edit Mode it reads the
  current editable mesh, keeps you in the mode, and leaves the selection alone.
- Live Review pauses when the scope exceeds the **Live Vertex Limit**, measured
  from the current source mesh rather than its modifier result. Increase the
  limit for a known asset or set it to zero to disable the ceiling.

The status below the controls reports **Changes pending**, **Up to date**, or
the reason a refresh is paused. A refresh clears any viewport highlight because
that overlay described the previous mesh state. Live Review only refreshes
diagnostic evidence: it never selects components, applies modifiers, repairs
topology, or edits geometry.

## Findings

Errors identify conditions that usually require correction, such as degenerate
faces, inconsistent winding, edges shared by more than two faces, or a negative
world-transform determinant. Exact duplicate faces occupying the same vertex
positions are also reported as errors. Warnings identify conditions that may be
valid but deserve review, such as open boundaries, ngons, unapplied scale,
coincident unwelded vertices, disconnected islands, or missing UVs.

An open boundary is not automatically a bad mesh: planes, cards, clothing, and
other intentionally open surfaces can be correct. Onyx Reviewer reports facts and
leaves the production decision to the artist.

### Finding view

Use the compact **Show** menu after a review to control how much evidence is
shown in the panel:

| View | Shows |
| --- | --- |
| All | Every finding from the latest review |
| Errors | Conditions that usually require correction |
| Warnings | Contextual conditions that may be intentional |
| Fixable | Findings with one of Onyx Reviewer's supported simple fixes |
| Changes | Findings that are new or changed since your saved baseline |

This is a presentation filter: it does not rerun the review or delete hidden
findings. **Show Problems** uses the same focused set in the 3D
Viewport, while **Copy Report** always includes every finding. Changing the view
clears the previous finding overlay so old evidence is not confused with the
new filter. Face and pole topology maps are independent and remain visible.

If Changes is empty, that is usually good news: nothing new appeared and no
existing finding changed. Resolved findings are shown in **Compare Changes**
because they are no longer part of the current result.

### Step through mesh problems

When the current Show view contains findings that can be pointed out on the
mesh, a small problem navigator appears below the filter. Press **Next** or the
back arrow to move through them. Onyx selects the matching object, opens its
result card, closes the other result cards, frames it in the current 3D
Viewport, and draws that finding in its usual color.

The navigator follows the active Show view. Choose **Errors** to walk only
through error-level mesh problems, **Fixable** to check the simple-fix cases,
or **Changes** to inspect visual problems introduced or changed since the
baseline. Findings such as a missing material are still listed and reported,
but are not part of this navigator because there is no mesh element to point at.
Moving past the last visual finding wraps back to the first.

## Review Delta

Review Delta answers a very practical question: “Did this modeling pass make
the mesh better, worse, or just different?”

### Save the before snapshot

1. Run Review on the object, selection, or collection you want to track.
2. Open **Compare Changes** and press **Save Baseline**.
3. Make your changes.
4. Run Review again.

“Baseline” simply means the before snapshot. After the second review, Onyx
shows:

- **New** — a finding that was not in the baseline;
- **Fixed** — a baseline finding that is now gone;
- **Changed** — the same finding is still there, but its count or details
  changed; and
- **Same** — the same finding still has the same details.

The box also shows the evaluated triangle change. A positive number means the
result gained triangles; a negative number means it lost triangles.

Choose **Changes** in the Show menu to see only introduced and changed findings on
the current mesh. Use **Copy Delta** when you want a plain-text before-and-after
summary. When the current result is your new good starting point, press **Use
Current as Baseline**.

The baseline is temporary. It stays only for the current Blender session and is
cleared when you load another file, disable the addon, or press **Clear
Baseline**. Changing the review scope, profile, custom check groups, or triangle
budget also clears it. It never becomes mesh data and is not saved in the
`.blend` file.

## Simple fixes

A **Fix** button appears only for four deliberately narrow cases:

| Finding | Explicit operation |
| --- | --- |
| Inconsistent face winding | Recalculate connected face normals for consistent winding |
| Exact duplicate faces | Keep the first face and delete later faces with exactly matching vertex positions |
| Loose edges | Delete edges that are not used by any face |
| Loose vertices | Delete vertices that are not connected to any edge |

Fixes work on the base mesh in Object Mode. Each click is one Blender undo step,
clears stale viewport evidence, and reruns the current review so the new counts
are visible immediately. Onyx refuses to run a fix on linked mesh data,
multi-user mesh data, or a mesh with shape keys.

There is no **Fix All** action and Live Review never runs fixes. Open boundaries,
degenerate faces, ngons, coincident vertices, disconnected islands, transforms,
UVs, and materials remain diagnosis-only because a generic change could destroy
intentional modeling decisions.

Element-level topology findings include an **Inspect** action. It activates the
reviewed mesh, enters Edit Mode, switches to the matching vertex, edge, or face
selection mode, and selects the elements that currently produce that finding.
Inspect supports non-manifold and boundary edges, degenerate and duplicate
faces, inconsistent winding, loose geometry, coincident vertices, disconnected
islands, and ngons. For disconnected islands, Inspect selects every island
outside the largest connected component.

Inspect changes the active object, mode, and selection so the problem is ready
to examine, but it never edits geometry. Results describe the last review run;
after correcting a mesh, run Review again or enable Live Review to refresh the
counts.

Each object card also reports its triangle, quad, and ngon face mix, plus counts
of vertices connected to 3, 5, or 6+ edges. These are descriptive topology
statistics rather than automatic warnings: the right mix and pole flow depend
on how the asset will deform, shade, or be edited.

## Topology detail

Expand **Topology Tools** inside an object card to turn those statistics into
viewport navigation.

**Show Face Map** displays every available face class together:

| Face class | Color |
| --- | --- |
| Quads | Teal |
| Triangles | Gold |
| Ngons | Coral |

**Show Pole Map** displays the pole classes that are present:

| Pole class | Color |
| --- | --- |
| 3-edge poles | Sky |
| 5-edge poles | Violet |
| 6+-edge poles | Pink |

Use **Show** beside one class to isolate it. Use **Inspect** to enter Edit Mode
and select its exact faces or vertices. Controls with a zero count remain
disabled. Like finding highlights, topology maps are temporary, visible through
the surface, and create no objects, materials, or saved mesh data.

## Viewport highlights

Use **Show** beside an actionable topology finding to draw its affected geometry
directly over the model. Each finding type keeps the same color:

| Finding | Color |
| --- | --- |
| Edges connected to more than two faces | Red |
| Degenerate faces | Rose |
| Duplicate faces | Magenta |
| Inconsistent winding | Purple |
| Open boundary edges | Cyan |
| Loose edges | Yellow |
| Loose vertices | Lime |
| Coincident vertices | Orange |
| Disconnected islands | Blue |
| Ngons | Amber |

Error-level findings use thicker lines and larger point markers, so severity is
still visible when several colors overlap. Vertex findings appear as points,
edge findings as lines, and face findings as outlines with center markers. The
overlay remains visible through the mesh so problems on the far side are not
hidden.

Use **Show Problems** in an object card to see its actionable findings
from the current Show filter together. The highlight summary acts as a color
legend when **Color Key** is opened and retains an error or warning icon beside
each entry. Pressing **Show** on an individual finding switches the overview to
that focused finding.

Press **Hide** in the highlight summary, or **Hide Problems** in the object
card, to remove the overlay. Rerunning or clearing the review and disabling the extension also
clear it. Highlights create no objects, materials, collections, or saved mesh
data, and they do not change the active object, mode, or selection.

Use **Copy Report** after a review to place a complete plain-text summary on the
clipboard for handoff notes, issue reports, or production checklists. This does
not write a file or change the scene. This is the only reason Reviewer asks for
clipboard permission; it does not need network or file access.

## Viewport review

Open **Viewport Modes** for these controls. They affect only the 3D Viewport where their button was pressed. The
first mode captures the original viewport settings. Switch freely between modes,
then press **Restore View**. Disabling Onyx Reviewer also restores saved viewports.
