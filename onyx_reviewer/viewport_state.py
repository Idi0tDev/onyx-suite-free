"""Reversible 3D Viewport inspection presets."""

from __future__ import annotations

from dataclasses import dataclass


_SHADING_FIELDS = (
    "type",
    "light",
    "color_type",
    "single_color",
    "show_shadows",
    "show_cavity",
    "show_xray",
)
_OVERLAY_FIELDS = (
    "show_overlays",
    "show_wireframes",
    "wireframe_opacity",
    "show_face_orientation",
)


@dataclass
class _Snapshot:
    space: object
    shading: dict
    overlay: dict


_SNAPSHOTS = {}


def _values(owner, fields):
    values = {}
    for name in fields:
        if hasattr(owner, name):
            value = getattr(owner, name)
            values[name] = tuple(value) if name == "single_color" else value
    return values


def _restore_values(owner, values):
    for name, value in values.items():
        try:
            setattr(owner, name, value)
        except (AttributeError, ReferenceError, TypeError):
            continue


def _pointer(space):
    try:
        return int(space.as_pointer())
    except (AttributeError, ReferenceError):
        return id(space)


def _snapshot(space):
    key = _pointer(space)
    if key not in _SNAPSHOTS:
        _SNAPSHOTS[key] = _Snapshot(
            space=space,
            shading=_values(space.shading, _SHADING_FIELDS),
            overlay=_values(space.overlay, _OVERLAY_FIELDS),
        )
    return key


def apply_mode(space, mode):
    if getattr(space, "type", "") != "VIEW_3D":
        raise ValueError("Review modes require a 3D Viewport")
    _snapshot(space)
    shading = space.shading
    overlay = space.overlay

    shading.type = "SOLID"
    shading.show_xray = False
    overlay.show_overlays = True
    overlay.show_face_orientation = False
    overlay.show_wireframes = False

    if mode == "STUDIO":
        shading.light = "STUDIO"
        shading.color_type = "MATERIAL"
        shading.show_shadows = True
        shading.show_cavity = True
    elif mode == "SILHOUETTE":
        shading.light = "FLAT"
        shading.color_type = "SINGLE"
        shading.single_color = (0.015, 0.015, 0.015)
        shading.show_shadows = False
        shading.show_cavity = False
    elif mode == "TOPOLOGY":
        shading.light = "STUDIO"
        shading.color_type = "SINGLE"
        shading.single_color = (0.18, 0.18, 0.18)
        shading.show_shadows = True
        shading.show_cavity = True
        overlay.show_wireframes = True
        overlay.wireframe_opacity = 1.0
    elif mode == "FACE_ORIENTATION":
        shading.light = "STUDIO"
        shading.color_type = "MATERIAL"
        shading.show_shadows = False
        shading.show_cavity = False
        overlay.show_face_orientation = True
    else:
        raise ValueError(f"Unknown review mode: {mode}")


def restore_space(space):
    snapshot = _SNAPSHOTS.pop(_pointer(space), None)
    if snapshot is None:
        return False
    try:
        _restore_values(snapshot.space.shading, snapshot.shading)
        _restore_values(snapshot.space.overlay, snapshot.overlay)
    except ReferenceError:
        pass
    return True


def restore_all():
    snapshots = tuple(_SNAPSHOTS.values())
    _SNAPSHOTS.clear()
    for snapshot in snapshots:
        try:
            _restore_values(snapshot.space.shading, snapshot.shading)
            _restore_values(snapshot.space.overlay, snapshot.overlay)
        except ReferenceError:
            continue


def register():
    return None


def unregister():
    restore_all()

