# VJB Design Principles

1. Open by default
   The format must be publicly documented and implementable without a private
   agreement with one vendor.

2. One format, multiple tools
   VJB must be usable by more than one authoring or playback application.

3. Portable performance intent
   The format carries not only media, but also marker and transport intent for
   realtime playback workflows.

4. No proprietary codec dependency
   VJB is a bundle format, not a codec. It should remain compatible with common
   media tooling.

5. Deterministic playback
   The same bundle should produce the same marker and segment behavior across
   conforming implementations.

6. Simple first, extensible later
   The core specification should stay small and stable, with explicit extension
   points for future features.

7. Forward-compatible metadata
   Unknown optional fields should be safely ignorable within a supported major
   version.

8. No hidden vendor fields
   Core interoperability must not depend on private metadata or undisclosed
   behavior.

9. Standard packaging
   The format should rely on ordinary tooling such as ZIP, JSON, and standard
   media files.

10. Runtime safety over cleverness
    Convenience in packaging must not compromise low-latency playback,
    deterministic seek, or predictable cache behavior.

11. Graceful degradation
    Readers should be able to report unsupported optional features without
    failing the entire bundle when core playback remains possible.

12. Validation is part of the format
    A useful open format needs explicit validation rules, fixtures, and clear
    error behavior.

13. Separation of authoring and playback
    The format should not assume a specific UI or one authoring workflow.

14. No DRM in the core spec
    Licensing or product gating must not be part of the core format.

15. Stable IDs over UI labels
    Internal references must rely on stable identifiers, not presentation-layer
    names or ordering.
