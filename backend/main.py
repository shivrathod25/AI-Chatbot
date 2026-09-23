"""
Course Enrollment Chatbot - FastAPI Backend
main.py
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import stripe
import os
import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from database import get_db_health
from queries import (
    save_user,
    get_user_by_email,
    get_user_by_enrollment_id,
    get_all_enrollments,
    update_user_details,
    update_payment_status,
    delete_user_by_enrollment_id
)

# Load environment variables from backend/.env regardless of CWD
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# ══════════════════════════════════════════════════════════════════
# ── Stripe Configuration ──────────────────────────────────────────
# Set your Stripe test keys in backend/.env:
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY",      "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET",  "")
# ══════════════════════════════════════════════════════════════════

# ── Init Stripe ───────────────────────────────────────────────────
stripe.api_key = STRIPE_SECRET_KEY

app = FastAPI(title="Course Enrollment API", version="1.0.0")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class RegistrationData(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    education: str
    course: str

    # Validate Full Name
    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()

        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")

        if not re.match(r"^[A-Za-z ]+$", v):
            raise ValueError("Name should contain only letters")

        return v

    # Validate Phone Number
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):

        if not re.match(r"^[6-9][0-9]{9}$", v):
            raise ValueError(
                "Phone must be 10 digits and start with 6,7,8,9"
            )

        return v


class PaymentRequest(BaseModel):
    email: EmailStr
    course: str
    enrollment_id: str


class UpdateRegistrationData(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    education: str | None = None
    course: str | None = None


class StatusUpdateRequest(BaseModel):
    payment_status: str
    payment_id: str | None = None


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Course Enrollment API is running ✅"}


@app.get("/api/health")
def db_health_check():
    """
    Check database connection and system status
    """
    return get_db_health()


@app.get("/api/enrollments")
def list_enrollments(limit: int = 100):
    """
    Retrieve all course enrollment records
    """
    return {
        "success": True,
        "enrollments": get_all_enrollments(limit)
    }


@app.get("/api/enrollment/{enrollment_id}")
def get_enrollment(enrollment_id: str):
    """
    Retrieve a specific enrollment record by ID
    """
    record = get_user_by_enrollment_id(enrollment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
    return {
        "success": True,
        "enrollment": record
    }


@app.put("/api/enrollment/{enrollment_id}")
def update_enrollment(enrollment_id: str, data: UpdateRegistrationData):
    """
    Update student enrollment details
    """
    existing = get_user_by_enrollment_id(enrollment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    updated = update_user_details(enrollment_id, data.dict(exclude_unset=True))
    if updated:
        return {
            "success": True,
            "message": f"Enrollment {enrollment_id} updated successfully",
            "enrollment": get_user_by_enrollment_id(enrollment_id)
        }
    raise HTTPException(status_code=400, detail="No fields updated")


@app.patch("/api/enrollment/{enrollment_id}/status")
def patch_payment_status(enrollment_id: str, data: StatusUpdateRequest):
    """
    Update payment status for an enrollment
    """
    existing = get_user_by_enrollment_id(enrollment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    update_payment_status(enrollment_id, data.payment_status, data.payment_id)
    return {
        "success": True,
        "message": f"Payment status for {enrollment_id} updated to {data.payment_status}",
        "enrollment": get_user_by_enrollment_id(enrollment_id)
    }


@app.delete("/api/enrollment/{enrollment_id}")
def delete_enrollment(enrollment_id: str):
    """
    Delete an enrollment record from the database
    """
    existing = get_user_by_enrollment_id(enrollment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Enrollment record not found")

    deleted = delete_user_by_enrollment_id(enrollment_id)
    if deleted:
        return {
            "success": True,
            "message": f"Enrollment record {enrollment_id} deleted successfully"
        }
    raise HTTPException(status_code=500, detail="Failed to delete enrollment record")


@app.get("/api/config")
def get_config():
    """
    Return Stripe publishable key to frontend
    """
    return {
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY
    }


@app.post("/api/register")
def register_student(data: RegistrationData):
    """
    Save student registration details to MySQL database
    """

    try:

        # Check if email already exists
        existing_user = get_user_by_email(data.email)

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        enrollment_id = "ENR-" + str(uuid.uuid4()).upper()[:12]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user = {
            "enrollment_id": enrollment_id,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "education": data.education,
            "course": data.course,
            "registered_at": timestamp,
            "payment_status": "PENDING"
        }

        save_user(user)

        return {
            "success": True,
            "enrollment_id": enrollment_id,
            "message": "Registration saved successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-payment")
def create_payment_link(data: PaymentRequest):
    """
    Create Stripe Checkout Session — visible in Stripe Dashboard under Payments
    """

    try:

        session = stripe.checkout.Session.create(

            payment_method_types=["card"],

            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "product_data": {
                        "name": data.course,
                        "description": f"Course Enrollment - {data.email}"
                    },
                    "unit_amount": 5000000   # Rs.50,000 in paise
                },
                "quantity": 1,
            }],

            mode="payment",

            customer_email=data.email,

            success_url=f"http://localhost:5500/success.html?enrollment={data.enrollment_id}",

            cancel_url="http://localhost:5500/cancel.html",

            metadata={
                "enrollment_id": data.enrollment_id,
                "course": data.course
            }
        )

        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.id
        }

    except stripe.error.StripeError as e:

        raise HTTPException(
            status_code=400,
            detail=f"Stripe Error: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()

    sig_header = request.headers.get("stripe-signature")

    try:

        # If webhook secret is set, verify signature; otherwise parse raw JSON
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                STRIPE_WEBHOOK_SECRET
            )
        else:
            event = json.loads(payload)

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        enrollment_id = session["metadata"]["enrollment_id"]

        print(f"✅ Payment confirmed for enrollment: {enrollment_id}")

    return {"status": "ok"}


# ─────────────────────────────────────────────
# RUN SERVER
# ─────────────────────────────────────────────

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
