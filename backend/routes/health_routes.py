from flask import Blueprint, jsonify, session, request
from database.db import db
from backend.models import User, Complaint, Provider, Job, ComplaintCluster

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for verifying system and database connectivity."""
    db_status = "connected"
    try:
        # Test database connection with a query
        user_count = User.query.count()
        complaint_count = Complaint.query.count()
        provider_count = Provider.query.count()
        job_count = Job.query.count()
        cluster_count = ComplaintCluster.query.count()
    except Exception as e:
        db_status = f"error: {str(e)}"
        user_count = complaint_count = provider_count = job_count = cluster_count = 0

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "CampusCare AI Platform",
        "version": "1.0.0-hackathon-mvp",
        "database": db_status,
        "counts": {
            "users": user_count,
            "complaints": complaint_count,
            "providers": provider_count,
            "jobs": job_count,
            "clusters": cluster_count
        }
    }), 200 if db_status == "connected" else 500


@health_bp.route("/system/stats", methods=["GET"])
def system_stats():
    """Returns analytics overview for dashboard scoped to the active institution."""
    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    col_filter = (admin_user.college_name if (admin_user and admin_user.role == "admin" and admin_user.college_name) else None) or request.args.get("college_name")

    comp_query = Complaint.query
    if col_filter:
        comp_query = comp_query.filter(Complaint.college_name == col_filter)

    total_complaints = comp_query.count()
    resolved_complaints = comp_query.filter(Complaint.status.in_(["Resolved", "Closed", "Closed / Verified"])).count()
    active_complaints = total_complaints - resolved_complaints
    in_progress = comp_query.filter_by(status="In Progress").count()
    critical_count = comp_query.filter_by(predicted_urgency="Critical").count()

    resolution_rate = round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 0.0

    provider_query = Provider.query
    if col_filter:
        provider_query = provider_query.join(User).filter(User.college_name == col_filter)
    prov_count = provider_query.count()
    if prov_count == 0:
        prov_count = Provider.query.count()

    active_clusters_count = ComplaintCluster.query.filter_by(status="Active").count()

    return jsonify({
        "total_complaints": total_complaints,
        "active_complaints": active_complaints,
        "in_progress": in_progress,
        "resolved_complaints": resolved_complaints,
        "critical_count": critical_count,
        "resolution_rate": resolution_rate,
        "total_providers": prov_count,
        "active_clusters": active_clusters_count,
        "college_name": col_filter or "Pan-India Multi-Campus"
    })
