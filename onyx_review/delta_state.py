"""Session-local Review Delta baselines and comparisons."""

from bpy.app.handlers import persistent

import bpy

from .analysis import ReviewSummary, compare_review_summaries


_BASELINES = {}
_DELTAS = {}


def _scene_key(scene):
    return scene.as_pointer()


def baseline(scene):
    return _BASELINES.get(_scene_key(scene))


def current_delta(scene):
    return _DELTAS.get(_scene_key(scene))


def set_baseline(scene, summary):
    if not isinstance(summary, ReviewSummary):
        raise TypeError("Expected a ReviewSummary")
    key = _scene_key(scene)
    _BASELINES[key] = summary
    _DELTAS.pop(key, None)


def compare(scene, summary):
    key = _scene_key(scene)
    saved = _BASELINES.get(key)
    if saved is None:
        _DELTAS.pop(key, None)
        return None
    delta = compare_review_summaries(saved, summary)
    _DELTAS[key] = delta
    return delta


def clear_delta(scene):
    _DELTAS.pop(_scene_key(scene), None)


def clear_baseline(scene):
    key = _scene_key(scene)
    _BASELINES.pop(key, None)
    _DELTAS.pop(key, None)


def clear_all():
    _BASELINES.clear()
    _DELTAS.clear()


@persistent
def _load_post(_unused):
    clear_all()


def register():
    clear_all()
    if _load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_load_post)


def unregister():
    if _load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post)
    clear_all()
