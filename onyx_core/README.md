# Onyx Core

Onyx Core is the free framework for the Onyx Blender ecosystem. It contains no
modeling, baking, material, or other artist tool. Its job is to give Onyx
extensions one stable runtime contract.

Core has two distributions from the same source. It is available as a free
standalone extension with diagnostics, and its lightweight runtime is bundled
inside every Onyx product. A product therefore never asks the artist to install
another dependency before it works. Compatible bundled copies cooperate through
one runtime API broker when several Onyx products are enabled together.

Version 0.1.0 provides:

- a versioned API broker that does not rely on cross-extension Python imports;
- extension and capability discovery;
- versioned runtime services with explicit ownership and cleanup;
- transactional registration with rollback when an add-on fails to enable;
- shared readiness and asset-metadata primitives, including the canonical
  `onyx_asset_id`, `onyx_asset_role`, and `onyx_source_name` contract;
- a small diagnostic view in Blender's extension preferences.

## Install

Install the packaged ZIP through **Edit > Preferences > Get Extensions > Install
from Disk**, then enable **Onyx Core**. Core targets Blender 5.2 or newer and
performs no downloads, package installation, telemetry, or background network
access.

The standalone Core intentionally adds no 3D Viewport panel. Its status is
visible only in its extension preferences. Installing it is optional when an
Onyx product is already installed, because every product is self-contained.

## For extension developers

See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for API discovery,
lifecycle, service, compatibility, and fallback examples.
