# Changelog

## 0.2.1

- Removed Python `threading` from Blender-facing registry access. Core now keeps
  Blender API and broker work on Blender's main process.
- Limited the standalone installable package to files used at runtime.
- Kept API 1.1 compatible with products that use the original API 1.0 surface.

## 0.2.0

- Added API 1.1 with shared material-channel roles and persistent metadata.
- Standardized Base Color, Roughness, Metallic, Normal, Height, Ambient
  Occlusion, Emission, and Alpha names for compatible Onyx tools.
- Added a versioned optional material-channel service contract without making
  any product depend on another installed extension.

## 0.1.0

- Added the API v1 runtime broker.
- Added the self-contained runtime vendored into every Onyx product package.
- Added extension, capability, and versioned service registration.
- Added transactional registration with reverse-order cleanup and rollback.
- Added shared readiness and Onyx asset metadata primitives.
- Added framework diagnostics in Blender's extension preferences.
