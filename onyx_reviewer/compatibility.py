"""Optional review-edition coordination through the shared Core broker."""

from __future__ import annotations

import bpy

from ._onyx_core.integration import discover


PRODUCTION_CAPABILITY = "onyx.review.production"
SUSPENDED_STATUS = "Paused: a production reviewer is active"

_CHECK_INTERVAL = 0.5
_LISTENERS = []
_LAST_ACTIVE = False
_HANDOFF_REFRESH_PENDING = False
_DISPLAY_SAW_PRODUCTION = False
_REGISTERED = False


def production_review_active():
    """Return whether an enabled Core participant owns production review."""
    endpoint = discover(bpy)
    if endpoint is None:
        return False
    try:
        extensions = endpoint.extensions()
    except (AttributeError, RuntimeError):
        return False
    return any(
        PRODUCTION_CAPABILITY in tuple(getattr(record, "capabilities", ()))
        for record in extensions
    )


def review_display_suspended():
    """Keep Free evidence hidden until takeover handoff has been refreshed."""
    global _DISPLAY_SAW_PRODUCTION
    active = production_review_active()
    if active:
        _DISPLAY_SAW_PRODUCTION = True
    # `_LAST_ACTIVE` and the display observation close the small window after
    # Pro unregisters but before the periodic watcher records that transition.
    return (
        active
        or _HANDOFF_REFRESH_PENDING
        or _LAST_ACTIVE
        or _DISPLAY_SAW_PRODUCTION
    )


def finish_handoff_refresh():
    """Release the handoff barrier after Free has safe evidence to display."""
    global _DISPLAY_SAW_PRODUCTION, _HANDOFF_REFRESH_PENDING, _LAST_ACTIVE
    active = production_review_active()
    had_barrier = (
        _HANDOFF_REFRESH_PENDING
        or _DISPLAY_SAW_PRODUCTION
        or (_LAST_ACTIVE and not active)
    )
    if not had_barrier:
        return False
    _HANDOFF_REFRESH_PENDING = False
    _DISPLAY_SAW_PRODUCTION = active
    if not active:
        _LAST_ACTIVE = False
    _tag_redraw()
    return True


def _timer_is_registered():
    return bpy.app.timers.is_registered(_watch_production_review)


def _tag_redraw():
    window_manager = getattr(bpy.context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _notify(active):
    for callback in tuple(_LISTENERS):
        try:
            callback(active)
        except (ReferenceError, RuntimeError):
            continue
    _tag_redraw()


def refresh():
    """Refresh takeover state and notify listeners only on a transition."""
    global _DISPLAY_SAW_PRODUCTION, _LAST_ACTIVE, _HANDOFF_REFRESH_PENDING
    active = production_review_active()
    if active != _LAST_ACTIVE:
        _HANDOFF_REFRESH_PENDING = not active
        if active:
            _DISPLAY_SAW_PRODUCTION = True
        _LAST_ACTIVE = active
        _notify(active)
    return active


def register_listener(callback):
    """Observe takeover changes and immediately receive the current state."""
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)
    callback(production_review_active())


def unregister_listener(callback):
    if callback in _LISTENERS:
        _LISTENERS.remove(callback)


def _watch_production_review():
    if not _REGISTERED:
        return None
    refresh()
    return _CHECK_INTERVAL


def register():
    global _DISPLAY_SAW_PRODUCTION, _REGISTERED, _LAST_ACTIVE, _HANDOFF_REFRESH_PENDING
    _REGISTERED = True
    _LAST_ACTIVE = production_review_active()
    _HANDOFF_REFRESH_PENDING = False
    _DISPLAY_SAW_PRODUCTION = _LAST_ACTIVE
    if not _timer_is_registered():
        bpy.app.timers.register(
            _watch_production_review,
            first_interval=_CHECK_INTERVAL,
            persistent=True,
        )


def unregister():
    global _DISPLAY_SAW_PRODUCTION, _REGISTERED, _LAST_ACTIVE, _HANDOFF_REFRESH_PENDING
    _REGISTERED = False
    if _timer_is_registered():
        bpy.app.timers.unregister(_watch_production_review)
    _LISTENERS.clear()
    _LAST_ACTIVE = False
    _HANDOFF_REFRESH_PENDING = False
    _DISPLAY_SAW_PRODUCTION = False
