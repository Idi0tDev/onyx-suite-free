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

Element-level topology findings include an **Inspect** action. It activates the
reviewed mesh, enters Edit Mode, switches to the matching vertex, edge, or face
selection mode, and selects the elements that currently produce that finding.
Inspect supports non-manifold and boundary edges, degenerate and duplicate
faces, inconsistent winding, loose geometry, coincident vertices, disconnected
islands, and ngons. For disconnected islands, Inspect selects every island
outside the largest connected component.

Inspect changes the active object, mode, and selection so the problem is ready
to examine, but it never edits geometry. Results describe the last review run;
after correcting a mesh, run Review again to refresh the counts.

## Viewport highlights

Use **Show** beside an actionable topology finding to draw its affected geometry
directly over the model. Errors use red; warnings use orange. Vertex findings
appear as points, edge findings as thick lines, and face findings as outlines
with center markers. The overlay remains visible through the mesh so problems
on the far side are not hidden.

Use **Show All Findings** in an object card to see every actionable problem for
that mesh together. The highlight summary acts as a legend: red geometry is an
error and orange geometry is a warning. Pressing **Show** on an individual
finding switches the overview to that focused finding.

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
