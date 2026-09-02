# Onyx Reviewer Engineering Case Study

Onyx Reviewer is a Blender mesh-inspection extension built around a simple
promise: useful evidence should not come at the cost of an artist's scene.
It compares source and evaluated geometry, reports topology and setup
conditions, and points to the affected mesh elements directly in the 3D
Viewport.

## The problem

Production meshes often look acceptable while still carrying expensive
surprises: modifier-driven triangle growth, inconsistent face winding,
overlapping faces, local normal-direction outliers, duplicate faces, loose
elements, missing asset setup, or topology that is hard to locate from a text
count alone. Blender exposes ways to investigate each condition, but the artist
has to know where to look and repeat the process for every object.

The product goal was therefore narrower than a general cleanup system:

- gather repeatable evidence for one object, a selection, or a collection;
- distinguish source geometry from the evaluated modifier result;
- turn topology counts into exact viewport locations;
- preserve context so reviewing a model does not disrupt modeling work; and
- make every mutation explicit, limited, and undoable.

## Product constraints

The implementation was shaped by five constraints.

1. **Inspection comes first.** A review, live refresh, highlight, or viewport
   mode must not modify mesh data.
2. **Warnings need context.** Open boundaries, ngons, or missing UVs can be
   intentional, so findings describe evidence rather than claiming every
   warning is a defect.
3. **Viewport evidence is temporary.** Highlights must not create objects,
   materials, collections, or saved metadata.
4. **Simple fixes stay narrow.** Only deterministic cases with a clear local
   operation receive a Fix button. There is no Fix All path.
5. **The extension is self-contained.** Reviewer bundles its compatible Onyx Core
   runtime and does not require a separately installed framework.

## Architecture

The analysis path is deliberately separated from Blender presentation code.

```text
Blender scope and readiness
           |
           v
Resolved review profile and finding groups
           |
           v
Base BMesh analysis + evaluated dependency-graph metrics
           |
           v
UI-neutral ObjectReview and ReviewSummary models
           |
           +--> panel and complete clipboard report
           +--> element selection for Inspect
           +--> transient GPU viewport overlays

Dependency-graph changes --> debounce and safety gates --> same review path

Saved session baseline --> pure summary comparison --> delta UI and report
```

| Area | Responsibility |
| --- | --- |
| `analysis.py` | Immutable issue, object-review, and summary data plus plain-text reporting |
| `mesh_analysis.py` | BMesh evidence, evaluated metrics, selection maps, overlay geometry, and simple fix operations |
| `operators.py` | Scope resolution and explicit Blender actions such as Review, Show, Inspect, and Fix |
| `highlight_state.py` | One transient GPU draw-handler lifecycle and stable finding colors |
| `viewport_state.py` | Capture, apply, and exact restoration of per-viewport display settings |
| `live_review.py` | Dependency-graph observation, debounce, current Edit Mode geometry, and density guard |
| `delta_state.py` | Session-only before snapshots, file-load cleanup, and the latest comparison |
| `review_profiles.py` | UI-neutral presets and custom finding-group resolution |
| `ui.py` and `properties.py` | Artist-facing state and layout without owning analysis rules |
| bundled `_onyx_core` | Transactional lifecycle, compatibility, discovery, and product registration |

This boundary lets the result model and report formatting run in ordinary
Python tests, while Blender-specific tests exercise BMesh, the dependency graph,
selection, draw geometry, lifecycle handlers, and viewport restoration.

## Decisions that matter

### Source and evaluated geometry are different evidence

Topology checks run against the editable base mesh. Final vertices, faces, and
triangles come from Blender's evaluated dependency graph and are released after
measurement. That avoids confusing a modifier result with the data an artist
can actually edit while still exposing modifier-driven cost.

### Visual evidence does not enter the scene

Finding and topology maps use a `SpaceView3D` GPU draw handler. Vertex evidence
is drawn as points, edge evidence as lines, and face evidence as outlines with
center markers. The overlay ignores surface depth so a problem on the far side
does not disappear. A live pass snapshots the active visual view, removes its old
coordinates, then rebuilds the same finding, overview, or topology map against
the current mesh. Cleanup removes the handler when evidence is hidden, cleared,
resolved, or the extension is disabled.

### A strange normal needs local context

A face is not suspicious just because it meets another face at a hard angle.
Reviewer first checks that at least three connected neighbors mostly agree with
one another. It reports the face only when its normal points strongly against
that local consensus. This catches a folded or reversed-looking patch without
painting ordinary cube corners and intentionally sharp low-poly work as errors.

### Overlap detection uses the cheapest useful test first

Crossing faces are found with Blender's spatial tree. Coplanar faces need a
separate 2D test because two triangles can cover the same area without crossing
in 3D. Reviewer groups those triangles by plane, performs a small bounding-box
sweep inside each group, and runs the exact overlap test only on the remaining
candidates. Exact duplicate faces are removed from this result so their more
specific finding remains clear.

### Filtering changes presentation, not truth

All, Errors, Warnings, and Fixable are views over the latest result. Switching
views never deletes findings or triggers a new analysis. The visible overview
follows the chosen view, while Copy Report always includes the complete result.
This keeps a dense panel usable without producing incomplete handoff notes.

### Mutation requires an explicit local decision

Only inconsistent winding, exact duplicate faces, loose edges, and loose
vertices offer simple fixes. Each click creates one Blender undo step, clears
stale visual evidence, performs the single named operation, and reruns the
review. Linked meshes, shared mesh data, and meshes with shape keys are refused
because a seemingly local change could have wider consequences.

### Live Review reuses the manual path

Live Review observes dependency-graph changes but does not own a second
analysis engine. It schedules the same review path after a configurable quiet
period. In Edit Mode it synchronizes the current editable geometry for analysis,
then preserves the artist's mode and component selection. A source-vertex
ceiling keeps accidental refreshes on unexpectedly dense scopes predictable.

### Review Delta stays out of the file

The baseline is an in-memory `ReviewSummary`, not scene metadata. Loading a file
or disabling the extension clears it. The actual comparison is a pure function
over two summaries, which makes introduced, resolved, changed, and unchanged
classification easy to test without Blender running. Current findings can be
filtered to new and changed items, while resolved findings remain available in
the delta box and copied report.

### Profiles change expectations, not geometry

General, While Modeling, and Topology Only resolve to small immutable profiles;
Custom resolves from four explicit switches. The same mesh metrics are still
reported, while issue creation follows the enabled finding groups. Changing a
scope, profile, custom switch, or budget invalidates old comparison state and
marks visible results as needing another run. This prevents a narrower profile
from being mistaken for a healthier mesh.

## Verification strategy

| Layer | What is checked |
| --- | --- |
| Pure result tests | Aggregation, severity, profile resolution, filtering, delta comparison, reporting, and compatibility behavior |
| Blender mesh tests | Real BMesh findings including normal outliers and two kinds of face overlap, source/evaluated counts, selection domains, and simple mutations |
| Viewport tests | Highlight geometry, stable distinct colors, topology maps, and exact state restoration |
| Lifecycle tests | Registration rollback, embedded Core parity, standalone Core coexistence, and cleanup |
| Release checks | Manifest/runtime version parity, public-source audit, deterministic packaging, archive inspection, SHA-256 output, and native Blender ZIP validation |
| Manual product pass | Installation, panel flow, real viewport overlays, filters, fixes, undo, and scene restoration in Blender 5.2 LTS |

Hosted checks run the portable result, framework, embedding, source-audit, and
packaging gates on Windows and Linux. The complete local release gate also runs
the real Blender smoke and coexistence suites with a clean factory startup.

## Current trade-offs

- Topology evidence maps the editable base mesh; evaluated geometry currently
  contributes metrics rather than selectable modifier-result elements.
- Face-overlap checks stay inside each editable base mesh; intersections between
  separate objects and evaluated modifier surfaces are not diagnosed yet.
- The local normal check finds a face that disagrees with coherent neighbors; it
  does not guess which side of an entire open model is globally inside or out.
- Live Review is debounced on Blender's main thread rather than running mesh
  analysis asynchronously.
- Simple fixes deliberately exclude operations whose correct result depends on
  modeling intent, including hole filling, broad merging, remeshing, transform
  application, UV creation, and material assignment.

## Next directions

Likely next steps include evaluated-geometry visualization and running the full
Blender smoke suite in hosted continuous integration. The first per-check rules
now ship as explicit allowances for open boundary edges and ngons, kept inside
the collapsed settings instead of expanding the everyday workflow.
