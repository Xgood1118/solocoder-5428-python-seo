import re
from urllib.parse import urlparse, urljoin
from typing import List, Optional


class RobotsTxtParser:
    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent
        self._rules: dict = {}
        self._sitemaps: List[str] = []
        self._loaded = False

    def parse(self, content: str):
        current_agents = []
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "user-agent":
                if current_agents and ("disallow" in self._rules.get(current_agents[0], {}) or
                                       "allow" in self._rules.get(current_agents[0], {})):
                    pass
                current_agents.append(value.lower())
                for agent in current_agents:
                    if agent not in self._rules:
                        self._rules[agent] = {"disallow": [], "allow": []}
            elif key == "disallow":
                for agent in current_agents:
                    if agent not in self._rules:
                        self._rules[agent] = {"disallow": [], "allow": []}
                    self._rules[agent]["disallow"].append(value)
            elif key == "allow":
                for agent in current_agents:
                    if agent not in self._rules:
                        self._rules[agent] = {"disallow": [], "allow": []}
                    self._rules[agent]["allow"].append(value)
            elif key == "sitemap":
                self._sitemaps.append(value)
        self._loaded = True

    def is_allowed(self, url: str, user_agent: Optional[str] = None) -> bool:
        if not self._loaded:
            return True
        ua = (user_agent or self.user_agent).lower()
        parsed = urlparse(url)
        path = parsed.path or "/"
        if ua in self._rules:
            rules = self._rules[ua]
        elif "*" in self._rules:
            rules = self._rules["*"]
        else:
            return True
        for allow_path in rules.get("allow", []):
            if self._match_path(allow_path, path):
                return True
        for disallow_path in rules.get("disallow", []):
            if self._match_path(disallow_path, path):
                return False
        return True

    def _match_path(self, pattern: str, path: str) -> bool:
        if not pattern:
            return False
        if pattern == "/":
            return True
        pattern = pattern.replace(".", r"\.")
        pattern = pattern.replace("*", ".*")
        pattern = pattern.replace("?", r"\?")
        if pattern.endswith("/"):
            pattern = pattern + ".*"
        try:
            return bool(re.match("^" + pattern, path))
        except re.error:
            return False

    @property
    def sitemaps(self) -> List[str]:
        return self._sitemaps

    @property
    def is_loaded(self) -> bool:
        return self._loaded
