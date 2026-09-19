import numpy as np
from sklearn.cluster import DBSCAN
from ml.colleges import (
    get_building_coords_for_college, 
    find_college_by_name, 
    get_all_buildings_for_college,
    ALL_COLLEGES
)

# Realistic fallback coordinates for university campus buildings
CAMPUS_BUILDING_COORDS = {
    "Hostel Block A": (28.5420, 77.1910),
    "Hostel Block B": (28.5428, 77.1918),
    "Central Library": (28.5452, 77.1932),
    "Library Building": (28.5452, 77.1932),
    "Engineering Hall": (28.5460, 77.1950),
    "Science Complex": (28.5468, 77.1960),
    "Dining Center": (28.5435, 77.1925),
    "Sports Complex": (28.5410, 77.1900),
    "Administrative Block": (28.5475, 77.1930),
}

# Category vibrant color palette
CATEGORY_COLORS = {
    "Electrical": "#f59e0b",         # Electric Amber / Gold
    "Plumbing": "#06b6d4",           # Aqua Cyan
    "HVAC": "#0284c7",               # Sky Blue
    "Civil / Infrastructure": "#8b5cf6", # Purple
    "Safety / Hazard": "#ef4444",     # Radiant Crimson Red
    "IT / Internet": "#10b981",       # Emerald Green
    "Sanitation / Grounds": "#84cc16", # Fresh Lime
    "Lab Equipment": "#6366f1",       # Deep Indigo
    "Emergency SOS": "#dc2626",       # Pulsing Emergency Red
    "General": "#ec4899"              # Rose
}

SEVERITY_WEIGHTS = {
    "Critical": 1.0,
    "High": 0.75,
    "Medium": 0.50,
    "Low": 0.25
}

def get_building_coords(building_name: str, college_name: str = None):
    if college_name:
        return get_building_coords_for_college(building_name, college_name)
    return CAMPUS_BUILDING_COORDS.get(building_name, (28.5450, 77.1930))

def get_category_color(category_name: str):
    if not category_name:
        return "#4f46e5"
    for cat_key, col in CATEGORY_COLORS.items():
        if cat_key.lower() in category_name.lower():
            return col
    return "#4f46e5"


class DualBasisComplaintClusterer:
    """
    Enhanced Enterprise Spatial & Facility Clustering Engine:
    - Hybrid DBSCAN + Facility Building Hotspot Detection:
      * Groups co-located incidents within 350m (eps=0.0035) into high-density zones.
      * Clusters multiple issues in the same building/facility into actionable hotspots.
      * Elevates Critical/Emergency hazard tickets into immediate radar beacons.
    - Rich Payloads: Formatted executive problem narratives, ticket rosters, severity meters.
    """
    def __init__(self, eps_degrees=0.0035, min_samples=2):
        self.eps = eps_degrees
        self.min_samples = min_samples

    def run_clustering(self, complaints_data, basis="volume"):
        if basis == "severity":
            return self.run_severity_clustering(complaints_data)
        return self.run_density_clustering(complaints_data)

    def _format_cluster_narrative(self, category, building, complaints):
        """Builds a beautifully formatted executive narrative of the problem root cause and affected facilities."""
        total = len(complaints)
        descs = [c.get("description", "").strip() for c in complaints if c.get("description", "").strip()]
        titles = [c.get("title", "").strip() for c in complaints if c.get("title", "").strip()]
        rooms = list(dict.fromkeys([c.get("room_or_area", "").strip() for c in complaints if c.get("room_or_area", "").strip()]))
        urgencies = [c.get("predicted_urgency", "Medium") for c in complaints]

        has_crit = any(u == "Critical" for u in urgencies)
        crit_count = sum(1 for u in urgencies if u == "Critical")
        high_count = sum(1 for u in urgencies if u == "High")

        room_str = f" in {', '.join(rooms[:3])}" if rooms else ""
        if has_crit:
            header = f"🚨 Critical {category} Hazard ({crit_count} Critical, {high_count} High)"
        elif high_count > 0:
            header = f"🔥 High Priority {category} Outage ({high_count} Urgent Reports)"
        else:
            header = f"⚡ {total} Concurrent {category} Reports"

        # Unique summaries of the issues
        unique_issues = []
        for c in complaints:
            t = c.get("title", "").strip()
            r = c.get("room_or_area", "").strip()
            u = c.get("predicted_urgency", "Medium")
            d = c.get("description", "").strip()
            entry = f"[{u}] {t}" + (f" ({r})" if r else "")
            if d and d != t:
                d_snip = d if len(d) <= 220 else (d[:217] + "...")
                entry += f": {d_snip}"
            if entry not in unique_issues:
                unique_issues.append(entry)

        issues_summary = " • ".join(unique_issues[:3]) if unique_issues else (descs[0] if descs else f"{category} facility failure reported.")
        return f"{header}{room_str} — {issues_summary}"

    def _build_complaint_items(self, complaints):
        items = []
        for c in complaints:
            items.append({
                "id": c.get("id"),
                "title": c.get("title", "Issue"),
                "description": c.get("description", "No description"),
                "room": c.get("room_or_area", "General Area"),
                "category": c.get("category", "General"),
                "urgency": c.get("predicted_urgency", "Medium"),
                "student_name": c.get("student_name") or "Student",
                "status": c.get("status", "Submitted"),
                "created_at": c.get("created_at", "")
            })
        return items

    def run_density_clustering(self, complaints_data):
        if not complaints_data:
            return {"basis": "volume", "clusters": [], "noise_ids": []}

        # 1. Coordinate preparation
        coords = []
        for c in complaints_data:
            lat = c.get("geo_lat")
            lon = c.get("geo_long")
            if lat is None or lon is None:
                b_lat, b_lon = get_building_coords(c.get("building", ""), c.get("college_name"))
                lat, lon = b_lat, b_lon
            coords.append([lat, lon])

        X = np.array(coords)
        clusters = []
        clustered_indices = set()

        # 2. Run DBSCAN Spatial Proximity Clustering if 2 or more points
        if len(complaints_data) >= 2:
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="euclidean")
            labels = db.fit_predict(X)

            unique_labels = set(labels)
            for label in unique_labels:
                if label == -1:
                    continue

                member_indices = [idx for idx, l in enumerate(labels) if l == label]
                clustered_indices.update(member_indices)
                cluster_complaints = [complaints_data[idx] for idx in member_indices]

                buildings = [c.get("building", "Campus Facility") for c in cluster_complaints]
                categories = [c.get("category", "General") for c in cluster_complaints]
                urgencies = [c.get("predicted_urgency", "Medium") for c in cluster_complaints]

                common_building = max(set(buildings), key=buildings.count)
                common_category = max(set(categories), key=categories.count)
                color_code = get_category_color(common_category)

                has_emergency = any(u == "Critical" for u in urgencies) or "safety" in common_category.lower()
                if has_emergency:
                    color_code = "#ef4444"

                crit_count = sum(1 for u in urgencies if u == "Critical")
                high_count = sum(1 for u in urgencies if u == "High")
                med_count = sum(1 for u in urgencies if u == "Medium")
                low_count = sum(1 for u in urgencies if u == "Low")

                scores = [SEVERITY_WEIGHTS.get(u, 0.5) for u in urgencies]
                hazard_score = round(sum(scores) / len(scores), 2)

                centroid = X[member_indices].mean(axis=0).tolist()
                full_narrative = self._format_cluster_narrative(common_category, common_building, cluster_complaints)
                cluster_name = f"{common_building} • {common_category} Hotspot ({len(cluster_complaints)} Reports)"

                clusters.append({
                    "cluster_name": cluster_name,
                    "basis": "Volume / Spatial Density",
                    "building": common_building,
                    "category": common_category,
                    "centroid_lat": round(centroid[0], 5),
                    "centroid_long": round(centroid[1], 5),
                    "complaint_ids": [c.get("id") for c in cluster_complaints],
                    "count": len(cluster_complaints),
                    "total_reports": len(cluster_complaints),
                    "critical_count": crit_count,
                    "high_count": high_count,
                    "medium_count": med_count,
                    "low_count": low_count,
                    "is_emergency": has_emergency,
                    "hazard_score": hazard_score,
                    "titles": [c.get("title", "") for c in cluster_complaints][:6],
                    "problem_description": full_narrative,
                    "sample_description": full_narrative,
                    "complaint_items": self._build_complaint_items(cluster_complaints),
                    "urgencies": list(set(urgencies)),
                    "severity_label": "🚨 Critical Hotspot" if has_emergency else f"⚡ High Volume ({len(cluster_complaints)} Reports)",
                    "color_code": color_code
                })

        # 3. Facility Co-Occurrence Check for unclustered complaints:
        # If any building has 2 or more open complaints that weren't captured by DBSCAN, group them!
        unclustered = [complaints_data[idx] for idx in range(len(complaints_data)) if idx not in clustered_indices]
        building_groups = {}
        for c in unclustered:
            b = c.get("building", "General Campus Area")
            if b not in building_groups:
                building_groups[b] = []
            building_groups[b].append(c)

        for b_name, b_comps in building_groups.items():
            if len(b_comps) >= 2:
                categories = [c.get("category", "General") for c in b_comps]
                urgencies = [c.get("predicted_urgency", "Medium") for c in b_comps]
                dom_cat = max(set(categories), key=categories.count)
                color_code = "#ef4444" if any(u == "Critical" for u in urgencies) else get_category_color(dom_cat)

                col_name = b_comps[0].get("college_name")
                b_lat, b_lon = get_building_coords(b_name, col_name)
                full_narrative = self._format_cluster_narrative(dom_cat, b_name, b_comps)
                has_emergency = any(u == "Critical" for u in urgencies)

                crit_count = sum(1 for u in urgencies if u == "Critical")
                high_count = sum(1 for u in urgencies if u == "High")
                med_count = sum(1 for u in urgencies if u == "Medium")
                low_count = sum(1 for u in urgencies if u == "Low")
                scores = [SEVERITY_WEIGHTS.get(u, 0.5) for u in urgencies]
                hazard_score = round(sum(scores) / len(scores), 2)

                clusters.append({
                    "cluster_name": f"{b_name} • {dom_cat} Facility Hotspot ({len(b_comps)} Reports)",
                    "basis": "Facility Incident Hotspot",
                    "building": b_name,
                    "category": dom_cat,
                    "centroid_lat": round(b_lat, 5),
                    "centroid_long": round(b_lon, 5),
                    "complaint_ids": [c.get("id") for c in b_comps],
                    "count": len(b_comps),
                    "total_reports": len(b_comps),
                    "critical_count": crit_count,
                    "high_count": high_count,
                    "medium_count": med_count,
                    "low_count": low_count,
                    "is_emergency": has_emergency,
                    "hazard_score": hazard_score,
                    "titles": [c.get("title", "") for c in b_comps][:6],
                    "problem_description": full_narrative,
                    "sample_description": full_narrative,
                    "complaint_items": self._build_complaint_items(b_comps),
                    "urgencies": list(set(urgencies)),
                    "severity_label": "🚨 Critical Hotspot" if has_emergency else f"⚡ High Volume ({len(b_comps)} Reports)",
                    "color_code": color_code
                })
                # Mark as clustered
                for c in b_comps:
                    unclustered.remove(c)

        # 4. Critical Emergency Elevation: If an isolated complaint is CRITICAL, don't drop it as noise!
        for c in unclustered:
            if c.get("predicted_urgency") == "Critical":
                b_name = c.get("building", "General Campus Area")
                col_name = c.get("college_name")
                b_lat, b_lon = get_building_coords(b_name, col_name)
                cat = c.get("category", "Emergency")

                clusters.append({
                    "cluster_name": f"{b_name} • 🚨 CRITICAL HAZARD BEACON",
                    "basis": "Emergency Urgency Hotspot",
                    "building": b_name,
                    "category": cat,
                    "centroid_lat": round(c.get("geo_lat") or b_lat, 5),
                    "centroid_long": round(c.get("geo_long") or b_lon, 5),
                    "complaint_ids": [c.get("id")],
                    "count": 1,
                    "total_reports": 1,
                    "critical_count": 1,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0,
                    "is_emergency": True,
                    "hazard_score": 1.0,
                    "titles": [c.get("title", "")],
                    "problem_description": f"🚨 URGENT HAZARD BEACON in {b_name} ({c.get('room_or_area', 'Facility')}): {c.get('description', c.get('title', ''))}",
                    "sample_description": c.get("description", ""),
                    "complaint_items": self._build_complaint_items([c]),
                    "urgencies": ["Critical"],
                    "severity_label": "🚨 IMMEDIATE ACTION REQUIRED",
                    "color_code": "#ef4444"
                })

        clusters.sort(key=lambda x: (x["is_emergency"], x["count"]), reverse=True)

        return {
            "basis": "volume",
            "clusters": clusters,
            "noise_ids": [c.get("id") for c in unclustered if c.get("predicted_urgency") != "Critical"]
        }

    def run_severity_clustering(self, complaints_data):
        if not complaints_data:
            return {"basis": "severity", "clusters": [], "noise_ids": []}

        building_groups = {}
        for c in complaints_data:
            b = c.get("building", "Campus Facility")
            if b not in building_groups:
                building_groups[b] = []
            building_groups[b].append(c)

        severity_clusters = []

        for building_name, comps in building_groups.items():
            total_tickets = len(comps)
            if total_tickets == 0:
                continue

            scores = [SEVERITY_WEIGHTS.get(c.get("predicted_urgency", "Medium"), 0.5) for c in comps]
            avg_hazard = sum(scores) / total_tickets
            crit_count = sum(1 for c in comps if c.get("predicted_urgency") == "Critical")
            high_count = sum(1 for c in comps if c.get("predicted_urgency") == "High")
            med_count = sum(1 for c in comps if c.get("predicted_urgency") == "Medium")
            low_count = sum(1 for c in comps if c.get("predicted_urgency") == "Low")

            dominant_category = max(set(c.get("category", "General") for c in comps), key=[c.get("category") for c in comps].count)

            if crit_count > 0 or avg_hazard >= 0.8:
                severity_level = "🚨 CRITICAL HAZARD BEACON"
                color_code = "#ef4444"
                is_emergency = True
            elif high_count > 0 or avg_hazard >= 0.6:
                severity_level = "🔥 HIGH RISK ZONE"
                color_code = "#f97316"
                is_emergency = True
            elif avg_hazard >= 0.4:
                severity_level = "⚠️ MODERATE PRIORITY"
                color_code = get_category_color(dominant_category)
                is_emergency = False
            else:
                severity_level = "ℹ️ ROUTINE MAINTENANCE"
                color_code = "#10b981"
                is_emergency = False

            full_narrative = self._format_cluster_narrative(dominant_category, building_name, comps)
            col_name = comps[0].get("college_name") if comps else None
            b_lat, b_lon = get_building_coords(building_name, col_name)
            cluster_name = f"{building_name} • {severity_level} ({total_tickets} Reports, Hazard: {avg_hazard:.2f})"

            severity_clusters.append({
                "cluster_name": cluster_name,
                "basis": "Severity / Hazard Index",
                "building": building_name,
                "category": dominant_category,
                "centroid_lat": b_lat,
                "centroid_long": b_lon,
                "complaint_ids": [c.get("id") for c in comps],
                "count": total_tickets,
                "total_reports": total_tickets,
                "critical_count": crit_count,
                "high_count": high_count,
                "medium_count": med_count,
                "low_count": low_count,
                "is_emergency": is_emergency,
                "hazard_score": round(avg_hazard, 2),
                "titles": [c.get("title", "") for c in comps][:6],
                "problem_description": full_narrative,
                "sample_description": full_narrative,
                "complaint_items": self._build_complaint_items(comps),
                "severity_label": severity_level,
                "color_code": color_code
            })

        severity_clusters.sort(key=lambda x: x["hazard_score"], reverse=True)

        return {
            "basis": "severity",
            "clusters": severity_clusters,
            "noise_ids": []
        }

dbscan_clusterer = DualBasisComplaintClusterer()
