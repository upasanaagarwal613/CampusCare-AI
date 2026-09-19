import sqlite3

con = sqlite3.connect('data/campuscare.db')
cur = con.cursor()

def add_col_if_missing(table, col, col_type):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    if col not in cols:
        print(f"Adding {col} to {table}...")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        con.commit()
    else:
        print(f"{col} already exists in {table}")

# Users
add_col_if_missing("users", "college_name", "VARCHAR(120) DEFAULT 'IIT Delhi Main Campus'")
add_col_if_missing("users", "id_verified", "BOOLEAN DEFAULT 1")
add_col_if_missing("users", "live_lat", "FLOAT")
add_col_if_missing("users", "live_lng", "FLOAT")

# Complaints
add_col_if_missing("complaints", "college_name", "VARCHAR(120) DEFAULT 'IIT Delhi Main Campus'")
add_col_if_missing("complaints", "audio_url", "VARCHAR(255)")
add_col_if_missing("complaints", "authenticity_score", "FLOAT DEFAULT 98.5")
add_col_if_missing("complaints", "is_fake_detected", "BOOLEAN DEFAULT 0")
add_col_if_missing("complaints", "is_live_capture", "BOOLEAN DEFAULT 1")
add_col_if_missing("complaints", "detected_lat", "FLOAT")
add_col_if_missing("complaints", "detected_lng", "FLOAT")
add_col_if_missing("complaints", "admin_approval_status", "VARCHAR(40) DEFAULT 'Pending'")

# Jobs
add_col_if_missing("jobs", "admin_approved_at", "DATETIME")
add_col_if_missing("jobs", "admin_approved_by", "VARCHAR(120)")
add_col_if_missing("jobs", "admin_approval_notes", "TEXT")

# Providers
add_col_if_missing("providers", "current_lat", "FLOAT")
add_col_if_missing("providers", "current_lng", "FLOAT")

# Complaint Clusters
add_col_if_missing("complaint_clusters", "college_name", "VARCHAR(120) DEFAULT 'IIT Delhi Main Campus'")

con.close()
print("Migration completed successfully!")

