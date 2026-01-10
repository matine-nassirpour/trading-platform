"""
DOMAIN ARCHITECTURE CHARTER
───────────────────────────

This document is NORMATIVE.

It defines the allowed roles of all domain objects and the strict
responsibilities attached to each role.

This charter is binding for:
- Code
- Reviews
- Audits
- Certification
"""

from enum import Enum


class DomainRole(str, Enum):
    AGGREGATE = "aggregate"
    ENTITY = "entity"
    VALUE_OBJECT = "value_object"
    POLICY = "policy"
    SERVICE = "service"
    FACTORY = "factory"
    EVENT = "event"
    PROJECTION = "projection"
    READ_MODEL = "read_model"
    CURSOR = "cursor"


ROLE_DEFINITION = {
    DomainRole.AGGREGATE: (
        """
    Aggregate Roots are the sole authority over domain state.
    They:
    - Own invariants
    - Emit events
    - Accept commands
    - Are the ONLY objects allowed to mutate domain state
    """
    ),
    DomainRole.ENTITY: (
        """
    Entities are identity-bearing domain objects.
    They:
    - Are owned by an Aggregate
    - Never exist outside their Aggregate
    - Never enforce global invariants
    """
    ),
    DomainRole.VALUE_OBJECT: (
        """
    Immutable, self-validating, context-free objects.
    They:
    - Have no identity
    - Are purely defined by their value
    - Enforce only local invariants
    """
    ),
    DomainRole.POLICY: (
        """
    Normative rule engines.
    They:
    - Enforce WHAT is allowed
    - Are pure and deterministic
    - Do NOT compute metrics
    - Do NOT mutate state
    """
    ),
    DomainRole.SERVICE: (
        """
    Computational services.
    They:
    - Compute values
    - Never enforce permissions
    - Never mutate state
    - Never make authorization decisions
    """
    ),
    DomainRole.FACTORY: (
        """
    Creation and validation orchestrators.
    They:
    - Create aggregates, events, or value objects
    - Validate preconditions
    - Never hold state
    """
    ),
    DomainRole.EVENT: (
        """
    Immutable facts that something happened.
    They:
    - Represent historical truth
    - Are never changed
    - Are audit artifacts
    """
    ),
}
