import json
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from database.db import db
from backend.models import User, Provider, Complaint, Job, ComplaintCluster, Notification
from ml.classifier import nlp_classifier
from ml.clustering import dbscan_clusterer, get_building_coords

def now_utc():
    return datetime.now(timezone.utc)


def seed_database():
    """Seeds realistic demo data for the hackathon presentation."""
    # Check if already seeded
    if User.query.first():
        print("Database already contains records. Skipping seed.")
        return

    print("Seeding demo accounts and campus data...")

    # 1. Create Users
    # Students
    student1 = User(
        name="Alex Rivera",
        email="student@campus.edu",
        password_hash=generate_password_hash("student123"),
        role="student",
        phone="+1 (555) 101-2001",
    )
    student2 = User(
        name="Priya Sharma",
        email="student2@campus.edu",
        password_hash=generate_password_hash("student123"),
        role="student",
        phone="+1 (555) 101-2002",
    )
    student3 = User(
        name="Jordan Lee",
        email="student3@campus.edu",
        password_hash=generate_password_hash("student123"),
        role="student",
        phone="+1 (555) 101-2003",
    )

    # Providers
    p_user_elec = User(
        name="Marcus Vance",
        email="sparky@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3001",
    )
    p_user_plumb = User(
        name="Elena Rostova",
        email="pipes@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3002",
    )
    p_user_hvac = User(
        name="David Chen",
        email="cool@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3003",
    )
    p_user_carpentry = User(
        name="Samuel Green",
        email="wood@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3004",
    )
    p_user_it = User(
        name="Vikram Patel",
        email="net@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3005",
    )
    p_user_clean = User(
        name="Rosa Morales",
        email="clean@campus.edu",
        password_hash=generate_password_hash("provider123"),
        role="provider",
        phone="+1 (555) 202-3006",
    )

    # Admin
    admin_user = User(
        name="Dr. Evelyn Reed",
        email="admin@campus.edu",
        password_hash=generate_password_hash("admin123"),
        role="admin",
        phone="+1 (555) 000-1111",
    )

    db.session.add_all([
        student1, student2, student3,
        p_user_elec, p_user_plumb, p_user_hvac,
        p_user_carpentry, p_user_it, p_user_clean,
        admin_user
    ])
    db.session.commit()

    # 2. Create Provider Profiles
    prov_elec = Provider(
        user_id=p_user_elec.id,
        service_category="Electrical",
        skills=json.dumps(["Circuit Breakers", "Wiring", "Lighting", "Sparks & Hazards", "Generators"]),
        rating=4.9,
        total_jobs_completed=48,
        active_jobs_count=1,
        is_available=True,
        location_zone="Hostel Zone",
    )
    prov_plumb = Provider(
        user_id=p_user_plumb.id,
        service_category="Plumbing",
        skills=json.dumps(["Pipe Leakage", "Drainage", "Clogged Toilets", "Water Heaters", "Fittings"]),
        rating=4.8,
        total_jobs_completed=39,
        active_jobs_count=1,
        is_available=True,
        location_zone="Hostel Zone",
    )
    prov_hvac = Provider(
        user_id=p_user_hvac.id,
        service_category="HVAC",
        skills=json.dumps(["AC Repair", "Ventilation", "Thermostat", "Heating Systems", "Ducts"]),
        rating=4.7,
        total_jobs_completed=27,
        active_jobs_count=0,
        is_available=True,
        location_zone="Academic Zone",
    )
    prov_carp = Provider(
        user_id=p_user_carpentry.id,
        service_category="Carpentry & Furniture",
        skills=json.dumps(["Door Locks", "Keys & Latches", "Bed Frames", "Desks & Chairs", "Windows"]),
        rating=4.9,
        total_jobs_completed=52,
        active_jobs_count=0,
        is_available=True,
        location_zone="Central Zone",
    )
    prov_it = Provider(
        user_id=p_user_it.id,
        service_category="Internet & IT",
        skills=json.dumps(["WiFi Access Points", "LAN Cabling", "Switch Hardware", "Network Jacks"]),
        rating=4.9,
        total_jobs_completed=65,
        active_jobs_count=0,
        is_available=True,
        location_zone="Academic Zone",
    )
    prov_clean = Provider(
        user_id=p_user_clean.id,
        service_category="Sanitation & Cleaning",
        skills=json.dumps(["Sanitization", "Pest Control", "Waste Clearance", "Hallway Scrubbing"]),
        rating=4.8,
        total_jobs_completed=81,
        active_jobs_count=0,
        is_available=True,
        location_zone="Campus-Wide",
    )

    db.session.add_all([prov_elec, prov_plumb, prov_hvac, prov_carp, prov_it, prov_clean])
    db.session.commit()

    # 3. Create Sample Complaints with Coordinates
    c1_lat, c1_lon = get_building_coords("Hostel Block A")
    ai1 = nlp_classifier.classify("Sparks from main switch board and complete power trip", "Smoke smell near study desk")
    comp1 = Complaint(
        student_id=student1.id,
        title="Sparks from main switch board and power trip",
        description="There was a loud pop, visible sparks from the switchboard, and the entire room 302 circuit tripped.",
        building="Hostel Block A",
        room_or_area="Room 302",
        geo_lat=c1_lat,
        geo_long=c1_lon,
        predicted_category=ai1["predicted_category"],
        confidence_score=ai1["confidence_score"],
        predicted_urgency=ai1["predicted_urgency"],
        urgency_score=ai1["urgency_score"],
        category=ai1["predicted_category"],
        status="Assigned",
        created_at=now_utc() - timedelta(hours=3),
    )

    c2_lat, c2_lon = 12.97152, 77.59452  # 20m from c1
    ai2 = nlp_classifier.classify("Ceiling fan not working and corridor lights flickering", "Corridor lights are flickering and room power keeps dropping")
    comp2 = Complaint(
        student_id=student2.id,
        title="Ceiling fan dead and corridor lights flickering",
        description="Fan suddenly stopped turning, breaker made clicking sound, light in hallway is also dimming.",
        building="Hostel Block A",
        room_or_area="Room 305",
        geo_lat=c2_lat,
        geo_long=c2_lon,
        predicted_category=ai2["predicted_category"],
        confidence_score=ai2["confidence_score"],
        predicted_urgency=ai2["predicted_urgency"],
        urgency_score=ai2["urgency_score"],
        category=ai2["predicted_category"],
        status="Submitted",
        created_at=now_utc() - timedelta(hours=2),
    )

    c3_lat, c3_lon = 12.97155, 77.59458  # 30m from c1
    ai3 = nlp_classifier.classify("Third floor corridor lights completely dark power outage", "Total blackout in the east wing corridor, cannot see anything at night.")
    comp3 = Complaint(
        student_id=student1.id,
        title="3rd Floor corridor blackout outage",
        description="Emergency lights are blinking, regular lights are completely unpowered.",
        building="Hostel Block A",
        room_or_area="Floor 3 East Wing",
        geo_lat=c3_lat,
        geo_long=c3_lon,
        predicted_category=ai3["predicted_category"],
        confidence_score=ai3["confidence_score"],
        predicted_urgency=ai3["predicted_urgency"],
        urgency_score=ai3["urgency_score"],
        category=ai3["predicted_category"],
        status="Submitted",
        created_at=now_utc() - timedelta(hours=1),
    )

    # Plumbing complaint in Hostel Block B
    b_lat, b_lon = get_building_coords("Hostel Block B")
    ai4 = nlp_classifier.classify("Severe water pipe leakage under bathroom sink", "Water pooling on the floor, leaking constantly from the U-joint.")
    comp4 = Complaint(
        student_id=student3.id,
        title="Severe water pipe leakage under bathroom sink",
        description="Water pooling on the floor, leaking constantly from the U-joint.",
        building="Hostel Block B",
        room_or_area="Room 104",
        geo_lat=b_lat,
        geo_long=b_lon,
        predicted_category=ai4["predicted_category"],
        confidence_score=ai4["confidence_score"],
        predicted_urgency=ai4["predicted_urgency"],
        urgency_score=ai4["urgency_score"],
        category=ai4["predicted_category"],
        status="In Progress",
        created_at=now_utc() - timedelta(hours=5),
    )

    # HVAC complaint in Library Building
    lib_lat, lib_lon = get_building_coords("Library Building")
    ai5 = nlp_classifier.classify("Air conditioner blowing hot air in quiet study hall", "AC unit blowing humid warm air, students cannot study comfortably.")
    comp5 = Complaint(
        student_id=student2.id,
        title="AC blowing hot air in quiet study hall",
        description="AC unit blowing humid warm air, students cannot study comfortably.",
        building="Library Building",
        room_or_area="2nd Floor Quiet Study",
        geo_lat=lib_lat,
        geo_long=lib_lon,
        predicted_category=ai5["predicted_category"],
        confidence_score=ai5["confidence_score"],
        predicted_urgency=ai5["predicted_urgency"],
        urgency_score=ai5["urgency_score"],
        category=ai5["predicted_category"],
        status="Submitted",
        created_at=now_utc() - timedelta(minutes=45),
    )

    # IT complaint in Engineering Hall
    eng_lat, eng_lon = get_building_coords("Engineering Hall")
    ai6 = nlp_classifier.classify("WiFi router offline and ethernet ports unresponsive", "Cannot connect to internet to submit senior capstone project.")
    comp6 = Complaint(
        student_id=student3.id,
        title="WiFi access point offline in project lab",
        description="Cannot connect to internet to submit senior capstone project, SSID is broadcasting but no internet.",
        building="Engineering Hall",
        room_or_area="Lab 201",
        geo_lat=eng_lat,
        geo_long=eng_lon,
        predicted_category=ai6["predicted_category"],
        confidence_score=ai6["confidence_score"],
        predicted_urgency=ai6["predicted_urgency"],
        urgency_score=ai6["urgency_score"],
        category=ai6["predicted_category"],
        status="Submitted",
        created_at=now_utc() - timedelta(minutes=20),
    )

    db.session.add_all([comp1, comp2, comp3, comp4, comp5, comp6])
    db.session.commit()

    # 4. Form an initial DBSCAN Hotspot Cluster for Hostel Block A (comp1, comp2, comp3)
    cluster1 = ComplaintCluster(
        cluster_name="Hostel Block A - Electrical Power Tripping Incident",
        cluster_type="Geographic DBSCAN Hotspot",
        building="Hostel Block A",
        category="Electrical",
        status="Active",
        complaint_count=3,
        centroid_lat=round((c1_lat + c2_lat + c3_lat) / 3, 5),
        centroid_long=round((c1_lon + c2_lon + c3_lon) / 3, 5),
        created_at=now_utc() - timedelta(hours=1),
    )
    db.session.add(cluster1)
    db.session.commit()

    comp1.cluster_id = cluster1.id
    comp2.cluster_id = cluster1.id
    comp3.cluster_id = cluster1.id
    db.session.commit()

    # 5. Create Seeded Jobs
    job1 = Job(
        complaint_id=comp1.id,
        provider_id=prov_elec.id,
        status="Accepted",
        assigned_at=now_utc() - timedelta(hours=2, minutes=30),
        notes="Dispatched to Hostel Block A. Carrying heavy-duty circuit breaker and voltage multimeter.",
    )
    job2 = Job(
        complaint_id=comp4.id,
        provider_id=prov_plumb.id,
        status="In Progress",
        assigned_at=now_utc() - timedelta(hours=4),
        started_at=now_utc() - timedelta(hours=1),
        notes="Isolated water supply line. Replacing rubber seals on P-trap.",
    )
    db.session.add_all([job1, job2])
    db.session.commit()

    # 6. Create Seeded Notifications
    notif1 = Notification(
        user_id=student1.id,
        title="Technician Dispatched",
        message="Marcus Vance (Electrical) has accepted your complaint for Room 302.",
        notification_type="status_update",
    )
    notif2 = Notification(
        user_id=p_user_elec.id,
        title="High Priority Job Assigned",
        message="New Critical Electrical complaint assigned in Hostel Block A, Room 302.",
        notification_type="job_assigned",
    )
    notif3 = Notification(
        user_id=admin_user.id,
        title="AI Hotspot Cluster Detected",
        message="3 concurrent Electrical complaints clustered in Hostel Block A. Probable wing sub-station failure.",
        notification_type="cluster_alert",
    )
    db.session.add_all([notif1, notif2, notif3])
    db.session.commit()

    print("Demo database seeding completed successfully!")
