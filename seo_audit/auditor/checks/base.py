from typing import Dict, Callable

from ..models import RuleResult, Severity, Weight, Category


class BaseCheck:
    category: Category = None

    @classmethod
    def get_checks(cls) -> Dict[str, Callable]:
        checks = {}
        for attr_name in dir(cls):
            if attr_name.startswith("check_"):
                checks[attr_name] = getattr(cls, attr_name)
        return checks
