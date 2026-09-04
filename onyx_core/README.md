<p align="center">
  <img src="../docs/assets/onyx-core-foundation.png" alt="Onyx Core shown as the workflow foundation of the Onyx Suite" width="100%">
</p>

<h1 align="center">Onyx Core 0.1.0</h1>

<p align="center">
  The quiet foundation shared by Onyx Blender tools.
</p>

<p align="center">
  <a href="https://github.com/Idi0tDev/onyx-suite-free/releases/download/v0.15.0/onyx_core-0.1.0.zip"><img alt="Download Onyx Core 0.1.0" src="https://img.shields.io/badge/Download-Onyx%20Core-e85d04?style=for-the-badge&logo=blender&logoColor=white"></a>
</p>

Onyx Core gives Onyx extensions one stable runtime for startup, compatibility,
diagnostics, and communication. It does not add modeling, baking, material, or
export tools of its own.

Most artists do **not** need to install Core separately. Every Onyx product,
including Reviewer, already contains the Core runtime it needs.

## What Core does

- Gives compatible Onyx products one versioned API broker
- Handles extension and capability discovery
- Provides shared services with clear ownership and cleanup
- Rolls registration back safely if an addon cannot finish starting
- Defines shared readiness and asset metadata conventions
- Adds a small diagnostic view when the standalone Core extension is installed

Bundled copies cooperate through the same broker instead of importing code from
another installed addon. The standalone extension joins that broker; it does not
start a competing runtime.

## Install the standalone extension

1. **[Download Onyx Core 0.1.0](https://github.com/Idi0tDev/onyx-suite-free/releases/download/v0.15.0/onyx_core-0.1.0.zip)** and leave the ZIP packed.
2. In Blender, open **Edit → Preferences → Get Extensions**.
3. Open the menu in the top-right and choose **Install from Disk**.
4. Pick `onyx_core-0.1.0.zip` and confirm the installation.

Core targets Blender 5.2 or newer. It performs no downloads, package
installation, telemetry, or background network access. Its status appears in
the extension preferences rather than the 3D Viewport sidebar.

## For extension developers

The [Core developer guide](docs/DEVELOPER_GUIDE.md) covers API discovery,
lifecycle, services, compatibility, metadata, and safe fallbacks.

<details>
<summary><strong>Why there are bundled and standalone versions</strong></summary>

Blender extensions should work on their own. Bundling Core means an artist can
install any Onyx product without setting up another dependency first. The
standalone version is optional and exposes diagnostics for people developing or
troubleshooting the wider Onyx ecosystem.

Both come from the same source and follow the same compatibility contract.

</details>
