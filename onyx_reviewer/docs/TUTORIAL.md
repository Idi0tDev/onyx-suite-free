# Your First Mesh Review

This little practice run uses Blender's default cube. You will make one obvious
mesh problem, find it on the model, and remove it again. Reviewer will not fix
or change anything for you.

## 1. Run a calm first check

1. Open a new Blender file and leave the cube selected.
2. Press **N** while your pointer is over the 3D Viewport.
3. Open **Onyx > Review**.
4. Keep **Active** and **General** selected.
5. Press **Run Review**.

The cube's card appears below the summary. A normal default cube may still have
a setup warning, such as having no material. That does not mean the mesh is
broken. Reviewer tells you what it found; you decide what matters for the job.

## 2. Make a problem that is easy to see

1. Turn on **Live**. Reviewer runs a scan straight away.
2. Enter Edit Mode with **Tab**.
3. Switch to face selection, select any one face, and delete **Faces**.
4. Wait a moment for Live Review to catch up.

The missing face leaves one open hole. Its boundary edges appear in their own
color on the cube, but the result counts the opening once rather than counting
every edge around it. If Live Review is not useful for a very dense object,
turn it off and use **Run Now** after your edits instead.

## 3. Ask Reviewer where to look

Use **Next** to focus the first drawable problem, or open the cube's card and
press **Show** beside the open-hole finding. Rest the pointer over one of the
colored lines. A small guide explains the finding and suggests what to check.
If another problem occupies the same place, the guide lists both.

You can also press **Inspect**. Reviewer selects the matching mesh elements in
Edit Mode, but it does not edit them. This is handy when a tiny problem is hard
to click by hand.

## 4. Remove the test problem

Press **Ctrl+Z** to bring the deleted face back. Live Review refreshes after a
short pause and removes the open-hole finding once the next scan confirms it is
gone.

If you turned Live off, press **Run Review** again. Either way, Reviewer waits
for a scan before changing the result, so the display reflects checked geometry
rather than a guess.

## 5. Try a viewport mode safely

1. Open **Viewport Modes**.
2. Try **Topology** or **Orientation**.
3. Press **Restore View**.

Reviewer remembers how that viewport looked before the first preset and puts it
back. Disabling the extension also restores any saved viewport state.

## 6. Copy a simple handoff note

Press **Copy Report** and paste into a text editor. The copied text includes the
full review even if the panel is currently filtered to one kind of finding.
Reviewer only uses clipboard access when you press a copy button.

That is the everyday loop: review, look at the colored evidence, make your own
edit, and review again.

## Optional: choose easier-to-read colors

Leave a problem visible, open **More Settings**, and change **Problem Colors**
from **Onyx** to **High Contrast** or **Colorblind Safe**. The marks on the mesh
and the little dots in the panel change straight away. Reviewer does not scan
again, so your result, Live Review state, and saved comparison stay as they
were. Pick whichever palette is easiest for you to read.

## Optional: bend a face on purpose

Want to try the non-planar check too? Start with a fresh cube, enter Edit Mode,
switch to vertex selection, and move one top corner upward a little. At least
one connected quad is now bent instead of perfectly flat. Run Review and look
for **Non-planar faces**.

Press **Show** or **Inspect** to point at the exact face. Undo the move and run
Review again to clear it. If a real model is meant to bend this way, open
**More Settings > Topology Limits** and raise **Non-Planar Angle**. Reviewer is
showing a production question, not declaring that every bent face is wrong.
The old colored evidence stays on the mesh while you adjust the limit and is
replaced when the next scan finishes.

## If both editions are installed

When Onyx Reviewer Pro is enabled, this Review panel and its viewport marks
pause so the editions do not overlap. Disable Pro and the panel returns. If Live
was on, Reviewer runs a fresh scan before showing its marks again.
