from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole


class RoleRule:
    def __init__(
        self,
        *,
        allow_methods: bool,
        allow_state: bool,
        allow_mutation: bool,
        must_be_dataclass: bool = False,
    ):
        self.allow_methods = allow_methods
        self.allow_state = allow_state
        self.allow_mutation = allow_mutation
        self.must_be_dataclass = must_be_dataclass


ROLE_RULES: dict[DomainRole, RoleRule] = {
    DomainRole.VALUE_OBJECT: RoleRule(
        allow_methods=False,
        allow_state=True,  # slots only
        allow_mutation=False,
        must_be_dataclass=True,
    ),
    DomainRole.EVENT: RoleRule(
        allow_methods=False,
        allow_state=True,
        allow_mutation=False,
        must_be_dataclass=True,
    ),
    DomainRole.POLICY: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
    DomainRole.SERVICE: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
    DomainRole.AGGREGATE: RoleRule(
        allow_methods=True,
        allow_state=False,  # state only via _AggregateState
        allow_mutation=True,
    ),
    DomainRole.ENTITY: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
    DomainRole.PROJECTION: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
    DomainRole.CURSOR: RoleRule(
        allow_methods=False,
        allow_state=True,
        allow_mutation=False,
        must_be_dataclass=True,
    ),
    DomainRole.FACTORY: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
}
