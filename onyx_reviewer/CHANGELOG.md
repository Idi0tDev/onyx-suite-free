# Changelog

## 0.13.0 - 2026-09-02

- Replace written color names in the Blender interface with small native color
  dots that match the viewport evidence exactly.
- Put the color dot beside each drawable finding and topology class, so artists
  can connect a result to its viewport marks before pressing Show.
- Tighten the active-highlight summary and rename Color Key to the simpler
  Colors disclosure.

## 0.12.2 - 2026-09-02

- Reuse the current review's mesh evidence when Live Review redraws a visible
  finding or topology map instead of scanning the mesh a second time.
- Shorten the default quiet period after an edit from 0.75 to 0.3 seconds, while
  keeping it adjustable down to 0.1 seconds in More Settings.
- Cover the optimized path in Blender and verify that an overlapping-face live
  refresh runs its expensive overlap search only once.

## 0.12.1 - 2026-09-02

- Keep a visible finding, problem overview, face map, or pole map on screen while
  Live Review refreshes changed geometry.
- Rebuild the overlay from the current mesh after every successful live pass so
  its positions and counts do not become stale.
- Remove a focused error overlay only when that error is resolved or no longer
  belongs to the reviewed scope.
- Preserve Edit Mode and component selection while refreshing both results and
  their visual evidence.

## 0.12.0 - 2026-09-02

- Flag faces that point against a coherent group of connected face normals.
- Detect both faces that cross in 3D and separate coplanar faces that partially
  overlap.
- Keep exact duplicate faces as their own clearer finding instead of counting
  them again as overlaps.
- Add face selection and Indigo and Mint viewport evidence for the two new
  diagnosis-only errors.
- Group coplanar candidates by plane so overlap checks remain responsive on
  production meshes and during Live Review.

## 0.11.0 - 2026-09-02

- Refresh Live Review from the current editable mesh while staying in Edit
  Mode.
- Keep Edit Mode selection and geometry unchanged during live inspection.
- Count current Edit Mode vertices before applying the live density limit.
- Refresh evaluated modifier totals from synchronized edit geometry instead of
  reporting the last Object Mode state.
- Avoid queuing a duplicate live pass when a manual review already synchronized
  the current Edit Mode mesh.

## 0.10.1 - 2026-09-02

- Declare the clipboard permission used by Copy Report and Copy Delta.
- Explain that clipboard access is only used for user-requested plain-text
  copies and that Reviewer does not need network or file access.
- Add manifest coverage for Reviewer permissions so release metadata cannot
  silently drift from the feature.

## 0.10.0 - 2026-09-02

- Add optional allowances for intentionally open boundary edges and ngons.
- Keep both allowances at zero by default so existing reviews stay strict.
- Hide the matching warning only when its count is within the allowance while
  keeping the complete mesh statistics available.
- Put the new rules inside a collapsed Topology Allowances section so the main
  review workflow stays compact.

## 0.9.0 - 2026-09-02

- Add compact previous and next controls for stepping through the mesh problems
  visible in the current finding filter.
- Select the matching object, open its result card, and show the finding's
  color-coded viewport evidence in one action.
- Keep only the current object's result card open while navigating a multi-object
  review so the compact panel does not grow with every step.
- Keep navigation filter-aware and wrap cleanly from the last visual finding
  back to the first.

## 0.8.0 - 2026-09-02

- Rename the product, extension ID, source package, and release ZIP to Onyx
  Reviewer and `onyx_reviewer` before the public release.
- Rework the sidebar into a compact, progressive layout with optional settings,
  comparisons, viewport modes, object findings, statistics, and topology tools
  collapsed until they are needed.
- Add General, While Modeling, Topology Only, and Custom review profiles.
- Let Custom reviews switch topology, transforms, UV and material setup, and
  triangle-budget findings on or off.
- Keep geometry statistics visible regardless of the chosen finding profile.
- Show which profile produced the current results and flag options changed
  after a completed review.
- Include the completed review's profile in copied reports.
- Treat results kept in memory during an upgrade from an earlier version as a
  General review instead of showing an empty profile name.
- Clear temporary Review Delta baselines when the scope, profile, custom check
  groups, or triangle budget changes so unlike reviews are not compared.

## 0.7.0 - 2026-09-01

- Add a session-only Review Delta baseline for clear before-and-after checks.
- Show introduced, resolved, changed, and unchanged findings after a new review.
- Add a Changes finding view for current findings that need attention.
- Report evaluated triangle differences alongside finding changes.
- Add Copy Delta, Use Current as Baseline, and Clear Baseline controls.
- Clear saved baselines when a file is loaded or the extension is disabled.

## 0.6.0 - 2026-09-01

- Add All, Errors, Warnings, and Fixable finding views for dense review results.
- Make per-object viewport overviews follow the active finding view.
- Clear stale finding overlays whenever the finding view changes while keeping
  independent topology maps visible.
- Keep copied reports complete regardless of the current presentation filter.

## 0.5.0 - 2026-09-01

- Add explicit quick fixes for inconsistent face winding, exact duplicate
  faces, loose edges, and loose vertices.
- Make every fix a separate Blender undo step and refresh Review immediately.
- Refuse fixes on linked, multi-user, and shape-key mesh data.
- Keep Live Review inspection-only and omit any automatic or Fix All workflow.
- Leave holes, ngons, coincident vertices, islands, transforms, UVs, and
  materials diagnosis-only.

## 0.4.0 - 2026-09-01

- Add optional, debounced Live Review after watched mesh changes.
- Reuse the manual inspection engine so live and manual results stay identical.
- Pause live refreshes while a target is in Edit Mode.
- Add a configurable source-vertex ceiling for dense review scopes.
- Clear stale viewport evidence before a refreshed result is shown.
- Keep Live Review strictly diagnostic with no mesh repair or geometry edits.

## 0.3.0 - 2026-09-01

- Add color-coded face maps for triangles, quads, and ngons.
- Add color-coded pole maps for 3-edge, 5-edge, and 6+-edge vertices.
- Add focused viewport highlights for every face and pole class.
- Add Edit Mode inspection that selects the exact elements in each class.
- Keep topology-map overlays temporary and free of scene data.

## 0.2.0 - 2026-09-01

- Assign a distinct, stable viewport color to every actionable finding type.
- Keep error severity readable with thicker lines and larger point markers.
- Add triangle, quad, and ngon face composition to the panel and text report.
- Add 3-edge, 5-edge, and 6+-edge topology-pole counts to the panel and report.

## 0.1.0 - 2026-09-01

- Add the initial active, selected, and collection review workflow.
- Report base and evaluated geometry statistics.
- Flag common topology, transform, UV, material, and triangle-budget concerns.
- Add reversible Studio, Silhouette, Topology, and Face Orientation modes.
- Add preflight target readiness and disable review when the scope has no mesh.
- Detect exact duplicate faces occupying the same vertex positions.
- Detect coincident unwelded vertices and additional disconnected mesh islands.
- Add transient red and orange 3D Viewport highlights for actionable findings.
- Add a per-object Show All Findings overview with a severity legend.
- Add Inspect actions that select the exact vertices, edges, or faces behind
  actionable topology findings without editing mesh data.
- Add a copyable plain-text report for production handoff.
- Bundle the generated Onyx Core runtime.
