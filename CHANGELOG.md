# Changelog

## Unreleased

- Add optional marker `roles` with backward-compatible default behavior of
  `["cue"]` when omitted.
- Distinguish playback cue markers from quantize timing markers.
- Add optional marker `quantize` metadata using `gridIndex` plus `phase`.
- Expand `transport.quantizeUnit` to support `half-beat`, `quarter-beat`, and
  `eighth-beat`.
- Clarify that `media.primaryVideo.alpha` is the authoritative playback alpha
  flag.
- Clarify that marker frames always reference baked `primaryVideo` frame space.
