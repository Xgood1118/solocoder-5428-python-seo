import json
import os
import time
from typing import Dict, List, Optional
from .models import Rule, Category, Severity, Weight


class RuleLoader:
    def __init__(self, rules_dir: str = None):
        if rules_dir is None:
            rules_dir = os.path.join(os.path.dirname(__file__), "rules")
        self.rules_dir = rules_dir
        self._rules: Dict[str, Rule] = {}
        self._last_load_time: float = 0
        self._file_mtimes: Dict[str, float] = {}

    def load_rules(self) -> Dict[str, Rule]:
        self._rules.clear()
        self._file_mtimes.clear()
        if not os.path.isdir(self.rules_dir):
            return self._rules
        for filename in os.listdir(self.rules_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.rules_dir, filename)
            self._load_file(filepath)
        self._last_load_time = time.time()
        return self._rules

    def reload_if_changed(self) -> bool:
        if not os.path.isdir(self.rules_dir):
            return False
        changed = False
        for filename in os.listdir(self.rules_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.rules_dir, filename)
            mtime = os.path.getmtime(filepath)
            if filepath not in self._file_mtimes or self._file_mtimes[filepath] != mtime:
                changed = True
                break
        if changed:
            self.load_rules()
        return changed

    def _load_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules_data = data if isinstance(data, list) else data.get("rules", [])
            for rule_data in rules_data:
                rule = Rule(
                    id=rule_data["id"],
                    name=rule_data["name"],
                    category=Category(rule_data["category"]),
                    severity=Severity(rule_data["severity"]),
                    weight=Weight(rule_data["weight"]),
                    description=rule_data.get("description", ""),
                    fix_advice=rule_data.get("fix_advice", ""),
                    check_function=rule_data.get("check_function", rule_data["id"]),
                    enabled=rule_data.get("enabled", True),
                )
                self._rules[rule.id] = rule
            self._file_mtimes[filepath] = os.path.getmtime(filepath)
        except Exception:
            pass

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        return list(self._rules.values())

    def get_rules_by_category(self, category: Category) -> List[Rule]:
        return [r for r in self._rules.values() if r.category == category and r.enabled]

    @property
    def rules_count(self) -> int:
        return len(self._rules)

    @property
    def last_load_time(self) -> float:
        return self._last_load_time
