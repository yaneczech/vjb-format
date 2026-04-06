# Changelog

## [1.0.0-draft.1] - Working Draft

- Add optional marker `roles` with backward-compatible default behavior of
  `["cue"]` when omitted.
- Distinguish playback cue markers from quantize timing markers.
- Add optional marker `quantize` metadata using `gridIndex` plus `phase`.
- Expand `transport.quantizeUnit` to support `half-beat`, `quarter-beat`, and
  `eighth-beat`.
- Clarify that `media.primaryVideo.alpha` is the authoritative playback alpha
  flag.
- Clarify that marker frames always reference baked `primaryVideo` frame space.
- Make `transport.defaultSpeed` optional in schema; readers must assume `1.0`
  when omitted.
- Add explicit default for `transport.quantizeUnit`: readers must treat omitted
  value as `none`.
- Define semantics for each `transport.quantizeUnit` value, including `marker`
  (snap to nearest marker frame in frame order).
- Mark `proxy/` and `analysis/` as reserved paths with no normative definition
  in `v1`; remove `proxies` from core schema.
- Clarify `easing` as an advisory hint for entry state adoption on
  trigger/teleport, not a frame-stepping law.
- Document that role-dependent field constraints must be enforced by code-level
  validators, not JSON Schema.
- Require readers to derive frame order from `frame` values and not rely on
  marker array order.
