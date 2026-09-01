# Onyx Review User Guide

## Quick start

1. Select a mesh object.
2. Open the 3D Viewport sidebar and choose **Onyx > Review**.
3. Choose Active, Selected, or Collection.
4. Set a triangle budget, or use zero to disable the budget warning.
5. Click **Run Review**.

The panel identifies the current target before the review starts. If the chosen
scope has no mesh objects, it explains what is missing and keeps the action
disabled.

Reviewing reads source and evaluated mesh data but does not change objects,
modifiers, materials, selection, or mesh elements.

## Live Review

**Live Review** is optional and off by default. Enable it in **Review Options**
when you want the results to refresh as a watched mesh changes. The active,
selected, or collection scope is shared with manual review, so both paths report
the same checks and counts.

The **Debounce** value controls how long Onyx waits after the latest detected
change. This prevents a new review from starting for every intermediate update
while Blender is still evaluating a mesh or modifier stack. **Run Now** remains
available whenever an immediate manual refresh is useful.

Two safeguards keep the workflow predictable:

- Live Review pauses while any target is in Edit Mode. Leave Edit Mode and the
  pending review resumes without altering the edit mesh.
- Live Review pauses when the scope exceeds the **Live Vertex Limit**, measured
  from source-mesh vertices. Increase the limit for a known asset or set it to
  zero to disable the ceiling.

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
other intentionally open surfaces can be correct. Onyx Review reports facts and
leaves the production decision to the artist.

### Finding view

Use **Finding View** after a review to control how much evidence is shown in the
panel:

| View | Shows |
| --- | --- |
| All | Every finding from the latest review |
| Errors | Conditions that usually require correction |
| Warnings | Contextual conditions that may be intentional |
| Fixable | Findings with one of Onyx Review's supported simple fixes |

This is a presentation filter: it does not rerun the review or delete hidden
findings. **Show Visible Findings** uses the same focused set in the 3D
Viewport, while **Copy Report** always includes every finding. Changing the view
clears the previous finding overlay so old evidence is not confused with the
new filter. Face and pole topology maps are independent and remain visible.

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

Expand **Topology Detail** inside an object card to turn those statistics into
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

Use **Show Visible Findings** in an object card to see its actionable findings
from the current Finding View together. The highlight summary acts as a color
legend and retains an error or warning icon beside each entry. Pressing **Show**
on an individual finding switches the overview to that focused finding.

Press **Hide**, **Hide All Findings**, or **Clear Highlight** to remove the
overlay. Rerunning or clearing the review and disabling the extension also
clear it. Highlights create no objects, materials, collections, or saved mesh
data, and they do not change the active object, mode, or selection.

Use **Copy Report** after a review to place a complete plain-text summary on the
clipboard for handoff notes, issue reports, or production checklists. This does
not write a file or change the scene.

## Viewport review

Viewport modes affect only the 3D Viewport where their button was pressed. The
first mode captures the original viewport settings. Switch freely between modes,
then press **Restore View**. Disabling Onyx Review also restores saved viewports.
