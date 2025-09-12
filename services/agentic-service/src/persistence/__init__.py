"""Persistence package for saving generated course artifacts to Postgres.

Exports helper to persist a generated State into the relational schema
defined across microservices (course, lesson, tests, final tests).
"""

from .course_persistence import save_course_state, init_database  # noqa: F401
