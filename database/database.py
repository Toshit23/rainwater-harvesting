"""
database.py - SQLite Relational Persistence for Rainwater Harvesting & Construction Water Estimator.

Manages:
- Database initialization and table creation
- Project ID auto-generation (PRJ-001, PRJ-002, ...)
- Saving project metadata, input parameters, and calculation results
- Project retrieval, listing, viewing, and cascading deletion
"""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


# Default database path relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "project_data.db"
SAVED_PROJECTS_DIR = BASE_DIR / "saved_projects"


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Establish and return a connection to the SQLite database with Foreign Keys enabled."""
    target_path = Path(db_path) if db_path else DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path: Optional[Path] = None) -> None:
    """Create tables if they do not exist with proper foreign-key relationships."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                location TEXT NOT NULL,
                site_area_m2 REAL NOT NULL,
                image_filename TEXT,
                created_at TEXT NOT NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS project_inputs (
                input_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                runoff_coefficient REAL NOT NULL,
                concrete_volume_m3 REAL NOT NULL,
                plaster_volume_m3 REAL NOT NULL,
                curing_duration_days REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS project_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                rooftop_percentage REAL NOT NULL,
                rooftop_area_m2 REAL NOT NULL,
                rainfall_mm REAL NOT NULL,
                harvestable_water_liters REAL NOT NULL,
                concrete_water_liters REAL NOT NULL,
                plaster_water_liters REAL NOT NULL,
                curing_water_liters REAL NOT NULL,
                total_construction_demand_liters REAL NOT NULL,
                net_water_balance_liters REAL NOT NULL,
                status TEXT NOT NULL,
                conclusion TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            """)
    finally:
        conn.close()


def generate_next_project_id(db_path: Optional[Path] = None) -> str:
    """Generate human-friendly project ID: PRJ-001, PRJ-002, etc."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT project_id FROM projects ORDER BY rowid DESC LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            return "PRJ-001"
        last_id = row["project_id"]
        if last_id.startswith("PRJ-"):
            try:
                num = int(last_id.split("-")[1])
                return f"PRJ-{num + 1:03d}"
            except (IndexError, ValueError):
                pass
        cursor.execute("SELECT COUNT(*) AS count FROM projects;")
        count = cursor.fetchone()["count"]
        return f"PRJ-{count + 1:03d}"
    finally:
        conn.close()


def save_project(
    project_name: str,
    location: str,
    site_area_m2: float,
    inputs: Dict[str, Any],
    results: Dict[str, Any],
    source_image_path: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> str:
    """Save full project (metadata, inputs, and results) in a single transaction.

    Copies image to saved_projects/<project_id>/ if provided.
    Returns the generated project_id.
    """
    initialize_database(db_path)
    project_id = generate_next_project_id(db_path)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Handle image persistence
    saved_filename = ""
    if source_image_path and os.path.isfile(source_image_path):
        try:
            proj_dir = SAVED_PROJECTS_DIR / project_id
            proj_dir.mkdir(parents=True, exist_ok=True)
            ext = Path(source_image_path).suffix or ".jpg"
            dest_file = proj_dir / f"input_image{ext}"
            shutil.copy2(source_image_path, str(dest_file))
            saved_filename = f"saved_projects/{project_id}/input_image{ext}"
        except Exception:
            saved_filename = os.path.basename(source_image_path)

    # Derive conclusion text from status
    status = results.get("status", "BALANCED")
    if status == "SURPLUS":
        conclusion = "Harvested rainwater is SUFFICIENT to fulfill site construction needs."
    elif status == "SHORTFALL":
        conclusion = "Additional external water source required to cover deficit."
    else:
        conclusion = "Supply and demand are exactly balanced."

    demand = results.get("demand_breakdown", {})

    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Insert into projects
            conn.execute(
                """
                INSERT INTO projects (project_id, project_name, location, site_area_m2, image_filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    project_id,
                    project_name.strip() or f"Project {project_id}",
                    location.strip(),
                    float(site_area_m2),
                    saved_filename,
                    created_at,
                ),
            )

            # 2. Insert into project_inputs
            conn.execute(
                """
                INSERT INTO project_inputs (project_id, runoff_coefficient, concrete_volume_m3, plaster_volume_m3, curing_duration_days)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    project_id,
                    float(inputs.get("runoff_coefficient", 0.8)),
                    float(inputs.get("concrete_volume_m3", 0.0)),
                    float(inputs.get("plaster_volume_m3", 0.0)),
                    float(inputs.get("curing_duration_days", 0.0)),
                ),
            )

            # 3. Insert into project_results
            conn.execute(
                """
                INSERT INTO project_results (
                    project_id, rooftop_percentage, rooftop_area_m2, rainfall_mm,
                    harvestable_water_liters, concrete_water_liters, plaster_water_liters,
                    curing_water_liters, total_construction_demand_liters, net_water_balance_liters,
                    status, conclusion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    project_id,
                    float(results.get("rooftop_percentage", 0.0)),
                    float(results.get("rooftop_area_m2", 0.0)),
                    float(results.get("rainfall_mm", 0.0)),
                    float(results.get("harvested_water_litres", 0.0)),
                    float(demand.get("concrete_water_litres", 0.0)),
                    float(demand.get("plaster_water_litres", 0.0)),
                    float(demand.get("curing_water_litres", 0.0)),
                    float(results.get("construction_water_demand_litres", 0.0)),
                    float(results.get("difference_litres", 0.0)),
                    status,
                    conclusion,
                ),
            )
        return project_id
    finally:
        conn.close()


def get_all_projects(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return all projects sorted by created_at DESC."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.project_id, p.project_name, p.location, p.site_area_m2, p.created_at,
                   r.status, r.harvestable_water_liters, r.total_construction_demand_liters,
                   r.net_water_balance_liters
            FROM projects p
            LEFT JOIN project_results r ON p.project_id = r.project_id
            ORDER BY p.created_at DESC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_project_by_id(project_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full project details: project metadata, inputs, and results."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        # Fetch project
        cursor.execute("SELECT * FROM projects WHERE project_id = ?;", (project_id,))
        proj_row = cursor.fetchone()
        if not proj_row:
            return None

        # Fetch inputs
        cursor.execute("SELECT * FROM project_inputs WHERE project_id = ?;", (project_id,))
        input_row = cursor.fetchone()

        # Fetch results
        cursor.execute("SELECT * FROM project_results WHERE project_id = ?;", (project_id,))
        res_row = cursor.fetchone()

        return {
            "project": dict(proj_row),
            "inputs": dict(input_row) if input_row else {},
            "results": dict(res_row) if res_row else {},
        }
    finally:
        conn.close()


def delete_project(project_id: str, db_path: Optional[Path] = None) -> bool:
    """Delete a project and its cascaded inputs and results. Also removes its image folder if any."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE project_id = ?;", (project_id,))
            deleted = cursor.rowcount > 0

        # Remove disk directory if exists
        proj_dir = SAVED_PROJECTS_DIR / project_id
        if proj_dir.exists():
            shutil.rmtree(str(proj_dir), ignore_errors=True)

        return deleted
    finally:
        conn.close()
