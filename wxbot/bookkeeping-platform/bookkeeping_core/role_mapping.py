from __future__ import annotations


_GROUP_NUM_ROLE_MAP = {
    1: "internal",
    2: "vendor",
    3: "vendor",
    4: "vendor",
    5: "customer",
    6: "customer",
    7: "customer",
    8: "customer",
}

_ROLE_ALIASES = {
    "customer": "customer",
    "guest": "customer",
    "客户": "customer",
    "客人": "customer",
    "vendor": "vendor",
    "supplier": "vendor",
    "供应商": "vendor",
    "internal": "internal",
    "inside": "internal",
    "内部": "internal",
    "unassigned": "unassigned",
    "unknown": "unassigned",
    "未归属": "unassigned",
    "待处理": "unassigned",
}


def list_group_num_role_rules() -> list[dict]:
    role_order = ("internal", "vendor", "customer")
    grouped_nums: dict[str, list[int]] = {}
    for group_num, role in _GROUP_NUM_ROLE_MAP.items():
        grouped_nums.setdefault(role, []).append(int(group_num))
    return [
        {
            "business_role": role,
            "group_nums": grouped_nums[role],
        }
        for role in role_order
        if grouped_nums.get(role)
    ]


def list_role_alias_rules() -> list[dict]:
    role_order = ("customer", "vendor", "internal", "unassigned")
    grouped_aliases: dict[str, list[str]] = {}
    for alias, role in _ROLE_ALIASES.items():
        grouped_aliases.setdefault(role, [])
        if alias not in grouped_aliases[role]:
            grouped_aliases[role].append(alias)
    return [
        {
            "business_role": role,
            "aliases": grouped_aliases[role],
        }
        for role in role_order
        if grouped_aliases.get(role)
    ]


def normalize_business_role(value) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return _ROLE_ALIASES.get(text.lower(), _ROLE_ALIASES.get(text))


def default_business_role_for_group_num(group_num: int | None) -> str | None:
    if group_num is None:
        return None
    return _GROUP_NUM_ROLE_MAP.get(int(group_num))


def resolve_business_role(*, business_role, group_num: int | None) -> str | None:
    normalized = normalize_business_role(business_role)
    if normalized is not None:
        return normalized
    return default_business_role_for_group_num(group_num)


def resolve_role_source(*, business_role, group_num: int | None) -> str:
    if normalize_business_role(business_role) is not None:
        return "manual"
    if default_business_role_for_group_num(group_num) is not None:
        return "group_num"
    return "unassigned"


def is_financial_role(role: str | None) -> bool:
    return role in {"customer", "vendor"}


def is_unassigned_role(role: str | None) -> bool:
    return role in {None, "unassigned"}
