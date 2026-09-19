from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from database.db import db
from backend.models import Complaint, Provider, Job, ComplaintCluster, Notification, User
from ml.clustering import dbscan_clusterer, CAMPUS_BUILDING_COORDS
from backend.colleges import find_college_by_name, get_all_buildings_for_college, get_all_colleges

admin_bp = Blueprint("admin", __name__)

def utc_now():
    return datetime.now(timezone.utc)

@admin_bp.route("/clusters", methods=["GET"])
def list_clusters():
    """
    Returns spatial clusters on dual bases:
    - ?basis=volume: DBSCAN density-based grouping by complaint numbers
    - ?basis=severity: Hazard-based grouping by problem criticality
    - ?college_name=...: Filter by specific college anywhere in India
    """
    basis = request.args.get("basis", "volume").lower()

    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    
    # Prefer explicit college query parameter if supplied, otherwise lock to admin's registered institution
    target_college = request.args.get("college_name") or (admin_user.college_name if admin_user else None)

    query = Complaint.query.filter(
        Complaint.status.in_(["Submitted", "Triaged", "Assigned", "In Progress"])
    )
    if target_college:
        query = query.filter(Complaint.college_name == target_college)

    active_complaints = query.all()
    complaints_data = [c.to_dict() for c in active_complaints]

    cluster_data = dbscan_clusterer.run_clustering(complaints_data, basis=basis)
    return jsonify(cluster_data)


@admin_bp.route("/clusters/run-dbscan", methods=["POST"])
def run_dbscan_clustering():
    """Triggers spatial clustering across all active complaints."""
    body = request.get_json(silent=True) or {}
    basis = body.get("basis", "volume").lower()

    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    admin_college = admin_user.college_name if admin_user else None

    query = Complaint.query.filter(
        Complaint.status.in_(["Submitted", "Triaged", "Assigned", "In Progress"])
    )
    if admin_college:
        query = query.filter(Complaint.college_name == admin_college)

    active_complaints = query.all()
    complaints_data = [c.to_dict() for c in active_complaints]
    cluster_results = dbscan_clusterer.run_clustering(complaints_data, basis=basis)

    if basis == "volume":
        for cl in cluster_results["clusters"]:
            existing = ComplaintCluster.query.filter_by(
                building=cl["building"], category=cl["category"], status="Active"
            ).first()

            if not existing:
                existing = ComplaintCluster(
                    cluster_name=cl["cluster_name"],
                    cluster_type="DBSCAN Volume Density",
                    building=cl["building"],
                    category=cl["category"],
                    status="Active",
                    complaint_count=cl["count"],
                    centroid_lat=cl["centroid_lat"],
                    centroid_long=cl["centroid_long"]
                )
                db.session.add(existing)
                db.session.flush()

            existing.complaint_count = cl["count"]
            existing.centroid_lat = cl["centroid_lat"]
            existing.centroid_long = cl["centroid_long"]

            for comp_id in cl["complaint_ids"]:
                comp = db.session.get(Complaint, comp_id)
                if comp:
                    comp.cluster_id = existing.id

        db.session.commit()

    return jsonify({
        "message": f"Clustering refreshed ({basis.upper()}). Found {len(cluster_results['clusters'])} active clusters.",
        "basis": basis,
        "clusters_detected": cluster_results["clusters"],
        "unclustered_isolated_ids": cluster_results.get("noise_ids", [])
    })


@admin_bp.route("/directory", methods=["GET"])
def get_campus_directory():
    """Returns directory of all users (Students, Providers, Admins) with live GPS and provider details."""
    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None

    query = User.query
    if admin_user and admin_user.college_name:
        query = query.filter(User.college_name == admin_user.college_name)

    users = query.order_by(User.role, User.name).all()
    directory = []
    for u in users:
        u_dict = u.to_dict()
        if u.role == "provider" and u.provider_profile:
            p = u.provider_profile
            u_dict["service_category"] = p.service_category
            u_dict["specialties"] = p.get_specialties_list()
            u_dict["rating"] = p.rating
            u_dict["active_jobs_count"] = p.active_jobs_count
            u_dict["total_jobs_completed"] = p.total_jobs_completed
            u_dict["location_zone"] = p.location_zone
            u_dict["is_available"] = p.is_available
            u_dict["current_lat"] = p.current_lat or u.live_lat
            u_dict["current_lng"] = p.current_lng or u.live_lng
        elif u.role == "student":
            u_dict["total_complaints_filed"] = Complaint.query.filter_by(student_id=u.id).count()
        directory.append(u_dict)

    return jsonify(directory)


@admin_bp.route("/audit-resolutions", methods=["GET"])
def get_resolution_audit():
    """
    Full Problem-to-Solution Audit Trail for Facilities Admin:
    Shows incoming problem, original live photo, audio memo, technician who resolved it,
    solution proof photo, notes, and Admin Done/Approval sign-off status.
    """
    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    admin_college = (admin_user.college_name if (admin_user and admin_user.role == "admin" and admin_user.college_name) else None) or request.args.get("college_name")

    query = Job.query.join(Complaint).order_by(Job.assigned_at.desc())
    if admin_college:
        query = query.filter(Complaint.college_name == admin_college)
    jobs = query.all()
    audit_trail = []
    for j in jobs:
        c = j.complaint
        if not c:
            continue
        p = j.provider
        audit_trail.append({
            "job_id": j.id,
            "complaint_id": c.id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "building": c.building,
            "room_or_area": c.room_or_area,
            "urgency": c.predicted_urgency,
            "urgency_score": c.urgency_score,
            "status": c.status,
            "admin_approval_status": c.admin_approval_status or ("Approved Done" if j.status == "Approved" else "Pending"),
            "incident_image_url": c.image_url,
            "audio_url": c.audio_url,
            "is_voice_input": c.is_voice_input,
            "authenticity_score": c.authenticity_score,
            "is_live_capture": c.is_live_capture,
            "reported_at": c.created_at.isoformat() if c.created_at else None,
            "student_name": c.student.name if c.student else "Student",
            "student_email": c.student.email if c.student else None,
            "student_phone": c.student.phone if c.student else None,
            "student_college": c.college_name,
            "resolver_name": p.user.name if p and p.user else "Unassigned",
            "resolver_phone": p.user.phone if p and p.user else "N/A",
            "resolver_email": p.user.email if p and p.user else "N/A",
            "resolver_category": p.service_category if p else "N/A",
            "resolver_rating": p.rating if p else 5.0,
            "resolution_notes": j.notes or j.resolution_proof or "No resolution notes provided",
            "resolution_image_url": j.resolution_image_url,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "admin_approved_at": j.admin_approved_at.isoformat() if j.admin_approved_at else None,
            "admin_approved_by": j.admin_approved_by,
            "feedback_rating": j.student_feedback_rating
        })

    return jsonify(audit_trail)


@admin_bp.route("/jobs/<int:job_id>/approve", methods=["POST"])
def approve_job_resolution(job_id):
    """
    Admin Final Done / Sign-Off Action:
    Admin reviews the realistic solution proof photo and officially approves & closes the ticket.
    """
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    complaint = job.complaint
    if not complaint:
        return jsonify({"error": "Associated complaint not found"}), 404

    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    admin_name = admin_user.name if admin_user else "Facilities Administrator"

    body = request.get_json(silent=True) or {}
    approval_notes = body.get("notes", "Resolution verified and signed off by Facilities Administration.")

    # Mark as Officially Approved & Closed
    job.status = "Approved"
    job.admin_approved_at = utc_now()
    job.admin_approved_by = admin_name
    job.admin_approval_notes = approval_notes

    complaint.status = "Closed / Verified"
    complaint.admin_approval_status = "Approved Done"

    # Decrement active jobs if technician still had it active
    provider = job.provider
    if provider:
        if provider.active_jobs_count and provider.active_jobs_count > 0:
            provider.active_jobs_count -= 1
        provider.total_jobs_completed = (provider.total_jobs_completed or 0) + 1

    # Send confirmation notifications
    s_notif = Notification(
        user_id=complaint.student_id,
        title=f"✅ Ticket #{complaint.id} Approved & Closed",
        message=f"Administrator {admin_name} has inspected the technician's solution proof and officially closed your issue.",
        notification_type="status_update"
    )
    if provider:
        p_notif = Notification(
            user_id=provider.user_id,
            title=f"🏆 Work Order #{job.id} Approved",
            message=f"Your resolution proof for Ticket #{complaint.id} has been verified and approved by {admin_name}.",
            notification_type="status_update"
        )
        db.session.add(p_notif)

    db.session.add(s_notif)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Ticket #{complaint.id} resolution verified and officially approved by {admin_name}.",
        "job": job.to_dict(),
        "complaint": complaint.to_dict()
    })


@admin_bp.route("/emergency-sos", methods=["POST"])
def broadcast_emergency_sos():
    """
    Broadcasts high-priority Emergency SOS alert to providers across campus.
    """
    body = request.get_json(silent=True) or {}
    building = body.get("building", "General Campus Area")
    category = body.get("category", "Emergency Hazard")
    description = body.get("description", "Immediate hazard detected requiring emergency response.")

    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None
    admin_name = admin_user.name if admin_user else "Facilities Command"
    admin_college = admin_user.college_name if admin_user else None

    # Notify providers strictly belonging to this college
    provider_query = Provider.query.join(User)
    if admin_college:
        provider_query = provider_query.filter(User.college_name == admin_college)
    providers = provider_query.all()
    if not providers and admin_college:
        # Fallback to any provider if no providers are registered specifically in this college yet
        providers = Provider.query.all()

    count_notified = 0
    for p in providers:
        notif = Notification(
            user_id=p.user_id,
            title=f"🚨 EMERGENCY SOS DISPATCH ({building})",
            message=f"CRITICAL ALERT: {category} in {building}. {description} Dispatched by {admin_name}.",
            notification_type="emergency_sos"
        )
        db.session.add(notif)
        count_notified += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Emergency SOS broadcast dispatched to {count_notified} technicians across campus!",
        "building": building,
        "category": category
    })


@admin_bp.route("/dispatch", methods=["POST"])
def dispatch_job():
    """Dispatches a technician to a complaint."""
    data = request.get_json() or {}
    complaint_id = data.get("complaint_id")
    provider_id = data.get("provider_id")
    notes = data.get("notes", "Dispatched by Facilities Administrator")

    if not complaint_id or not provider_id:
        return jsonify({"error": "complaint_id and provider_id are required"}), 400

    complaint = db.session.get(Complaint, complaint_id)
    provider = db.session.get(Provider, provider_id)
    if not complaint or not provider:
        return jsonify({"error": "Complaint or Provider not found"}), 404

    job = Job.query.filter_by(complaint_id=complaint.id).first()
    if job:
        job.provider_id = provider.id
        job.status = "Assigned"
        job.notes = notes
    else:
        job = Job(
            complaint_id=complaint.id,
            provider_id=provider.id,
            status="Assigned",
            notes=notes
        )
        db.session.add(job)

    complaint.status = "Assigned"
    provider.active_jobs_count = (provider.active_jobs_count or 0) + 1

    p_notif = Notification(
        user_id=provider.user_id,
        title=f"New Work Order: Ticket #{complaint.id}",
        message=f"Assigned to {complaint.building} - {complaint.room_or_area} ({complaint.category}, Urgency: {complaint.predicted_urgency})",
        notification_type="job_assigned"
    )
    s_notif = Notification(
        user_id=complaint.student_id,
        title=f"Technician Assigned: Ticket #{complaint.id}",
        message=f"{provider.user.name} ({provider.service_category}) has been assigned to your ticket.",
        notification_type="status_update"
    )
    db.session.add_all([p_notif, s_notif])
    db.session.commit()

    return jsonify({
        "message": "Work order dispatched successfully",
        "job": job.to_dict(),
        "complaint": complaint.to_dict()
    })


@admin_bp.route("/colleges", methods=["GET"])
def get_pan_india_colleges():
    """Returns list of 50+ Pan-India colleges across all zones with GPS coordinates."""
    colleges = get_all_colleges()
    return jsonify({
        "colleges": colleges,
        "total": len(colleges)
    })


@admin_bp.route("/campus-map", methods=["GET"])
def campus_map_data():
    """
    Returns GPS coordinates, hazard scores, and active issue summaries for hover popups.
    Dynamically centers on and computes building GPS coordinates for ANY college across India.
    """
    user_id = session.get("user_id")
    admin_user = db.session.get(User, user_id) if user_id else None

    # Prefer explicit college query parameter if supplied, otherwise lock to admin's registered institution
    target_college = request.args.get("college_name") or (admin_user.college_name if admin_user else None)

    col_info = find_college_by_name(target_college)
    
    # Honor Admin's live detected GPS coordinates if available, otherwise use college coordinates
    center_lat = (admin_user.live_lat if admin_user and admin_user.live_lat else None) or col_info["lat"]
    center_lng = (admin_user.live_lng if admin_user and admin_user.live_lng else None) or col_info["lng"]
    
    building_coords = get_all_buildings_for_college(target_college)

    building_stats = []
    for building_name, coords in building_coords.items():
        query = Complaint.query.filter(
            Complaint.building == building_name,
            Complaint.status.in_(["Submitted", "Triaged", "Assigned", "In Progress"])
        )
        if target_college:
            query = query.filter(Complaint.college_name == target_college)

        open_comps = query.all()
        total_open = len(open_comps)
        critical_count = sum(1 for c in open_comps if c.predicted_urgency == "Critical")
        high_count = sum(1 for c in open_comps if c.predicted_urgency == "High")
        medium_count = sum(1 for c in open_comps if c.predicted_urgency == "Medium")
        low_count = sum(1 for c in open_comps if c.predicted_urgency == "Low")

        # Hazard Index (0.0 - 1.0)
        if total_open > 0:
            weights = {"Critical": 1.0, "High": 0.75, "Medium": 0.5, "Low": 0.25}
            hazard_score = round(sum(weights.get(c.predicted_urgency, 0.5) for c in open_comps) / total_open, 2)
        else:
            hazard_score = 0.0

        active_clusters = ComplaintCluster.query.filter_by(
            building=building_name, status="Active"
        ).count()

        # Build detailed problem narrative from active complaints
        all_descs = [c.description.strip() for c in open_comps if c.description and c.description.strip()]
        problem_narrative = " • ".join(all_descs[:3]) if all_descs else (open_comps[0].title if open_comps else "No active maintenance issues.")

        # Build issue snippets for rich hover card
        issues_summary = [
            f"#{c.id}: {c.title} ({c.predicted_urgency})"
            for c in open_comps[:4]
        ]

        building_stats.append({
            "building": building_name,
            "lat": coords[0],
            "lon": coords[1],
            "college_name": target_college or col_info["name"],
            "college_center": [center_lat, center_lng],
            "college_city": col_info.get("city", "India"),
            "college_zone": col_info.get("zone", "Pan-India"),
            "open_complaints": total_open,
            "critical_complaints": critical_count,
            "high_complaints": high_count,
            "medium_complaints": medium_count,
            "low_complaints": low_count,
            "hazard_score": hazard_score,
            "has_cluster": active_clusters > 0,
            "issues_summary": issues_summary,
            "problem_description": problem_narrative,
            "sample_description": problem_narrative
        })

    return jsonify(building_stats)
