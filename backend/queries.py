"""
Course Enrollment Chatbot - SQL Data Access & Query Engine
queries.py

Executes SQL queries against XAMPP MySQL database 'ai_chatbot'.
Uses Python-to-SQL connection provided strictly by database.py.
"""

import logging
from database import get_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("queries")


def save_user(user: dict):
    """
    Insert a new enrollment record into XAMPP MySQL database.
    """
    conn = get_connection()
    cursor = conn.cursor()

    user.setdefault("payment_id", None)
    user.setdefault("payment_status", "PENDING")

    insert_query = """
    INSERT INTO enrollments
    (enrollment_id, full_name, email, phone, education, course, registered_at, payment_status, payment_id)
    VALUES
    (%(enrollment_id)s, %(full_name)s, %(email)s, %(phone)s,
     %(education)s, %(course)s, %(registered_at)s, %(payment_status)s, %(payment_id)s)
    """
    cursor.execute(insert_query, user)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Saved user {user['email']} with Enrollment ID: {user['enrollment_id']}")


def get_user_by_email(email: str):
    """
    Fetch enrollment record by user email.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM enrollments WHERE email = %s ORDER BY id DESC LIMIT 1"
    cursor.execute(query, (email.strip().lower(),))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_user_by_enrollment_id(enrollment_id: str):
    """
    Fetch enrollment record by Enrollment ID.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM enrollments WHERE enrollment_id = %s"
    cursor.execute(query, (enrollment_id.strip().upper(),))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def update_payment_status(enrollment_id: str, status: str, payment_id: str = None):
    """
    Update payment status and transaction ID for an enrollment.
    """
    conn = get_connection()
    cursor = conn.cursor()
    update_query = """
    UPDATE enrollments
    SET payment_status = %s, payment_id = COALESCE(%s, payment_id)
    WHERE enrollment_id = %s
    """
    cursor.execute(update_query, (status, payment_id, enrollment_id))
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Updated payment status for {enrollment_id} to '{status}' (Payment ID: {payment_id})")


def get_all_enrollments(limit: int = 100):
    """
    Fetch all enrollment records up to specified limit.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM enrollments ORDER BY id DESC LIMIT %s"
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def update_user_details(enrollment_id: str, details: dict):
    """
    Update details (full_name, phone, education, course) for an enrollment record.
    """
    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    params = []
    for key in ['full_name', 'phone', 'education', 'course']:
        if key in details and details[key] is not None:
            fields.append(f"{key} = %s")
            params.append(details[key])

    if not fields:
        cursor.close()
        conn.close()
        return False

    params.append(enrollment_id.strip().upper())
    set_clause = ", ".join(fields)
    query = f"UPDATE enrollments SET {set_clause} WHERE enrollment_id = %s"

    cursor.execute(query, tuple(params))
    updated = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    if updated:
        logger.info(f"Updated enrollment record: {enrollment_id}")
    return updated


def delete_user_by_enrollment_id(enrollment_id: str):
    """
    Delete enrollment record by Enrollment ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    delete_query = "DELETE FROM enrollments WHERE enrollment_id = %s"
    cursor.execute(delete_query, (enrollment_id.strip().upper(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    if deleted:
        logger.info(f"Deleted enrollment record: {enrollment_id}")
    else:
        logger.warning(f"No enrollment record found to delete for ID: {enrollment_id}")
    return deleted
