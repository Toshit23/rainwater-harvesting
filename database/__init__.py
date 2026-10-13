"""
database package - SQLite Persistence for Rainwater Harvesting & Construction Water Estimator.
"""

from .database import (
    initialize_database,
    generate_next_project_id,
    save_project,
    get_all_projects,
    get_project_by_id,
    delete_project,
    get_db_connection,
    DB_PATH,
    SAVED_PROJECTS_DIR,
)

__all__ = [
    "initialize_database",
    "generate_next_project_id",
    "save_project",
    "get_all_projects",
    "get_project_by_id",
    "delete_project",
    "get_db_connection",
    "DB_PATH",
    "SAVED_PROJECTS_DIR",
]
