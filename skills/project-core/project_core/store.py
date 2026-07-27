"""Compatibility facade for project-core stores.

Store implementations live in domain modules. Existing callers can continue
importing classes and default factories from :mod:`project_core.store`.
"""

from __future__ import annotations

from .config import db_path
from .store_base import row_to_dict
from .store_collaboration import PeopleStore, RetrospectiveStore
from .store_governance import DecisionStore, RiskStore
from .store_work import MilestoneStore, ProjectStore, TaskStore

__all__ = [
  "DecisionStore",
  "MilestoneStore",
  "PeopleStore",
  "ProjectStore",
  "RetrospectiveStore",
  "RiskStore",
  "TaskStore",
  "default_decision_store",
  "default_milestone_store",
  "default_people_store",
  "default_project_store",
  "default_retrospective_store",
  "default_risk_store",
  "default_task_store",
  "row_to_dict",
]


def default_project_store() -> ProjectStore:
  return ProjectStore(db_path())


def default_task_store() -> TaskStore:
  return TaskStore(db_path())


def default_milestone_store() -> MilestoneStore:
  return MilestoneStore(db_path())


def default_risk_store() -> RiskStore:
  return RiskStore(db_path())


def default_decision_store() -> DecisionStore:
  return DecisionStore(db_path())


def default_people_store() -> PeopleStore:
  return PeopleStore(db_path())


def default_retrospective_store() -> RetrospectiveStore:
  return RetrospectiveStore(db_path())
