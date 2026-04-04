## VJB Examples

These examples are implementation-oriented manifest fixtures for `v1`.

Suggested use:

- `valid-minimal.manifest.json`: smallest useful playable shape
- `valid-segmented.manifest.json`: markers with segment resolution and transport
  defaults
- `valid-marker-roles.manifest.json`: explicit `cue` and `quantize` marker role
  combinations plus `quantize.gridIndex` and `quantize.phase`
- `warning-timeMs-mismatch.manifest.json`: valid manifest that should produce a
  warning because `timeMs` does not match the authoritative frame timing
- `invalid-bad-path.manifest.json`: invalid because the media path escapes the
  archive root
- `invalid-missing-segment-target.manifest.json`: invalid because a
  `segmentEndMarkerId` points to a missing marker

These files are JSON manifests only. They are not complete `.vjb` bundles by
themselves.
