"""Vetted tool catalog — the stable ``id → capability`` layer a persona references."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import aisuite as ai

from .agents.base import AgentContext
from .engineering.managed_tools import managed_engineering_tools
from .engineering.tools import engineering_os_tools
from .risk import RiskClass
from .tools.files import file_tools
from .tools.git import git_tools
from .tools.search import search_tools
from .tools.shell import shell_tools
from .tools.todo import todo_tools

_REQUIREMENTS: dict[str, Callable[[AgentContext], bool]] = {
    "workspace": lambda c: c.workspace is not None,
    "executor": lambda c: c.executor is not None,
    "todo": lambda c: c.todo is not None,
}

@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    description: str
    build: Callable[[AgentContext], list]
    requires: tuple[str, ...] = ()
    risk: tuple[RiskClass, ...] = (RiskClass.READ,)
    def available(self, context: AgentContext) -> bool:
        return all(_REQUIREMENTS[r](context) for r in self.requires)

def _code_files(context: AgentContext) -> list:
    ws = str(context.workspace); replaced = {"search_files", "read_file", "read_file_lines"}
    files = [t for t in ai.toolkits.files(root=ws, allow_write=True) if getattr(t,"__name__","") not in replaced]
    return [*files, *file_tools(ws)]
def _files(context: AgentContext) -> list:
    ws=str(context.workspace); file_kwargs={"roots":context.roots} if context.roots else {"root":ws,"allow_write":True}
    return [t for t in ai.toolkits.files(**file_kwargs) if getattr(t,"__name__","")!="search_files"]
def _git(context: AgentContext) -> list: return [*ai.toolkits.git(root=str(context.workspace)), *git_tools(str(context.workspace))]
def _search(context: AgentContext) -> list: return search_tools(str(context.workspace))
def _shell(context: AgentContext) -> list: return shell_tools(context.executor)
def _todo(context: AgentContext) -> list: return todo_tools(context.todo)
def _engineering_os(_context: AgentContext) -> list:
    return [*engineering_os_tools(), *managed_engineering_tools()]

_CAPS: list[Capability] = [
    Capability("code_files","Code files","Read & edit files in a single repo workspace (line-numbered reads).",_code_files,("workspace",),(RiskClass.READ,RiskClass.WRITE_LOCAL)),
    Capability("files","Files","Read & edit files across the session's workspace folders.",_files,("workspace",),(RiskClass.READ,RiskClass.WRITE_LOCAL)),
    Capability("git","Git","Inspect git state and history (status, diff, log).",_git,("workspace",),(RiskClass.READ,)),
    Capability("search","Search","Fast code/content search (grep).",_search,("workspace",),(RiskClass.READ,)),
    Capability("shell","Shell","Run shell commands in a persistent session.",_shell,("executor",),(RiskClass.EXEC,)),
    Capability("todo","Task list","Maintain a visible task/progress list.",_todo,("todo",),(RiskClass.READ,)),
    Capability("engineering_os","Engineering control plane",
               "Inspect and govern AI-Engineering-OS Projects/Jobs/Reviews/Deliveries and run approved authoritative engineering flows.",
               _engineering_os,(),(RiskClass.READ,RiskClass.EXTERNAL)),
]
CATALOG: dict[str, Capability] = {c.id:c for c in _CAPS}
def capability(cap_id: str) -> Capability:
    cap=CATALOG.get(cap_id)
    if cap is None: raise KeyError(f"Unknown capability id: {cap_id!r}")
    return cap
def expand(ids: list[str], context: AgentContext) -> list:
    tools=[]
    for cap_id in ids:
        cap=capability(cap_id)
        if cap.available(context): tools.extend(cap.build(context))
    return tools
def risk_summary(ids: list[str]) -> set[RiskClass]:
    out=set()
    for cap_id in ids: out.update(capability(cap_id).risk)
    return out
