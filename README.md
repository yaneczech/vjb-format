# VJB Format

VJB (`.vjb`) is an open bundle format for temporal media prepared for live
playback.

It is built for a simple idea:

prepare the heavy work ahead of time, then perform with media that can jump,
freeze, reverse, loop, and hit exact moments without falling apart under
pressure.

VJB is meant for tools that care about rhythm, timing, markers, and reliable
realtime behavior, not just raw asset storage.

## What VJB Packages

- A primary baked media file
- Marker-driven transport metadata
- Optional thumbnails, analysis data, and future extensions

In practice, that means a VJB bundle can carry both the image and the intent:
where to jump, how to move, where a segment begins, and how it should behave
once playback lands there.

## Why It Exists

Modern visual performance often swings between two extremes:

- smooth temporal motion
- hard rhythmic cuts

The point of VJB is to make both feel direct.

Instead of asking a live playback tool to do expensive temporal processing at
show time, VJB assumes that interpolation, baking, and packaging can happen in
advance. What remains at runtime is the part that matters in performance:
fast seek, stable playback, and expressive transport control.

## Core Values

- Open by default
- Deterministic playback behavior
- Simple packaging with standard tooling
- Clear separation between authoring and playback
- Extensible without breaking core interoperability

## Status

This repository contains the first public working draft of the format.

The current focus is deliberately narrow:

- define the container
- define the manifest
- define marker and transport semantics
- define the minimum rules needed for interoperable playback

## Repository Layout

- [`spec/SPEC.md`](./spec/SPEC.md): current specification draft
- [`spec/PRINCIPLES.md`](./spec/PRINCIPLES.md): design principles for the format
- [`schema/manifest.schema.json`](./schema/manifest.schema.json): draft JSON Schema for `manifest.json`

## Naming

- Product/app example: `Vijual Bake Studio`
- Feature/workflow example: `Temporal Sampler`
- File format: `VJB` / `.vjb`

`VJB` is treated here as the format name. The specification is intended to be
usable by multiple tools and not tied to any single vendor runtime.

## Scope

VJB is:

- a bundle format
- a transport metadata format
- a playback-oriented interchange format

VJB is not:

- a new video codec
- a generic editing timeline format
- a vendor-locked project file

## License

This repository is licensed under Apache-2.0.
