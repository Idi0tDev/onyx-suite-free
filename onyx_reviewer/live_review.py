"""Opt-in, debounced refreshes for Onyx Reviewer diagnostics."""

from __future__ import annotations

import time

import bpy
from bpy.app.handlers import persistent

from . import operators


_PENDING_SCENE = None
_DUE_AT = 0.0
_RUNNING = False


def _scene_pointer(scene):
    return scene.as_pointer() if scene is not None else None


def _timer_is_registered():
    return bpy.app.timers.is_registered(_timer)


def is_registered():
    return _depsgraph_updated in bpy.app.handlers.depsgraph_update_post


def has_pending(scene):
    return _PENDING_SCENE == _scene_pointer(scene)


def cancel_scene(scene):
    global _PENDING_SCENE, _DUE_AT
    if has_pending(scene):
        _PENDING_SCENE = None
        _DUE_AT = 0.0


def _ensure_timer(delay):
    if not _timer_is_registered():
        bpy.app.timers.register(
            _timer,
            first_interval=max(0.0, delay),
            persistent=False,
        )


def schedule(scene, *, immediate=False):
    """Queue one refresh for the active scene, replacing older pending work."""
    global _PENDING_SCENE, _DUE_AT
    if scene is None or scene != getattr(bpy.context, "scene", None):
        return False
    settings = getattr(scene, "onyx_reviewer", None)
    if settings is None or not settings.live_review:
        return False

    delay = 0.0 if immediate else settings.live_delay
    _PENDING_SCENE = _scene_pointer(scene)
    _DUE_AT = time.monotonic() + delay
    settings.live_status = "Review pending" if immediate else "Changes pending"
    _ensure_timer(delay)
    return True


def settings_changed(scene):
    settings = getattr(scene, "onyx_reviewer", None)
    if settings is None:
        return
    if settings.live_review:
        schedule(scene, immediate=True)
    else:
        cancel_scene(scene)
        settings.live_status = "Off"


def review_options_changed(scene):
    settings = getattr(scene, "onyx_reviewer", None)
    if settings is not None and settings.live_review:
        schedule(scene, immediate=True)


def _target_is_being_edited(objects):
    return any(obj.mode != "OBJECT" for obj in objects)


def _source_vertex_count(objects):
    return sum(len(obj.data.vertices) for obj in objects)


def flush_scene(scene):
    """Run a queued scene refresh now, or report why it is safely paused."""
    global _PENDING_SCENE, _DUE_AT, _RUNNING
    if scene is None or scene != getattr(bpy.context, "scene", None):
        return False
    settings = getattr(scene, "onyx_reviewer", None)
    if settings is None or not settings.live_review:
        cancel_scene(scene)
        return False

    objects = operators.scoped_meshes(bpy.context, settings.scope)
    if not objects:
        cancel_scene(scene)
        settings.live_status = operators.review_blocker(bpy.context, settings.scope)
        return False
    if _target_is_being_edited(objects):
        settings.live_status = "Paused while a target is in Edit Mode"
        return False

    vertex_count = _source_vertex_count(objects)
    if settings.live_max_vertices and vertex_count > settings.live_max_vertices:
        cancel_scene(scene)
        settings.live_status = (
            f"Paused: {vertex_count:,} source vertices exceed the "
            f"{settings.live_max_vertices:,} live limit"
        )
        return False

    cancel_scene(scene)
    _RUNNING = True
    try:
        operators.perform_review(bpy.context)
    except Exception as exc:  # Keep Blender responsive if a live pass cannot finish.
        settings.live_status = f"Paused: {exc}"
        return False
    finally:
        _RUNNING = False
    settings.live_status = "Up to date"
    return True


def _timer():
    global _PENDING_SCENE, _DUE_AT
    if _PENDING_SCENE is None:
        return None
    scene = getattr(bpy.context, "scene", None)
    if not has_pending(scene):
        # The artist changed scenes or loaded another file. The old context is
        # no longer safe to inspect through bpy.context, so discard that work.
        _PENDING_SCENE = None
        _DUE_AT = 0.0
        return None
    remaining = _DUE_AT - time.monotonic()
    if remaining > 0.0:
        return max(0.05, remaining)
    if flush_scene(scene):
        return None if _PENDING_SCENE is None else 0.1
    if has_pending(scene):
        # Edit Mode pauses instead of discarding the pending refresh. Leaving
        # the mode lets the same request complete without modifying the mesh.
        return 0.5
    return None


def _updated_id_pointer(update):
    updated_id = getattr(update.id, "original", update.id)
    pointer = getattr(updated_id, "as_pointer", None)
    return pointer() if pointer else None


@persistent
def _depsgraph_updated(scene, depsgraph):
    if _RUNNING or scene != getattr(bpy.context, "scene", None):
        return
    settings = getattr(scene, "onyx_reviewer", None)
    if settings is None or not settings.live_review:
        return
    objects = operators.scoped_meshes(bpy.context, settings.scope)
    watched = {
        pointer
        for obj in objects
        for pointer in (obj.as_pointer(), obj.data.as_pointer())
    }
    if watched and any(_updated_id_pointer(update) in watched for update in depsgraph.updates):
        schedule(scene)


def register():
    if not is_registered():
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph_updated)


def unregister():
    global _PENDING_SCENE, _DUE_AT, _RUNNING
    if is_registered():
        bpy.app.handlers.depsgraph_update_post.remove(_depsgraph_updated)
    if _timer_is_registered():
        bpy.app.timers.unregister(_timer)
    _PENDING_SCENE = None
    _DUE_AT = 0.0
    _RUNNING = False
