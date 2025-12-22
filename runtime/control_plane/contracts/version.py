"""
Canonical version of the Admin HTTP control-plane contract.

This version identifies the semantic shape of the JSON responses
exposed by the runtime control-plane.

Any backward-incompatible change MUST bump this version.
"""

CONTROL_PLANE_HTTP_API_VERSION: str = "2025.1"
