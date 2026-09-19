# CampusCare AI 🏫⚡

> **AI-Powered Campus Complaint & Service Management Platform**  
> *Built for a 24-Hour Hackathon MVP*

CampusCare AI transforms sluggish, opaque campus facilities management into an intelligent, transparent, and rapid-response operations hub. It unites **Students**, **Service Providers**, and **Campus Facilities Administrators** into an integrated workflow powered by real machine learning and spatial clustering.

---

## 🌟 Key Features

1. **🤖 Real-Time NLP Complaint Classification**:
   - Classifies complaint descriptions into 6 categories (*Electrical, Plumbing, HVAC, Internet & IT, Carpentry, Sanitation*) using Scikit-Learn TF-IDF and Naive Bayes.
   - Computes an explainable Urgency Score (0.0 to 1.0) and urgency levels (*Critical, High, Medium, Low*) based on severity signals and keywords (e.g. *sparks, burst pipe, blackout*).
   - Provides instantaneous real-time inference in the browser as the student types.

2. **📍 DBSCAN Spatial Outage & Hotspot Clustering**:
   - Employs Scikit-Learn's `DBSCAN` (Density-Based Spatial Clustering of Applications with Noise) over campus coordinates and buildings.
   - Automatically detects widespread systemic failures (e.g., 3 students reporting tripped circuits in Hostel Block A) to form Incident Clusters and prevent redundant technician dispatches.

3. **🎯 Explainable Multi-Factor Provider Matching**:
   - Matches work orders to qualified contractors using a transparent 100-point scoring algorithm:
     - **Category & Skill Match**: 40 pts
     - **Workload Bandwidth & Availability**: 25 pts
     - **Student Satisfaction Rating**: 20 pts
     - **Campus Zone Proximity**: 15 pts
   - Administrators see exactly why a provider was recommended with point-by-point justifications.

4. **🔄 3-in-1 Role-Based Experience**:
   - **Student Portal**: File issues with instant AI feedback, track progress timeline, rate resolutions (1–5 stars).
   - **Service Provider Portal**: View work orders, accept dispatches, start repairs, submit resolution proof and notes.
   - **Admin Dispatch Desk**: Master complaint queue, DBSCAN cluster scanner, building incident grid, 1-click AI contractor dispatch.

---

## 👥 Seeded Demo Accounts (1-Click Switcher)

The application includes a persistent top banner for instantaneous persona switching during presentations:

| Persona | Email | Password | Details |
|---------|-------|----------|---------|
| 🎓 **Student** | `student@campus.edu` | `student123` | Alex Rivera (Hostel Block A, Room 302) |
| ⚡ **Electrician** | `sparky@campus.edu` | `provider123` | Marcus Vance (⭐ 4.9, 48 completed jobs) |
| 🔧 **Plumber** | `pipes@campus.edu` | `provider123` | Elena Rostova (⭐ 4.8, 39 completed jobs) |
| 🛡️ **Facilities Admin** | `admin@campus.edu` | `admin123` | Dr. Evelyn Reed (Director of Facilities) |

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask 3.1, Flask-SQLAlchemy 3.1
- **Database**: SQLite with SQLAlchemy ORM (6 models: `User`, `Provider`, `Complaint`, `Job`, `ComplaintCluster`, `Notification`)
- **AI / ML**: Scikit-Learn (`TfidfVectorizer`, `MultinomialNB`, `DBSCAN`), NumPy
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (zero node build step required)

---

## 🚀 Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
You can run either from the project root:
```bash
python run.py
```
or from inside `CampusCare-AI/`:
```bash
cd CampusCare-AI
python run.py
```

### 3. Open in Browser
- **Web App**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Health Check API**: [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)

---

## 📡 REST API Endpoints

### Health & Analytics
- `GET /api/health` - Diagnostic health check and database record counts.
- `GET /api/system/stats` - Platform KPIs (total, active, resolution rate, critical count).

### Authentication
- `GET /api/auth/demo-users` - List all seeded demo accounts.
- `POST /api/auth/switch-demo` - Instantly switch active session persona.
- `GET /api/auth/current-user` - Get authenticated session user.

### Complaints
- `POST /api/complaints/preview-ai` - Real-time NLP category & urgency prediction.
- `POST /api/complaints` - File a new complaint (triggers AI classification & DBSCAN check).
- `GET /api/complaints` - Query complaints (filters: status, category, urgency, student_id).
- `POST /api/complaints/<id>/feedback` - Submit student star rating & review.

### Service Providers & Matching
- `GET /api/providers` - Directory of providers with ratings, skills, and workload.
- `GET /api/providers/recommendations/<complaint_id>` - Explainable AI matching recommendations.
- `GET /api/providers/my-jobs` - Work orders assigned to active provider.
- `POST /api/providers/jobs/<id>/status` - Update job status (`Accepted`, `In Progress`, `Completed`).

### Facilities Administration
- `GET /api/admin/clusters` - View active DBSCAN incident clusters.
- `POST /api/admin/clusters/run-dbscan` - Execute spatial clustering on open complaints.
- `POST /api/admin/dispatch` - Assign technician to work order.
- `GET /api/admin/campus-map` - Incident density by campus building.
