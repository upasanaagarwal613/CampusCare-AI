from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from database.db import db
from backend.models import Provider, Job, Complaint, Notification, User
from ml.matcher import provider_matcher

provider_bp = Blueprint("providers", __name__)

def utc_now():
    return datetime.now(timezone.utc)

@provider_bp.route("", methods=["GET"])
def list_providers():
    """Returns directory of all service providers."""
    providers = Provider.query.all()
    return jsonify([p.to_dict() for p in providers])


@provider_bp.route("/recommendations/<int:complaint_id>", methods=["GET"])
def get_recommendations(complaint_id):
    """
    Computes explainable AI match scores for all providers against a target complaint.
    Returns ranked candidate list with transparent scoring breakdown.
    """
    complaint = Complaint.query.get_or_404(complaint_id)
    providers = Provider.query.all()

    providers_data = [p.to_dict() for p in providers]
    complaint_data = complaint.to_dict()

    ranked = provider_matcher.rank_providers(providers_data, complaint_data)
    return jsonify({
        "complaint_id": complaint.id,
        "complaint_category": complaint.category,
        "building": complaint.building,
        "recommendations": ranked
    })


@provider_bp.route("/my-jobs", methods=["GET"])
def get_provider_jobs():
    """Fetches jobs assigned to the requesting provider."""
    provider_id = request.args.get("provider_id")
    if not provider_id:
        user_id = session.get("user_id")
        if user_id:
            provider = Provider.query.filter_by(user_id=user_id).first()
            if provider:
                provider_id = provider.id

    if not provider_id:
        provider = Provider.query.first()
        provider_id = provider.id if provider else None

    if not provider_id:
        return jsonify([])

    jobs = Job.query.filter_by(provider_id=provider_id).order_by(Job.assigned_at.desc()).all()
    
    result = []
    for job in jobs:
        j_dict = job.to_dict()
        j_dict["complaint"] = job.complaint.to_dict() if job.complaint else None
        result.append(j_dict)

    return jsonify(result)


@provider_bp.route("/jobs/<int:job_id>/status", methods=["POST"])
def update_job_status(job_id):
    """
    Service Provider updates job lifecycle:
    'Accepted' -> 'In Progress' -> 'Completed' (with realistic solution photo proof)
    """
    job = Job.query.get_or_404(job_id)
    complaint = job.complaint

    import os
    import uuid

    if request.is_json:
        data = request.get_json() or {}
        image_file = None
    else:
        data = request.form.to_dict()
        image_file = request.files.get("resolution_image")

    new_status = data.get("status")
    notes = data.get("notes")
    resolution_proof = data.get("resolution_proof")

    valid_statuses = ["Accepted", "In Progress", "Completed", "Cancelled"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

    job.status = new_status
    if notes:
        job.notes = notes
    if resolution_proof:
        job.resolution_proof = resolution_proof

    # Handle resolution photo proof upload
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1].lower() or ".jpg"
        unique_name = f"resolution_{uuid.uuid4().hex[:10]}{ext}"
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        upload_folder = os.path.join(base_dir, "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, unique_name)
        image_file.save(save_path)
        job.resolution_image_url = f"/static/uploads/{unique_name}"

    if new_status == "In Progress":
        job.started_at = utc_now()
        if complaint:
            complaint.status = "In Progress"
    elif new_status == "Completed":
        job.completed_at = utc_now()
        if complaint:
            complaint.status = "Resolved"
            complaint.admin_approval_status = "Pending Approval"

        # Notify Facilities Administration that solution proof is ready for approval
        admins = User.query.filter_by(role="admin").all()
        for adm in admins:
            adm_notif = Notification(
                user_id=adm.id,
                title=f"📸 Solution Proof Awaiting Approval: Ticket #{complaint.id if complaint else job.id}",
                message=f"Technician {job.provider.user.name if job.provider and job.provider.user else 'Technician'} submitted fix proof for {complaint.building if complaint else 'Campus'}. Please review and approve.",
                notification_type="status_update"
            )
            db.session.add(adm_notif)

    # Notify student
    if complaint and complaint.student_id:
        notif = Notification(
            user_id=complaint.student_id,
            title=f"Service Update: Ticket #{complaint.id}",
            message=f"Status changed to '{new_status}' by {job.provider.user.name if job.provider and job.provider.user else 'Technician'}. Proof submitted: {'Photo attached' if job.resolution_image_url else 'Notes only'}.",
            notification_type="status_update"
        )
        db.session.add(notif)

    db.session.commit()
    return jsonify({
        "message": f"Job status updated to '{new_status}'",
        "job": job.to_dict(),
        "complaint_status": complaint.status if complaint else None
    })
