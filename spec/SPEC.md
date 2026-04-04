# VJB Specification Draft

## 1. Overview

VJB is an open bundle format for packaged temporal media playback.

A VJB file contains:

- a primary baked media file
- playback metadata
- optional analysis and thumbnail assets

The format is designed for low-latency marker-based playback workflows such as
teleport seek, reverse traversal, looping, and segment-based live performance.

## 2. Conformance

Interpretation of normative language in this document:

- `must` and `must not` indicate hard interoperability requirements
- `should` and `should not` indicate strong recommendations
- `may` indicates optional behavior

Conforming `v1` reader behavior:

- must parse the bundle as a ZIP archive
- must read `manifest.json` from archive root
- must validate required fields and hard validation rules
- must reject unsupported major schema versions
- must ignore unknown optional fields within a supported major version
- must use manifest timing fields as the authoritative playback timing source

Conforming `v1` writer behavior:

- must produce a `manifest.json` that satisfies the schema and hard validation
  rules
- must write `media.primaryVideo.path` as an archive-relative path
- must not rely on private or undocumented fields for correct core playback

## 3. Design Goals

- Portable between authoring and playback tools
- Deterministic marker and segment behavior
- Simple packaging with ordinary tools
- Strong forward compatibility rules
- Good runtime ergonomics for cached playback

## 4. Non-Goals

- Defining a new video codec
- Replacing editing timelines such as OTIO or AAF
- Embedding app-specific UI state into the interchange format
- Requiring direct playback from inside compressed archive storage

## 5. Container

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

## 6. Directory Layout

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

## 7. Manifest

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

Root manifest field guide:

| Field | Required | Meaning | Used By |
| --- | --- | --- | --- |
| `schema` | yes | Format namespace identifier | readers, validators |
| `schemaVersion` | yes | Format version using semver | readers, validators |
| `bundleId` | yes | Stable bundle identifier | cataloging, caching, tooling |
| `createdAt` | no | Bundle creation timestamp | diagnostics, tooling |
| `title` | yes | Human-readable bundle title | UIs, asset browsers |
| `description` | no | Freeform bundle description | UIs, tooling |
| `source` | yes | Provenance and source media facts | tooling, diagnostics |
| `bake` | yes | How the playback media was prepared | tooling, diagnostics |
| `media` | yes | Playback asset references, timing, and playback asset flags | readers, validators |
| `transport` | yes | Bundle-level default playback intent | readers, playback apps |
| `markers` | yes | Marker entry points and segment metadata | readers, playback apps |
| `custom` | no | Namespaced extension data | extension-aware tools |

Field intent grouping:

- provenance and diagnostics: `bundleId`, `createdAt`, `source`, `bake`
- core playback semantics: `media`, `transport`, `markers`
- UI-facing metadata: `title`, `description`
- extensions: `custom`

## 8. Versioning

`schema` identifies the format namespace.

`schemaVersion` uses semantic versioning:

- patch: clarification or non-breaking additions
- minor: new optional fields
- major: breaking structural or semantic changes

Reader behavior:

- reject unknown major versions
- ignore unknown fields within supported major version
- apply documented defaults to missing optional fields

## 9. Media Rules

`v1` supports exactly one primary playback media file.

The source of truth for playback timing is:

- `media.primaryVideo.frameCount`
- `media.primaryVideo.fps`
- marker `frame`

For `v1`, all playback timing references in markers and transport behavior are
defined in the baked frame space of `media.primaryVideo`, not in the frame or
time space of `source`.

Recommended supported media targets for `v1`:

- `mov + hap_q`
- `mov + prores_422`
- `mov + prores_4444`

Primary media path:

- must be relative to archive root
- must resolve to an existing file inside the bundle
- must not be absolute
- must not contain `.` or `..` path segments after normalization
- must use `/` as the path separator inside the archive

MOV guidance for `v1`:

- primary playback media for `v1` should use constant frame rate export
- deterministic playback behavior depends on a stable baked frame space with a
  single effective frame rate
- playback timing should be derived from manifest `frameCount` and `fps`, not
  from container timestamp quirks
- `media.primaryVideo.alpha` should be treated as the authoritative playback
  alpha flag for renderer setup
- `source.hasAlpha` is descriptive source metadata only and should not override
  `media.primaryVideo.alpha` for playback decisions
- alpha-bearing exports should use a codec/profile that preserves alpha, such
  as `prores_4444`
- implementations should treat the MOV file as a cached local playback asset,
  not as a stream-optimized delivery file
- authoring tools should avoid encoder settings that change effective frame
  count without updating manifest timing fields
- readers may inspect container metadata for diagnostics, but manifest timing
  remains authoritative for VJB playback

## 10. Marker Model

Markers define playback entry points and segment state.

For `v1`, marker `frame` is an integer zero-based frame index into
`media.primaryVideo`.

Normative frame-space rule:

- `markers[].frame` must reference the zero-based frame index in the baked
  primary playback media described by `media.primaryVideo`, not the original
  source media

Required marker fields:

- `id`
- `index`
- `frame`

Optional marker fields:

- `label`
- `color`
- `roles`
- `quantize`
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
  "roles": ["cue"],
  "quantize": {
    "gridIndex": 10,
    "phase": 0.25
  },
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

Marker roles:

Markers may optionally declare semantic roles via `roles`.

Supported roles in `v1`:

- `cue`: a playback entry marker that may define segment behavior
- `quantize`: a timing reference marker for snapping, sync, or quantized jumps

If `roles` is omitted, readers must treat the marker as if it were:

```json
{
  "roles": ["cue"]
}
```

This preserves backward compatibility with manifests created before marker
roles were introduced.

Quantize metadata:

Markers that include the `quantize` role may optionally declare quantize
metadata via `quantize`.

Supported quantize fields in `v1`:

- `gridIndex`: the integer grid position counted from the start of the active
  quantize timeline
- `phase`: the normalized position within one quantize grid step

If `quantize.phase` is omitted, readers should treat it as `0.0`.

Quantize phase is defined in the half-open interval `0.0 <= phase < 1.0`.

Quantize grid semantics:

- `transport.quantizeUnit` defines what one quantize grid step means
- `quantize.gridIndex = 0` refers to the first grid step in that unit space
- `quantize.phase = 0.0` means exactly on the grid step
- `quantize.phase = 0.5` means halfway through the grid step

Supported quantize units in `v1`:

- `beat`
- `bar`
- `half-beat`
- `quarter-beat`
- `eighth-beat`

Examples:

- `{"gridIndex": 10, "phase": 0.0}` with `transport.quantizeUnit = "bar"`:
  exactly on the eleventh bar boundary
- `{"gridIndex": 10, "phase": 0.25}` with `transport.quantizeUnit = "beat"`:
  the eleventh beat plus one quarter of a beat
- `{"gridIndex": 40, "phase": 0.5}` with `transport.quantizeUnit =
  "quarter-beat"`: halfway through the forty-first quarter-beat step

Rules:

- `id` must be unique within bundle
- `index` must be unique within bundle
- `frame` must be within media bounds
- `frame` must be less than `media.primaryVideo.frameCount`
- `frame` is authoritative for playback and transport math
- if `timeMs` is present and conflicts with `frame`, `frame` wins
- `timeMs` is advisory metadata for tooling and UI display
- if `segmentEndMarkerId` is present, it must resolve to an existing marker
- if `segmentEndMarkerId` is present, it must reference a marker that includes
  the `cue` role
- `segmentEndMarkerId` must not reference the same marker
- the resolved segment end marker must have `frame >=` the start marker frame
- if `quantize` is present, it is only meaningful for markers that include the
  `quantize` role
- unknown marker roles within a supported major version should be ignored unless
  explicitly supported by the implementation

Playback role semantics:

- only markers that include the `cue` role participate in implicit playback
  segment resolution
- markers with the `quantize` role may be used as timing references for
  snapping, sync, or quantized jumps
- markers with the `quantize` role do not implicitly start playback segments
- markers with the `quantize` role do not implicitly terminate playback
  segments
- `quantize.gridIndex` and `quantize.phase` define where the marker sits within
  the active quantize grid
- `state` and `segmentEndMarkerId` are only meaningful for markers that include
  the `cue` role

Authoring note:

- authoring tools may internally store markers in source frame space or source
  time space
- when exporting VJB, authoring tools must convert marker positions into the
  baked frame space of `media.primaryVideo`
- this export conversion should happen before writing `markers[].frame`

Example baked-frame conversion:

- source clip at `30.0 fps`, baked export at `120.0 fps`: source frame `300`
  maps to baked frame `1200`
- source clip at `30.0 fps`, baked export at `240.0 fps`: source frame `300`
  maps to baked frame `2400`
- equivalent time-based conversion is `bakedFrame = sourceTimeSeconds *
  media.primaryVideo.fps`

Rounding guidance for authoring tools:

- if conversion starts from fractional source time, tools should use one stable
  rounding strategy consistently for the whole export
- nearest-frame rounding is recommended for `v1`
- exported manifests should not mix rounding strategies across markers within
  the same bundle

## 11. Playback Semantics

Teleport behavior:

1. select target marker
2. resolve bundle defaults, marker state, and any active runtime overrides
3. if the effective quantize unit is absent or `none`, continue immediately;
   otherwise wait for the next quantization boundary
4. seek to exact marker frame
5. continue playback according to the effective segment mode

Segment resolution:

- if `segmentEndMarkerId` exists, use that marker as segment end
- otherwise use the next marker with the `cue` role in frame order
- if no later marker exists, segment end defaults to end of media

Normative `v1` segment rules:

- segment start is the target marker frame
- segment end is inclusive when it resolves to another marker frame
- segment end is `media.primaryVideo.frameCount - 1` when it defaults to end of
  media
- a resolved segment must satisfy `segmentEndFrame >= segmentStartFrame`
- a single-frame segment where `segmentEndFrame == segmentStartFrame` is valid

`transport.quantizeUnit` values for `v1`:

- `none`
- `marker`
- `beat`
- `bar`
- `half-beat`
- `quarter-beat`
- `eighth-beat`

Recommended `mode` values:

- `once`
- `loop`
- `pingpong`
- `hold`

Normative `v1` mode behavior:

- `once`: advance in the current direction until the segment end is reached,
  then stop on the boundary frame
- `loop`: on reaching a segment boundary, jump to the opposite segment boundary
  and continue without changing direction
- `pingpong`: on reaching a segment boundary, remain on the boundary frame for
  that tick, then invert direction
- `hold`: seek to the segment start frame and remain there until an external
  transport action changes playback state

State resolution:

- `transport` defines bundle-level default playback state
- marker `state` defines the bundle-provided entry behavior for that marker
- omitted marker `state` fields inherit from `transport`
- upon teleport or trigger to a marker, readers should adopt the marker's
  effective entry behavior unless explicitly overridden by the live controller
- playback applications may apply runtime overrides after marker resolution
- runtime overrides take precedence over both `transport` and marker `state`
- runtime overrides may replace `speed`, `direction`, `mode`, `easing`, and
  `quantizeUnit`
- `direction` of `0` is invalid for `v1`; direction must be either negative or
  positive

Boundary behavior:

- for forward playback, the upper segment bound is the active stop boundary
- for reverse playback, the lower segment bound is the active stop boundary
- conforming readers must not read past either boundary before applying the
  selected mode behavior

Recommended `easing` values for `v1`:

- `linear`
- `sine-in`
- `sine-out`
- `sine-in-out`
- `cubic-in`
- `cubic-out`
- `cubic-in-out`
- `bounce-out`

## 12. Progress Semantics

Playback consumers should expose segment progress as:

- `0.0` to `1.0`

Recommended interpretation for `v1`:

- normalized position between the lower and upper segment frame bounds
- independent of playback direction
- computed from inclusive segment bounds

This keeps modulation behavior stable when direction changes.

Normative `v1` progress rules:

- if `segmentStartFrame == segmentEndFrame`, progress is always `1.0`
- otherwise progress is `(currentFrame - segmentStartFrame) / (segmentEndFrame -
  segmentStartFrame)`
- readers must clamp the exposed value to the closed interval `0.0` to `1.0`
- reverse playback does not invert progress; only frame position within the
  segment matters

## 13. Runtime Cache Guidance

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

## 14. Validation

Minimum validation rules:

- `manifest.json` exists
- `schema` is recognized
- `schemaVersion` is parseable
- `bundleId` is present
- `media.primaryVideo.path` exists
- `media.primaryVideo.path` does not escape the archive root when normalized
- `bake.targetFps > 0`
- `transport.defaultDirection` is not `0`
- all marker ids are unique
- all marker indices are unique
- all marker frames are in range
- every `segmentEndMarkerId`, if present, resolves to an existing marker
- no `segmentEndMarkerId` points to the same marker
- no resolved segment end frame is earlier than its start frame

Minimum validator behavior:

- violations of the minimum validation rules are hard errors
- unknown fields within a supported major version must not be hard errors
- unsupported optional features may produce warnings, but must not invalidate
  otherwise playable bundles

Soft warnings:

- thumbnails missing
- markers not pre-sorted by frame
- `timeMs` inconsistent with `frame`
- optional analysis files missing

## 15. Extensions

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

## 16. Open Format Expectations

VJB should be treated as:

- an openly documented format
- implementable by multiple tools
- independent from any one vendor runtime

Reference apps may add tooling around the format, but must not rely on hidden
fields or private decoding rules to achieve correct core playback behavior.
