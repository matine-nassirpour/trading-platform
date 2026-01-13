from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole


class RoleRule:
    def __init__(
        self,
        *,
        allow_methods: bool,
        allow_state: bool,
        allow_mutation: bool,
        must_be_dataclass: bool = False,
        must_use_slots: bool = False,
        forbid_dict: bool = False,
    ):
        self.allow_methods = allow_methods
        self.allow_state = allow_state
        self.allow_mutation = allow_mutation
        self.must_be_dataclass = must_be_dataclass
        self.must_use_slots = must_use_slots
        self.forbid_dict = forbid_dict


ROLE_RULES: dict[DomainRole, RoleRule] = {
    DomainRole.VALUE_OBJECT: RoleRule(
        allow_methods=False,
        allow_state=True,  # slots only
        allow_mutation=False,
        must_be_dataclass=True,
        must_use_slots=True,
        forbid_dict=True,
    ),
    DomainRole.EVENT: RoleRule(
        allow_methods=False,
        allow_state=True,
        allow_mutation=False,
        must_be_dataclass=True,
        must_use_slots=True,
        forbid_dict=True,
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
        must_use_slots=True,
        forbid_dict=True,
    ),
    DomainRole.FACTORY: RoleRule(
        allow_methods=True,
        allow_state=False,
        allow_mutation=False,
    ),
}
