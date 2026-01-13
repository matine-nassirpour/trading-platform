from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole


class RoleRule:
    def __init__(
        self,
        *,
        allow_state: bool,
        allow_mutation: bool,
        allow_public_domain_methods: bool,
        must_be_dataclass: bool = False,
        must_use_slots: bool = False,
        forbid_dict: bool = False,
    ):
        self.allow_state = allow_state
        self.allow_mutation = allow_mutation
        self.allow_public_domain_methods = allow_public_domain_methods
        self.must_be_dataclass = must_be_dataclass
        self.must_use_slots = must_use_slots
        self.forbid_dict = forbid_dict


ROLE_RULES: dict[DomainRole, RoleRule] = {
    DomainRole.VALUE_OBJECT: RoleRule(
        allow_state=True,
        allow_mutation=False,
        allow_public_domain_methods=False,
        must_be_dataclass=True,
        must_use_slots=True,
        forbid_dict=True,
    ),
    DomainRole.EVENT: RoleRule(
        allow_state=True,
        allow_mutation=False,
        allow_public_domain_methods=False,
        must_be_dataclass=True,
        must_use_slots=True,
        forbid_dict=True,
    ),
    DomainRole.CURSOR: RoleRule(
        allow_state=True,
        allow_mutation=False,
        allow_public_domain_methods=False,
        must_be_dataclass=True,
        must_use_slots=True,
        forbid_dict=True,
    ),
    DomainRole.POLICY: RoleRule(
        allow_state=False,
        allow_mutation=False,
        allow_public_domain_methods=True,
    ),
    DomainRole.SERVICE: RoleRule(
        allow_state=False,
        allow_mutation=False,
        allow_public_domain_methods=True,
    ),
    DomainRole.AGGREGATE: RoleRule(
        allow_state=False,
        allow_mutation=True,
        allow_public_domain_methods=True,
    ),
    DomainRole.ENTITY: RoleRule(
        allow_state=False,
        allow_mutation=False,
        allow_public_domain_methods=True,
    ),
    DomainRole.PROJECTION: RoleRule(
        allow_state=False,
        allow_mutation=False,
        allow_public_domain_methods=True,
    ),
    DomainRole.FACTORY: RoleRule(
        allow_state=False,
        allow_mutation=False,
        allow_public_domain_methods=True,
    ),
}
