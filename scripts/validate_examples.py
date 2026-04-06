#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_ID = "com.vjb.bundle"
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
ALLOWED_CODECS = {"hap_q", "prores_422", "prores_4444"}
ALLOWED_MODES = {"once", "loop", "pingpong", "hold"}
ALLOWED_EASING = {
    "linear",
    "sine-in",
    "sine-out",
    "sine-in-out",
    "cubic-in",
    "cubic-out",
    "cubic-in-out",
    "bounce-out",
}
ALLOWED_MARKER_ROLES = {"cue", "quantize"}
ALLOWED_QUANTIZE_UNITS = {
    "none",
    "marker",
    "beat",
    "bar",
    "half-beat",
    "quarter-beat",
    "eighth-beat",
}


@dataclass
class ValidationResult:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def status(self) -> str:
        if self.errors:
            return "ERROR"
        if self.warnings:
            return "WARN"
        return "OK"


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def add_error_if_missing(result: ValidationResult, obj: dict[str, Any], key: str) -> Any:
    if key not in obj:
        result.errors.append(f"missing required field `{key}`")
        return None
    return obj[key]


def validate_manifest(path: Path) -> ValidationResult:
    result = ValidationResult(path=path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"invalid JSON: {exc}")
        return result

    if not isinstance(manifest, dict):
        result.errors.append("manifest root must be an object")
        return result

    schema = add_error_if_missing(result, manifest, "schema")
    if schema is not None and schema != SCHEMA_ID:
        result.errors.append(f"`schema` must be `{SCHEMA_ID}`")

    schema_version = add_error_if_missing(result, manifest, "schemaVersion")
    if schema_version is not None and (
        not isinstance(schema_version, str) or not SEMVER_RE.match(schema_version)
    ):
        result.errors.append("`schemaVersion` must be a semantic version string")

    for key in ("bundleId", "title"):
        value = add_error_if_missing(result, manifest, key)
        if value is not None and (not isinstance(value, str) or not value):
            result.errors.append(f"`{key}` must be a non-empty string")

    source = validate_source(result, manifest.get("source"))
    validate_bake(result, manifest.get("bake"))
    primary_video = validate_media(result, manifest.get("media"))
    transport = validate_transport(result, manifest.get("transport"))
    validate_markers(result, manifest.get("markers"), primary_video, transport)
    return result


def validate_source(result: ValidationResult, source: Any) -> dict[str, Any] | None:
    required = ("fileName", "durationMs", "width", "height", "fpsNominal", "frameCount")
    if not isinstance(source, dict):
        result.errors.append("`source` must be an object")
        return None
    for key in required:
        if key not in source:
            result.errors.append(f"`source.{key}` is required")
    validate_positive_int(result, source, "durationMs", "source", minimum=0)
    validate_positive_int(result, source, "width", "source", minimum=1)
    validate_positive_int(result, source, "height", "source", minimum=1)
    validate_positive_int(result, source, "frameCount", "source", minimum=1)
    validate_positive_number(result, source, "fpsNominal", "source")
    return source


def validate_bake(result: ValidationResult, bake: Any) -> None:
    if not isinstance(bake, dict):
        result.errors.append("`bake` must be an object")
        return
    if "targetFps" not in bake:
        result.errors.append("`bake.targetFps` is required")
        return
    validate_positive_number(result, bake, "targetFps", "bake")


def validate_media(result: ValidationResult, media: Any) -> dict[str, Any] | None:
    if not isinstance(media, dict):
        result.errors.append("`media` must be an object")
        return None
    primary_video = media.get("primaryVideo")
    if not isinstance(primary_video, dict):
        result.errors.append("`media.primaryVideo` must be an object")
        return None

    required = ("path", "container", "codec", "width", "height", "fps", "frameCount", "durationMs")
    for key in required:
        if key not in primary_video:
            result.errors.append(f"`media.primaryVideo.{key}` is required")

    path = primary_video.get("path")
    if not isinstance(path, str) or not path:
        result.errors.append("`media.primaryVideo.path` must be a non-empty string")
    else:
        parts = path.split("/")
        if path.startswith("/"):
            result.errors.append("`media.primaryVideo.path` must not be absolute")
        if any(part in {".", ".."} for part in parts):
            result.errors.append("`media.primaryVideo.path` must not contain `.` or `..` segments")
        if "//" in path:
            result.errors.append("`media.primaryVideo.path` must not contain empty segments")

    if primary_video.get("container") != "mov":
        result.errors.append("`media.primaryVideo.container` must be `mov`")
    if primary_video.get("codec") not in ALLOWED_CODECS:
        result.errors.append("`media.primaryVideo.codec` is not a supported v1 codec")

    validate_positive_int(result, primary_video, "width", "media.primaryVideo", minimum=1)
    validate_positive_int(result, primary_video, "height", "media.primaryVideo", minimum=1)
    validate_positive_number(result, primary_video, "fps", "media.primaryVideo")
    validate_positive_int(result, primary_video, "frameCount", "media.primaryVideo", minimum=1)
    validate_positive_int(result, primary_video, "durationMs", "media.primaryVideo", minimum=0)
    alpha = primary_video.get("alpha")
    if alpha is not None and not isinstance(alpha, bool):
        result.errors.append("`media.primaryVideo.alpha` must be a boolean when present")
    return primary_video


def validate_transport(result: ValidationResult, transport: Any) -> dict[str, Any] | None:
    if not isinstance(transport, dict):
        result.errors.append("`transport` must be an object")
        return None
    required = ("defaultMode", "defaultDirection", "seekMode")
    for key in required:
        if key not in transport:
            result.errors.append(f"`transport.{key}` is required")

    if transport.get("defaultMode") not in ALLOWED_MODES:
        result.errors.append("`transport.defaultMode` must be a supported mode")

    direction = transport.get("defaultDirection")
    if not is_number(direction) or not (-1 <= direction <= 1) or direction == 0:
        result.errors.append("`transport.defaultDirection` must be a non-zero number between -1 and 1")

    speed = transport.get("defaultSpeed")
    if speed is not None and (not is_number(speed) or speed < 0):
        result.errors.append("`transport.defaultSpeed` must be a number >= 0 when present")

    if transport.get("seekMode") != "frame-accurate":
        result.errors.append("`transport.seekMode` must be `frame-accurate`")

    quantize_unit = transport.get("quantizeUnit")
    if quantize_unit is not None and quantize_unit not in ALLOWED_QUANTIZE_UNITS:
        result.errors.append("`transport.quantizeUnit` is not a supported v1 value")
    return transport


def validate_markers(
    result: ValidationResult,
    markers: Any,
    primary_video: dict[str, Any] | None,
    transport: dict[str, Any] | None,
) -> None:
    if not isinstance(markers, list) or not markers:
        result.errors.append("`markers` must be a non-empty array")
        return

    frame_count = None
    fps = None
    if primary_video:
        frame_count = primary_video.get("frameCount")
        fps = primary_video.get("fps")

    marker_by_id: dict[str, dict[str, Any]] = {}
    indices: set[int] = set()
    effective_roles: dict[str, set[str]] = {}

    for idx, marker in enumerate(markers):
        label = f"markers[{idx}]"
        if not isinstance(marker, dict):
            result.errors.append(f"`{label}` must be an object")
            continue

        marker_id = marker.get("id")
        if not isinstance(marker_id, str) or not marker_id:
            result.errors.append(f"`{label}.id` must be a non-empty string")
            continue
        if marker_id in marker_by_id:
            result.errors.append(f"duplicate marker id `{marker_id}`")
        marker_by_id[marker_id] = marker

        index = marker.get("index")
        if not isinstance(index, int) or isinstance(index, bool) or index < 1:
            result.errors.append(f"`{label}.index` must be an integer >= 1")
        elif index in indices:
            result.errors.append(f"duplicate marker index `{index}`")
        else:
            indices.add(index)

        frame = marker.get("frame")
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
            result.errors.append(f"`{label}.frame` must be an integer >= 0")
        elif isinstance(frame_count, int) and frame >= frame_count:
            result.errors.append(f"`{label}.frame` must be less than media.primaryVideo.frameCount")

        color = marker.get("color")
        if color is not None and (not isinstance(color, str) or not COLOR_RE.match(color)):
            result.errors.append(f"`{label}.color` must be a valid hex color when present")

        roles = marker.get("roles")
        if roles is None:
            role_set = {"cue"}
        else:
            role_set = set()
            if not isinstance(roles, list) or not roles:
                result.errors.append(f"`{label}.roles` must be a non-empty array when present")
            else:
                for role in roles:
                    if role not in ALLOWED_MARKER_ROLES:
                        result.errors.append(f"`{label}.roles` contains unsupported role `{role}`")
                    else:
                        role_set.add(role)
                if len(role_set) != len(roles):
                    result.errors.append(f"`{label}.roles` must not contain duplicates")
        effective_roles[marker_id] = role_set

        time_ms = marker.get("timeMs")
        if time_ms is not None:
            if not isinstance(time_ms, int) or isinstance(time_ms, bool) or time_ms < 0:
                result.errors.append(f"`{label}.timeMs` must be an integer >= 0")
            elif isinstance(frame, int) and is_number(fps):
                expected_time_ms = int(round(frame * 1000.0 / float(fps)))
                if abs(time_ms - expected_time_ms) > 1:
                    result.warnings.append(
                        f"`{label}.timeMs` ({time_ms}) does not match frame-derived timing ({expected_time_ms})"
                    )

        validate_marker_state(result, label, marker.get("state"))
        validate_quantize(result, label, marker.get("quantize"), role_set)

    for marker_id, marker in marker_by_id.items():
        roles = effective_roles[marker_id]
        segment_end = marker.get("segmentEndMarkerId")
        if segment_end is not None:
            if not isinstance(segment_end, str) or not segment_end:
                result.errors.append(f"marker `{marker_id}` has invalid `segmentEndMarkerId`")
            elif segment_end == marker_id:
                result.errors.append(f"marker `{marker_id}` must not reference itself as segment end")
            elif segment_end not in marker_by_id:
                result.errors.append(f"marker `{marker_id}` references missing segment end `{segment_end}`")
            else:
                if "cue" not in effective_roles.get(segment_end, set()):
                    result.errors.append(
                        f"marker `{marker_id}` must reference a `cue` marker as segment end"
                    )
                start_frame = marker.get("frame")
                end_frame = marker_by_id[segment_end].get("frame")
                if isinstance(start_frame, int) and isinstance(end_frame, int) and end_frame < start_frame:
                    result.errors.append(
                        f"marker `{marker_id}` resolves to segment end frame earlier than its start frame"
                    )
        if marker.get("state") is not None and "cue" not in roles:
            result.warnings.append(f"marker `{marker_id}` has `state` without the `cue` role")

    explicit_end_usage: dict[str, list[str]] = {}
    for marker_id, marker in marker_by_id.items():
        segment_end = marker.get("segmentEndMarkerId")
        if isinstance(segment_end, str) and segment_end in marker_by_id:
            explicit_end_usage.setdefault(segment_end, []).append(marker_id)

    for end_marker_id, start_markers in explicit_end_usage.items():
        if len(start_markers) > 1:
            joined = ", ".join(sorted(start_markers))
            result.errors.append(
                f"explicit cue pairing is one-to-one; end marker `{end_marker_id}` is shared by multiple start markers: {joined}"
            )

    if transport and transport.get("quantizeUnit") == "marker":
        quantize_markers = [marker_id for marker_id, roles in effective_roles.items() if "quantize" in roles]
        if not quantize_markers:
            result.warnings.append(
                "`transport.quantizeUnit` is `marker` but no markers include the `quantize` role"
            )


def validate_marker_state(result: ValidationResult, label: str, state: Any) -> None:
    if state is None:
        return
    if not isinstance(state, dict):
        result.errors.append(f"`{label}.state` must be an object when present")
        return
    direction = state.get("direction")
    if direction is not None and (not is_number(direction) or not (-1 <= direction <= 1) or direction == 0):
        result.errors.append(f"`{label}.state.direction` must be a non-zero number between -1 and 1")
    speed = state.get("speed")
    if speed is not None and (not is_number(speed) or speed < 0):
        result.errors.append(f"`{label}.state.speed` must be a number >= 0")
    mode = state.get("mode")
    if mode is not None and mode not in ALLOWED_MODES:
        result.errors.append(f"`{label}.state.mode` must be a supported mode")
    easing = state.get("easing")
    if easing is not None and easing not in ALLOWED_EASING:
        result.errors.append(f"`{label}.state.easing` must be a supported easing")


def validate_quantize(
    result: ValidationResult, label: str, quantize: Any, roles: set[str]
) -> None:
    if quantize is None:
        return
    if not isinstance(quantize, dict):
        result.errors.append(f"`{label}.quantize` must be an object when present")
        return
    if "quantize" not in roles:
        result.warnings.append(f"`{label}.quantize` is present without the `quantize` role")
    grid_index = quantize.get("gridIndex")
    if grid_index is None:
        result.errors.append(f"`{label}.quantize.gridIndex` is required when `quantize` is present")
    elif not isinstance(grid_index, int) or isinstance(grid_index, bool) or grid_index < 0:
        result.errors.append(f"`{label}.quantize.gridIndex` must be an integer >= 0")
    phase = quantize.get("phase")
    if phase is not None and (not is_number(phase) or phase < 0 or phase >= 1):
        result.errors.append(f"`{label}.quantize.phase` must satisfy 0 <= phase < 1")


def validate_positive_int(
    result: ValidationResult, obj: dict[str, Any], key: str, prefix: str, minimum: int
) -> None:
    value = obj.get(key)
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        result.errors.append(f"`{prefix}.{key}` must be an integer >= {minimum}")


def validate_positive_number(result: ValidationResult, obj: dict[str, Any], key: str, prefix: str) -> None:
    value = obj.get(key)
    if value is None:
        return
    if not is_number(value) or value <= 0:
        result.errors.append(f"`{prefix}.{key}` must be a number > 0")


def iter_manifests(base: Path, target: str | None) -> list[Path]:
    if target:
        path = Path(target)
        if not path.is_absolute():
            path = base / target
        return [path]
    return sorted((base / "examples").glob("*.manifest.json"))


def expected_status_for(path: Path) -> str:
    name = path.name
    if name.startswith("invalid-"):
        return "ERROR"
    if name.startswith("warning-"):
        return "WARN"
    return "OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VJB manifest examples.")
    parser.add_argument(
        "--manifest",
        help="Validate a single manifest path relative to the vjb-format directory.",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parents[1]
    manifests = iter_manifests(base, args.manifest)
    if not manifests:
        print("No manifest files found.", file=sys.stderr)
        return 1

    exit_code = 0
    for manifest_path in manifests:
        result = validate_manifest(manifest_path)
        expected = expected_status_for(manifest_path)
        actual = result.status()
        mismatch = expected != actual
        print(f"{manifest_path.relative_to(base)}: {actual} (expected {expected})")
        for message in result.errors:
            print(f"  error: {message}")
        for message in result.warnings:
            print(f"  warning: {message}")
        if mismatch:
            exit_code = 1
            print("  error: result classification does not match filename expectation")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
