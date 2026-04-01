# VJB Specification Draft

## 1. Overview

VJB is an open bundle format for packaged temporal media playback.

A VJB file contains:

- a primary baked media file
- playback metadata
- optional analysis and thumbnail assets

The format is designed for low-latency marker-based playback workflows such as
teleport seek, reverse traversal, looping, and segment-based live performance.

## 2. Design Goals

- Portable between authoring and playback tools
- Deterministic marker and segment behavior
- Simple packaging with ordinary tools
- Strong forward compatibility rules
- Good runtime ergonomics for cached playback

## 3. Non-Goals

- Defining a new video codec
- Replacing editing timelines such as OTIO or AAF
- Embedding app-specific UI state into the interchange format
- Requiring direct playback from inside compressed archive storage

## 4. Container

File extension:

- `.vjb`

Container type:

- ZIP archive

Recommended ZIP behavior:

- `manifest.json` and small metadata files may use compression
- primary media files should use `store` mode where possible

Reasoning:

- simple inspection
- broad tool support
- straightforward packaging
- practical extraction to runtime cache

## 5. Directory Layout

Minimum layout:

```text
example.vjb
├── manifest.json
└── media/
    └── master.mov
```

Optional directories:

- `proxy/`
- `thumbnails/`
- `analysis/`
- `extras/`

Reserved top-level paths:

- `manifest.json`
- `media/`
- `proxy/`
- `thumbnails/`
- `analysis/`
- `extras/`

## 6. Manifest

The root manifest file must be named:

- `manifest.json`

Required root keys for `v1`:

- `schema`
- `schemaVersion`
- `bundleId`
- `title`
- `source`
- `bake`
- `media`
- `transport`
- `markers`

Recommended root shape:

```json
{
  "schema": "com.vjb.bundle",
  "schemaVersion": "1.0.0",
  "bundleId": "01JQ7K7Y3V6J7Y1M0P8E6C4T9N",
  "createdAt": "2026-04-01T18:42:00Z",
  "title": "Club_Loop_128BPM_8Indices",
  "description": "",
  "source": {
    "fileName": "club_loop.mp4",
    "durationMs": 124000,
    "width": 1920,
    "height": 1080,
    "fpsNominal": 30.0,
    "frameCount": 3720
  },
  "bake": {
    "targetFps": 240.0,
    "interpolationFactor": 8.0,
    "aiEngine": {
      "id": "rife-ncnn-vulkan",
      "version": "4.6",
      "model": "rife-v4.6",
      "precision": "fp16"
    }
  },
  "media": {
    "primaryVideo": {
      "path": "media/master.mov",
      "container": "mov",
      "codec": "hap_q",
      "width": 1920,
      "height": 1080,
      "fps": 240.0,
      "frameCount": 29760,
      "durationMs": 124000
    }
  },
  "transport": {
    "defaultMode": "loop",
    "defaultDirection": 1.0,
    "defaultSpeed": 1.0,
    "seekMode": "frame-accurate"
  },
  "markers": [
    {
      "id": "m_intro",
      "index": 1,
      "frame": 0,
      "state": {
        "direction": 1.0,
        "speed": 1.0,
        "mode": "loop",
        "easing": "linear"
      }
    }
  ]
}
```

## 7. Versioning

`schema` identifies the format namespace.

`schemaVersion` uses semantic versioning:

- patch: clarification or non-breaking additions
- minor: new optional fields
- major: breaking structural or semantic changes

Reader behavior:

- reject unknown major versions
- ignore unknown fields within supported major version
- apply documented defaults to missing optional fields

## 8. Media Rules

`v1` supports exactly one primary playback media file.

The source of truth for playback timing is:

- `media.primaryVideo.frameCount`
- `media.primaryVideo.fps`
- marker `frame`

Recommended supported media targets for `v1`:

- `mov + hap_q`
- `mov + prores_422`
- `mov + prores_4444`

Primary media path:

- must be relative to archive root
- must resolve to an existing file inside the bundle

## 9. Marker Model

Markers define playback entry points and segment state.

Required marker fields:

- `id`
- `index`
- `frame`

Optional marker fields:

- `label`
- `color`
- `timeMs`
- `segmentEndMarkerId`
- `state`

Recommended marker shape:

```json
{
  "id": "m_hit",
  "index": 2,
  "label": "Hit",
  "color": "#FCA5A5",
  "frame": 1240,
  "timeMs": 5167,
  "segmentEndMarkerId": "m_tail",
  "state": {
    "direction": -0.5,
    "speed": 0.5,
    "mode": "pingpong",
    "easing": "cubic-out"
  }
}
```

Rules:

- `id` must be unique within bundle
- `index` must be unique within bundle
- `frame` must be within media bounds
- if `timeMs` is present and conflicts with `frame`, `frame` wins

## 10. Playback Semantics

Teleport behavior:

1. select target marker
2. optionally wait for quantization boundary
3. seek to exact marker frame
4. apply marker state
5. continue playback according to segment mode

Segment resolution:

- if `segmentEndMarkerId` exists, use that marker as segment end
- otherwise use the next marker in frame order
- if no later marker exists, segment end defaults to end of media

Recommended `mode` values:

- `once`
- `loop`
- `pingpong`
- `hold`

Recommended `easing` values for `v1`:

- `linear`
- `sine-in`
- `sine-out`
- `sine-in-out`
- `cubic-in`
- `cubic-out`
- `cubic-in-out`
- `bounce-out`

## 11. Progress Semantics

Playback consumers should expose segment progress as:

- `0.0` to `1.0`

Recommended interpretation for `v1`:

- normalized position between the lower and upper segment frame bounds
- independent of playback direction

This keeps modulation behavior stable when direction changes.

## 12. Runtime Cache Guidance

VJB is a transport container, not a required direct-playback container.

Recommended runtime behavior:

- read `manifest.json` from archive
- validate bundle
- extract primary media to local cache
- playback from cached media path

Benefits:

- predictable seek behavior
- simpler decoder integration
- no dependency on archive-aware media playback

## 13. Validation

Minimum validation rules:

- `manifest.json` exists
- `schema` is recognized
- `schemaVersion` is parseable
- `bundleId` is present
- `media.primaryVideo.path` exists
- `bake.targetFps > 0`
- all marker ids are unique
- all marker indices are unique
- all marker frames are in range

Soft warnings:

- thumbnails missing
- markers not pre-sorted by frame
- `timeMs` inconsistent with `frame`
- optional analysis files missing

## 14. Extensions

Implementations may add extra data under:

```json
{
  "custom": {
    "extensions": {}
  }
}
```

Extension rules:

- must not redefine core field meaning
- must be safe to ignore for core playback
- should use namespaced keys

## 15. Open Format Expectations

VJB should be treated as:

- an openly documented format
- implementable by multiple tools
- independent from any one vendor runtime

Reference apps may add tooling around the format, but must not rely on hidden
fields or private decoding rules to achieve correct core playback behavior.
