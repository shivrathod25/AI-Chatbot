"""
Comprehensive Test Suite for Course Enrollment Chatbot
Validates XAMPP MySQL database CRUD operations and FastAPI integration endpoints.
"""

import sys
import os
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import queries
from main import app

client = TestClient(app)

def test_database_crud():
    print("\n==================================================")
    print("1. Testing XAMPP/MySQL Database Engine & CRUD")
    print("==================================================")

    # Health Check
    health = database.get_db_health()
    print(f"[1.1] DB Health Check: {health}")
    assert health["status"] == "healthy", "Database health check failed"
    assert health["engine"] == "MYSQL", f"Expected MYSQL engine, got {health['engine']}"
    assert health["database"] == "ai_chatbot", f"Expected database ai_chatbot, got {health['database']}"
    print("[OK] Active Engine: MYSQL (Database: ai_chatbot)")

    # CREATE
    test_email = f"suite.mysql.{int(time.time())}@example.com"
    test_enrollment_id = f"ENR-SUITE-{int(time.time())}"
    test_user = {
        "enrollment_id": test_enrollment_id,
        "full_name": "Suite Test Student",
        "email": test_email,
        "phone": "9876543210",
        "education": "B.Tech Computer Science",
        "course": "Full Stack Python Development",
        "registered_at": "2026-09-19 16:00:00",
        "payment_status": "PENDING"
    }

    queries.save_user(test_user)
    print(f"[1.2] CREATE -> Saved user: {test_email}")

    # READ BY EMAIL
    user_by_email = queries.get_user_by_email(test_email)
    assert user_by_email is not None and user_by_email["enrollment_id"] == test_enrollment_id
    print(f"[1.3] READ BY EMAIL -> [OK]")

    # READ BY ID
    user_by_id = queries.get_user_by_enrollment_id(test_enrollment_id)
    assert user_by_id is not None and user_by_id["email"] == test_email
    print(f"[1.4] READ BY ID -> [OK]")

    # READ ALL
    all_users = queries.get_all_enrollments(100)
    matching = [u for u in all_users if u["enrollment_id"] == test_enrollment_id]
    assert len(matching) == 1
    print(f"[1.5] READ ALL -> Total MySQL records: {len(all_users)} [OK]")

    # UPDATE PAYMENT STATUS
    queries.update_payment_status(test_enrollment_id, "SUCCESS", "pay_suite_stripe_999")
    updated_user = queries.get_user_by_enrollment_id(test_enrollment_id)
    assert updated_user["payment_status"] == "SUCCESS"
    print(f"[1.6] UPDATE STATUS -> [OK]")

    # UPDATE USER DETAILS
    update_res = queries.update_user_details(test_enrollment_id, {
        "full_name": "Suite Test Student Updated",
        "course": "AI & ML Masterclass"
    })
    assert update_res is True
    print(f"[1.7] UPDATE DETAILS -> [OK]")

    # DELETE
    deleted = queries.delete_user_by_enrollment_id(test_enrollment_id)
    assert deleted is True
    assert queries.get_user_by_enrollment_id(test_enrollment_id) is None
    print(f"[1.8] DELETE -> Record {test_enrollment_id} removed [OK]")


def test_api_endpoints():
    print("\n==================================================")
    print("2. Testing FastAPI HTTP Endpoints Integration")
    print("==================================================")

    # Root & Config
    r_root = client.get("/")
    assert r_root.status_code == 200
    print("[2.1] GET / -> 200 OK")

    r_config = client.get("/api/config")
    assert r_config.status_code == 200 and "stripe_publishable_key" in r_config.json()
    print("[2.2] GET /api/config -> Publishable key verified")

    r_health = client.get("/api/health")
    assert r_health.status_code == 200 and r_health.json()["engine"] == "MYSQL"
    print(f"[2.3] GET /api/health -> Engine: MYSQL")

    # POST /api/register
    test_email = f"api.suite.{int(time.time())}@gmail.com"
    payload = {
        "full_name": "API Suite Student",
        "email": test_email,
        "phone": "9876543210",
        "education": "B.Sc Computer Science",
        "course": "Full Stack Web Development"
    }

    r_reg = client.post("/api/register", json=payload)
    assert r_reg.status_code == 200
    enrollment_id = r_reg.json()["enrollment_id"]
    print(f"[2.4] POST /api/register -> Enrollment ID: {enrollment_id}")

    # Duplicate check
    assert client.post("/api/register", json=payload).status_code == 400
    print("[2.5] Duplicate Registration -> 400 Bad Request [OK]")

    # GET /api/enrollment/{enrollment_id}
    r_get = client.get(f"/api/enrollment/{enrollment_id}")
    assert r_get.status_code == 200 and r_get.json()["enrollment"]["email"] == test_email
    print(f"[2.6] GET /api/enrollment/{enrollment_id} -> [OK]")

    # GET /api/enrollments
    assert client.get("/api/enrollments").status_code == 200
    print("[2.7] GET /api/enrollments -> [OK]")

    # PUT update
    update_payload = {"full_name": "API Suite Student Updated", "course": "Data Science & AI"}
    assert client.put(f"/api/enrollment/{enrollment_id}", json=update_payload).status_code == 200
    print(f"[2.8] PUT /api/enrollment/{enrollment_id} -> [OK]")

    # PATCH status
    status_payload = {"payment_status": "SUCCESS", "payment_id": "ch_suite_test_888"}
    assert client.patch(f"/api/enrollment/{enrollment_id}/status", json=status_payload).status_code == 200
    print(f"[2.9] PATCH /api/enrollment/{enrollment_id}/status -> [OK]")

    # POST create-payment
    pay_payload = {"email": test_email, "course": "Data Science & AI", "enrollment_id": enrollment_id}
    r_pay = client.post("/api/create-payment", json=pay_payload)
    assert r_pay.status_code == 200 and "checkout_url" in r_pay.json()
    print("[2.10] POST /api/create-payment -> Generated Stripe Link [OK]")

    # DELETE
    assert client.delete(f"/api/enrollment/{enrollment_id}").status_code == 200
    assert client.get(f"/api/enrollment/{enrollment_id}").status_code == 404
    print(f"[2.11] DELETE /api/enrollment/{enrollment_id} -> 404 Verified Post-Delete [OK]")


if __name__ == "__main__":
    print("Starting Comprehensive Project Test Suite...")
    test_database_crud()
    test_api_endpoints()
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")
    print("==================================================")
