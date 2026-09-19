from datetime import datetime, timezone
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
    critical_count = comp_query.filter(Complaint.predicted_urgency == "Critical", ~Complaint.status.in_(["Resolved", "Closed", "Closed / Verified"])).count()
    pending_assignments = comp_query.filter_by(status="Submitted").count()

    resolution_rate = round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 0.0

    # Provider metrics
    provider_query = Provider.query
    if col_filter:
        provider_query = provider_query.join(User).filter(User.college_name == col_filter)
    all_providers = provider_query.all()
    if not all_providers:
        all_providers = Provider.query.all()

    prov_count = len(all_providers)
    active_providers = sum(1 for p in all_providers if p.is_available)

    # Active Jobs count
    job_query = Job.query.join(Complaint)
    if col_filter:
        job_query = job_query.filter(Complaint.college_name == col_filter)
    active_jobs_count = job_query.filter(Job.status.in_(["Assigned", "Accepted", "On the Way", "In Progress"])).count()

    # SLA Breaches calculation (estimated based on created_at vs current time)
    now = datetime.now(timezone.utc)
    open_comps = comp_query.filter(~Complaint.status.in_(["Resolved", "Closed", "Closed / Verified"])).all()
    sla_breaches = 0
    for oc in open_comps:
        if oc.created_at:
            created = oc.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_hours = (now - created).total_seconds() / 3600.0
            if oc.predicted_urgency == "Critical" and age_hours > 2.0:
                sla_breaches += 1
            elif oc.predicted_urgency == "High" and age_hours > 12.0:
                sla_breaches += 1
            elif age_hours > 24.0:
                sla_breaches += 1

    active_clusters_count = ComplaintCluster.query.filter_by(status="Active").count()

    # Recurring problems summary (top facilities with multiple open reports)
    facility_counts = {}
    for oc in open_comps:
        key = f"{oc.building} • {oc.category}"
        facility_counts[key] = facility_counts.get(key, 0) + 1
    recurring_problems = [
        {"facility": k, "count": v}
        for k, v in sorted(facility_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Provider Workload snapshot
    provider_workload = []
    for p in all_providers[:6]:
        provider_workload.append({
            "name": p.user.name if p.user else "Technician",
            "category": p.service_category,
            "active_jobs": p.active_jobs_count or 0,
            "rating": round(p.rating, 1) if p.rating else 5.0,
            "is_available": p.is_available
        })

    # Recent escalations
    escalations = [
        {
            "id": oc.id,
            "title": oc.title,
            "building": oc.building,
            "category": oc.category,
            "urgency": oc.predicted_urgency,
            "status": oc.status,
            "created_at": oc.created_at.isoformat() if oc.created_at else None
        }
        for oc in open_comps if oc.predicted_urgency == "Critical"
    ][:5]

    return jsonify({
        "total_complaints": total_complaints,
        "active_complaints": active_complaints,
        "active_jobs": active_jobs_count,
        "in_progress": in_progress,
        "resolved_complaints": resolved_complaints,
        "critical_count": critical_count,
        "active_providers": active_providers,
        "total_providers": prov_count,
        "sla_breaches": sla_breaches,
        "pending_assignments": pending_assignments,
        "resolution_rate": resolution_rate,
        "active_clusters": active_clusters_count,
        "recurring_problems": recurring_problems,
        "provider_workload": provider_workload,
        "escalations": escalations,
        "college_name": col_filter or "Pan-India Multi-Campus"
    })

