<p align="center">
  <img src="docs/assets/onyx-suite-hero.png" alt="Onyx Suite modular cube artwork" width="100%">
</p>

<h1 align="center">Onyx Suite Free</h1>

<p align="center">
  <strong>Small, focused Blender tools built on one shared foundation.</strong><br>
  Free, open source, and designed to stay out of your way.
</p>

<p align="center">
  <img alt="Blender 5.2 or newer" src="https://img.shields.io/badge/Blender-5.2%2B-5b7083">
  <img alt="GPL 3.0 or later" src="https://img.shields.io/badge/license-GPL--3.0--or--later-5b7083">
  <img alt="Public release" src="https://img.shields.io/badge/status-public%20release-c58b36">
</p>

<p align="center">
  <a href="#download-onyx-suite-free"><img alt="Download Onyx Suite Free" src="https://img.shields.io/badge/Download-Onyx%20Suite%20Free-e85d04?style=for-the-badge&logo=blender&logoColor=white"></a>
</p>

## Onyx Core

<p align="center">
  <img src="docs/assets/onyx-core-foundation.png" alt="Onyx Core shown as the workflow foundation of the Onyx Suite" width="100%">
</p>

Core is the common foundation behind Onyx tools. It handles startup,
compatibility, diagnostics, and safe communication between products.

- Every Onyx product bundles the Core runtime it needs.
- Artists do not have to install Core separately.
- The standalone Core download is useful for framework diagnostics and addon
  development.

**[Open the Core product page](onyx_core/README.md)** ·
**[Read the developer guide](onyx_core/docs/DEVELOPER_GUIDE.md)**

## Onyx Reviewer

<p align="center">
  <img src="docs/assets/onyx-reviewer-hero.png" alt="Onyx Reviewer scanning a mesh and identifying geometry problems" width="100%">
</p>

Reviewer checks editable and modifier-evaluated meshes, explains what it finds,
and points to useful evidence directly in Blender's 3D Viewport. It does not
repair, remesh, or otherwise change your geometry.

- Color-coded highlights make different problem types easy to tell apart.
- Hover guides list every problem sharing the same part of a face and suggest
  a practical way to approach each one.
- Live Review follows Object Mode and Edit Mode changes after they settle.
- Review Delta shows what appeared, changed, or disappeared since a baseline.
- Viewport modes help inspect form, silhouette, topology, and face direction.
- Open holes count once per connected opening, regardless of edge density.
- Saving a baseline or adjusting topology limits keeps the current colored
  evidence visible while the next review is prepared.

<p align="center">
  <img src="docs/assets/onyx-reviewer-live-review.gif" alt="Onyx Reviewer updating its findings while a topology problem is fixed in Edit Mode" width="100%">
</p>

**[Open the Reviewer product page](onyx_reviewer/README.md)** ·
**[Read the user guide](onyx_reviewer/docs/USER_GUIDE.md)**

## Download Onyx Suite Free

Pick the add-on you want. These are ready-to-install Blender ZIPs—there is no
need to download the repository or unpack anything.

- **[Download Onyx Reviewer 1.0.2](https://github.com/Idi0tDev/onyx-suite-free/releases/download/v1.0.2/onyx_reviewer-1.0.2.zip)** — find mesh problems and see them on the model.
- **[Download Onyx Core 0.2.1](https://github.com/Idi0tDev/onyx-suite-free/releases/download/v1.0.2/onyx_core-0.2.1.zip)** — optional standalone diagnostics for the shared framework.

Each Onyx add-on includes the Core runtime it needs, so you never have to
install Core as a separate dependency. All versions, checksums, and release
notes are also kept on the
[Releases](https://github.com/Idi0tDev/onyx-suite-free/releases) page. Future
free Onyx add-ons will get their own direct download here.

## Install an Onyx add-on

1. Download the add-on ZIP you want from the section above and leave it packed.
2. In Blender, open **Edit → Preferences → Get Extensions**.
3. Open the menu in the top-right and choose **Install from Disk**.
4. Pick the downloaded `onyx_*.zip` file and confirm the installation.
5. Enable the add-on if Blender asks. Its product page and user guide explain
   where its controls live.

That is it. Every Onyx product already carries its compatible Core runtime.

## Repository map

| Path | What is there |
| --- | --- |
| [`onyx_core/`](onyx_core) | The public framework and optional standalone extension |
| [`onyx_reviewer/`](onyx_reviewer) | The Reviewer extension, product page, and user guide |
| [`docs/`](docs) | Shared project notes, troubleshooting, and artwork |

## Contributing and support

Found a bug or have a focused idea? Open an
[issue](https://github.com/Idi0tDev/onyx-suite-free/issues). Please include your
Blender version, the Onyx version, what you expected, and a small reproduction
when possible.

### Support the flock 🐔

Onyx stays free. If it saves you some time and you feel the urge to support
future updates, here is a photo of my chickens—the tiny support crew you are
supporting:

<p align="center">
  <img src="docs/assets/onyx-support-crew-upright.png" alt="Marco's chickens, the unofficial Onyx support crew" width="360">
</p>

They contribute nothing to the codebase, ignore release schedules, and remain
deeply committed to the feed budget.

**[Support free Onyx addons on Gumroad](https://idi0tdev.gumroad.com/l/onyx-suite-free)**

<details>
<summary><strong>How releases are checked</strong></summary>

Before a ZIP is published, the Core framework, Reviewer analysis, viewport
evidence, Live Review, embedded runtime, edition coexistence, package contents,
and a clean Blender installation are checked. The downloadable ZIP is the same
file that goes through those checks.

</details>

<details>
<summary><strong>Why Core is bundled</strong></summary>

Blender extensions work best when they are self-contained. Each Onyx product
therefore carries a generated copy of the same Core runtime. Compatible copies
meet through a versioned broker instead of importing code from another installed
addon. This keeps installation simple while still allowing Onyx products to
cooperate.

The standalone Core extension joins that same broker and adds diagnostics. It
does not create a second competing runtime.

</details>

## License

The source code is licensed under [GNU GPL 3.0 or later](LICENSE).
