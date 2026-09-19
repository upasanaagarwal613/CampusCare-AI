from datetime import datetime, timezone
import json
from database.db import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'student', 'provider', 'admin'
    phone = db.Column(db.String(30), nullable=True)
    google_id = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    college_name = db.Column(db.String(120), default="IIT Delhi Main Campus")
    id_verified = db.Column(db.Boolean, default=True)
    live_lat = db.Column(db.Float, nullable=True)
    live_lng = db.Column(db.Float, nullable=True)
    designation = db.Column(db.String(120), nullable=True)  # For admin/faculty (e.g. Director of Facilities, Dean, Warden)
    staff_id_number = db.Column(db.String(60), nullable=True)  # Teacher / Staff / Student ID card number
    id_card_url = db.Column(db.String(255), nullable=True)  # Proof image of ID card
    department = db.Column(db.String(100), nullable=True)
    otp_code = db.Column(db.String(10), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    complaints = db.relationship("Complaint", backref="student", lazy="dynamic", foreign_keys="Complaint.student_id")
    provider_profile = db.relationship("Provider", backref="user", uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        complaints_count = self.complaints.count() if self.role == "student" else 0
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "college_name": self.college_name or "IIT Delhi Main Campus",
            "id_verified": self.id_verified if self.id_verified is not None else True,
            "live_lat": self.live_lat,
            "live_lng": self.live_lng,
            "designation": self.designation or ("Director of Facilities" if self.role == "admin" else None),
            "staff_id_number": self.staff_id_number,
            "id_card_url": self.id_card_url,
            "department": self.department,
            "total_complaints_filed": complaints_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "provider_id": self.provider_profile.id if self.provider_profile else None,
        }


class Provider(db.Model):
    __tablename__ = "providers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    service_category = db.Column(db.String(60), nullable=False)  # e.g., 'Electrical', 'Plumbing', 'HVAC', etc.
    skills = db.Column(db.Text, nullable=True)  # JSON or comma-separated
    rating = db.Column(db.Float, default=5.0)
    total_jobs_completed = db.Column(db.Integer, default=0)
    active_jobs_count = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    location_zone = db.Column(db.String(60), nullable=True)  # e.g., 'North Campus', 'Hostel Zone', 'Central'
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)

    # Relationships
    jobs = db.relationship("Job", backref="provider", lazy="dynamic")

    def get_specialties_list(self):
        if not self.service_category:
            return []
        return [s.strip() for s in self.service_category.split(",") if s.strip()]

    def has_specialty(self, category_name):
        if not category_name:
            return False
        specs = [s.lower() for s in self.get_specialties_list()]
        cat_lower = category_name.lower().strip()
        return any(s in cat_lower or cat_lower in s for s in specs)

    def get_skills_list(self):
        if not self.skills:
            return self.get_specialties_list()
        try:
            return json.loads(self.skills)
        except Exception:
            return [s.strip() for s in self.skills.split(",") if s.strip()]

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "email": self.user.email if self.user else None,
            "phone": self.user.phone if self.user else None,
            "college_name": self.user.college_name if self.user else "IIT Delhi Main Campus",
            "service_category": self.service_category,
            "specialties": self.get_specialties_list(),
            "skills": self.get_skills_list(),
            "rating": round(self.rating, 2) if self.rating else 5.0,
            "total_jobs_completed": self.total_jobs_completed,
            "active_jobs_count": self.active_jobs_count,
            "is_available": self.is_available,
            "location_zone": self.location_zone,
            "current_lat": self.current_lat,
            "current_lng": self.current_lng,
        }


class ComplaintCluster(db.Model):
    __tablename__ = "complaint_clusters"

    id = db.Column(db.Integer, primary_key=True)
    cluster_name = db.Column(db.String(120), nullable=False)
    cluster_type = db.Column(db.String(50), default="Geographic DBSCAN")
    building = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(60), nullable=True)
    college_name = db.Column(db.String(120), default="IIT Delhi Main Campus")
    status = db.Column(db.String(30), default="Active")  # 'Active', 'Investigating', 'Resolved'
    complaint_count = db.Column(db.Integer, default=1)
    centroid_lat = db.Column(db.Float, nullable=True)
    centroid_long = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    complaints = db.relationship("Complaint", backref="cluster", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "cluster_name": self.cluster_name,
            "cluster_type": self.cluster_type,
            "building": self.building,
            "category": self.category,
            "college_name": self.college_name,
            "status": self.status,
            "complaint_count": self.complaint_count,
            "centroid_lat": self.centroid_lat,
            "centroid_long": self.centroid_long,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    building = db.Column(db.String(80), nullable=False)
    room_or_area = db.Column(db.String(80), nullable=False)
    college_name = db.Column(db.String(120), default="IIT Delhi Main Campus")
    geo_lat = db.Column(db.Float, nullable=True)
    geo_long = db.Column(db.Float, nullable=True)
    detected_lat = db.Column(db.Float, nullable=True)
    detected_lng = db.Column(db.Float, nullable=True)

    # AI Classification outputs
    predicted_category = db.Column(db.String(60), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    predicted_urgency = db.Column(db.String(30), default="Medium")  # 'Low', 'Medium', 'High', 'Critical'
    urgency_score = db.Column(db.Float, default=0.5)

    # Deterministic / Verified Category & Status
    category = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(40), default="Submitted")  # 'Submitted', 'Triaged', 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Rejected'
    admin_approval_status = db.Column(db.String(40), default="Pending")  # 'Pending', 'Approved Done'
    
    cluster_id = db.Column(db.Integer, db.ForeignKey("complaint_clusters.id"), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
    is_live_capture = db.Column(db.Boolean, default=True)
    authenticity_score = db.Column(db.Float, default=98.5)
    is_fake_detected = db.Column(db.Boolean, default=False)
    is_voice_input = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    job = db.relationship("Job", backref="complaint", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "student_email": self.student.email if self.student else None,
            "student_college": self.college_name or (self.student.college_name if self.student else "IIT Delhi Main Campus"),
            "title": self.title,
            "description": self.description,
            "building": self.building,
            "room_or_area": self.room_or_area,
            "college_name": self.college_name,
            "geo_lat": self.geo_lat,
            "geo_long": self.geo_long,
            "detected_lat": self.detected_lat,
            "detected_lng": self.detected_lng,
            "predicted_category": self.predicted_category,
            "confidence_score": round(self.confidence_score, 2) if self.confidence_score else None,
            "predicted_urgency": self.predicted_urgency,
            "urgency_score": round(self.urgency_score, 2) if self.urgency_score is not None else 0.5,
            "category": self.category,
            "status": self.status,
            "admin_approval_status": self.admin_approval_status,
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster.cluster_name if self.cluster else None,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "is_live_capture": self.is_live_capture,
            "authenticity_score": self.authenticity_score,
            "is_fake_detected": self.is_fake_detected,
            "is_voice_input": self.is_voice_input,
            "job": self.job.to_dict() if self.job else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=False, unique=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id"), nullable=False)
    status = db.Column(db.String(40), default="Assigned")  # 'Assigned', 'Accepted', 'In Progress', 'Completed', 'Approved', 'Cancelled'
    assigned_at = db.Column(db.DateTime, default=utc_now)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    admin_approved_at = db.Column(db.DateTime, nullable=True)
    admin_approved_by = db.Column(db.String(120), nullable=True)
    admin_approval_notes = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    resolution_proof = db.Column(db.Text, nullable=True)  # text note / resolution description
    resolution_image_url = db.Column(db.String(255), nullable=True)  # realistic proof photo of completed fix
    student_feedback_rating = db.Column(db.Integer, nullable=True)
    student_feedback_comment = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "provider_id": self.provider_id,
            "provider_name": self.provider.user.name if self.provider and self.provider.user else None,
            "provider_phone": self.provider.user.phone if self.provider and self.provider.user else None,
            "provider_category": self.provider.service_category if self.provider else None,
            "status": self.status,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "admin_approved_at": self.admin_approved_at.isoformat() if self.admin_approved_at else None,
            "admin_approved_by": self.admin_approved_by,
            "admin_approval_notes": self.admin_approval_notes,
            "notes": self.notes,
            "resolution_proof": self.resolution_proof,
            "resolution_image_url": self.resolution_image_url,
            "student_feedback_rating": self.student_feedback_rating,
            "student_feedback_comment": self.student_feedback_comment,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(40), default="system")  # 'job_assigned', 'status_update', 'cluster_alert', 'emergency_sos', 'system'
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "notification_type": self.notification_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
