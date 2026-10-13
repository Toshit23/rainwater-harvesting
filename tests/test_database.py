"""
Unit tests for SQLite database persistence module.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from database.database import (
    initialize_database,
    generate_next_project_id,
    save_project,
    get_all_projects,
    get_project_by_id,
    delete_project,
    get_db_connection,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_project_data.db"
    initialize_database(db_file)
    return db_file


def test_initialize_database(temp_db):
    conn = get_db_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()

    assert "projects" in tables
    assert "project_inputs" in tables
    assert "project_results" in tables


def test_generate_next_project_id(temp_db):
    assert generate_next_project_id(temp_db) == "PRJ-001"


def test_save_and_get_project(temp_db, tmp_path):
    sample_img = tmp_path / "sample.jpg"
    sample_img.write_bytes(b"fake image bytes")

    inputs = {
        "runoff_coefficient": 0.85,
        "concrete_volume_m3": 120.0,
        "plaster_volume_m3": 60.0,
        "curing_duration_days": 14.0,
    }
    results = {
        "rooftop_percentage": 45.5,
        "rooftop_area_m2": 455.0,
        "rainfall_mm": 2200.0,
        "harvested_water_litres": 850850.0,
        "construction_water_demand_litres": 81600.0,
        "difference_litres": 769250.0,
        "status": "SURPLUS",
        "demand_breakdown": {
            "concrete_water_litres": 21600.0,
            "plaster_water_litres": 9600.0,
            "curing_water_litres": 50400.0,
        }
    }

    prj_id = save_project(
        project_name="Kalyan Construction Site",
        location="Kalyan, Maharashtra",
        site_area_m2=1000.0,
        inputs=inputs,
        results=results,
        source_image_path=str(sample_img),
        db_path=temp_db,
    )

    assert prj_id == "PRJ-001"

    # Next id should now be PRJ-002
    assert generate_next_project_id(temp_db) == "PRJ-002"

    # Fetch all
    all_projects = get_all_projects(temp_db)
    assert len(all_projects) == 1
    assert all_projects[0]["project_id"] == "PRJ-001"
    assert all_projects[0]["project_name"] == "Kalyan Construction Site"
    assert all_projects[0]["status"] == "SURPLUS"

    # Fetch by ID
    full_data = get_project_by_id(prj_id, temp_db)
    assert full_data is not None
    assert full_data["project"]["project_name"] == "Kalyan Construction Site"
    assert full_data["project"]["location"] == "Kalyan, Maharashtra"
    assert full_data["project"]["site_area_m2"] == 1000.0
    assert full_data["inputs"]["runoff_coefficient"] == 0.85
    assert full_data["inputs"]["concrete_volume_m3"] == 120.0
    assert full_data["results"]["harvestable_water_liters"] == 850850.0
    assert full_data["results"]["status"] == "SURPLUS"
    assert "SUFFICIENT" in full_data["results"]["conclusion"]


def test_delete_project_cascades(temp_db):
    inputs = {
        "runoff_coefficient": 0.8,
        "concrete_volume_m3": 50.0,
        "plaster_volume_m3": 25.0,
        "curing_duration_days": 7.0,
    }
    results = {
        "rooftop_percentage": 30.0,
        "rooftop_area_m2": 300.0,
        "rainfall_mm": 1500.0,
        "harvested_water_litres": 360000.0,
        "construction_water_demand_litres": 23500.0,
        "difference_litres": 336500.0,
        "status": "SURPLUS",
        "demand_breakdown": {
            "concrete_water_litres": 9000.0,
            "plaster_water_litres": 4000.0,
            "curing_water_litres": 10500.0,
        }
    }

    prj_1 = save_project("Site 1", "Mumbai", 1000.0, inputs, results, db_path=temp_db)
    prj_2 = save_project("Site 2", "Pune", 1500.0, inputs, results, db_path=temp_db)

    assert len(get_all_projects(temp_db)) == 2

    # Delete prj_1
    deleted = delete_project(prj_1, db_path=temp_db)
    assert deleted is True

    # prj_1 should be gone, prj_2 intact
    assert get_project_by_id(prj_1, db_path=temp_db) is None
    assert get_project_by_id(prj_2, db_path=temp_db) is not None

    # Check cascading in database tables
    conn = get_db_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS c FROM project_inputs WHERE project_id = ?;", (prj_1,))
    assert cursor.fetchone()["c"] == 0
    cursor.execute("SELECT COUNT(*) AS c FROM project_results WHERE project_id = ?;", (prj_1,))
    assert cursor.fetchone()["c"] == 0
    conn.close()

    assert len(get_all_projects(temp_db)) == 1
