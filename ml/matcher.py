class ProviderMatcher:
    """
    Explainable scoring algorithm for matching campus complaints with the best service providers.
    Uses multi-criteria decision scoring with transparent point breakdowns:
    1. Specialty & Qualification Match (Max 40 pts)
    2. Availability & Queue Bandwidth (Max 25 pts)
    3. Rating & Track Record (Max 20 pts)
    4. Proximity, Zone & Campus Affiliation (Max 15 pts)
    """

    ZONE_MAPPINGS = {
        "Hostel Block A": "Hostel Zone",
        "Hostel Block B": "Hostel Zone",
        "Dining Center": "Hostel Zone",
        "Sports Complex": "Hostel Zone",
        "Library Building": "Academic Zone",
        "Central Library": "Academic Zone",
        "Engineering Hall": "Academic Zone",
        "Science Complex": "Academic Zone",
        "Administrative Block": "Central Zone",
    }

    def score_provider(self, provider_dict, complaint_dict):
        category = complaint_dict.get("category", "")
        building = complaint_dict.get("building", "")
        c_college = (complaint_dict.get("college_name") or "").strip().lower()
        complaint_zone = self.ZONE_MAPPINGS.get(building, "Central Zone")

        p_category = provider_dict.get("service_category", "")
        p_specialties = provider_dict.get("specialties", [])
        p_skills = provider_dict.get("skills", [])
        p_rating = provider_dict.get("rating", 5.0)
        p_active_jobs = provider_dict.get("active_jobs_count", 0)
        p_available = provider_dict.get("is_available", True)
        p_zone = provider_dict.get("location_zone", "")
        p_college = (provider_dict.get("college_name") or "").strip().lower()

        breakdown = {}

        # 1. Category & Specialty Match (Max 40 pts)
        if not p_available:
            category_score = 0
            breakdown["category"] = {
                "score": 0, "max": 40, "reason": "Provider is marked unavailable / off-duty"
            }
        else:
            cat_lower = category.lower()
            all_specs = [s.lower() for s in p_specialties] + [s.lower() for s in p_skills]
            p_cat_lower = p_category.lower()

            is_match = (
                cat_lower in p_cat_lower or 
                p_cat_lower in cat_lower or 
                any(cat_lower in s or s in cat_lower for s in all_specs)
            )

            if is_match:
                category_score = 40
                breakdown["category"] = {
                    "score": 40, "max": 40, "reason": f"Verified specialty qualification for '{category}'"
                }
            else:
                category_score = 8
                breakdown["category"] = {
                    "score": 8, "max": 40, "reason": "Cross-disciplinary generalist technician fallback"
                }

        # 2. Availability & Workload (Max 25 pts)
        if not p_available:
            workload_score = 0
            breakdown["workload"] = {"score": 0, "max": 25, "reason": "Currently off-duty"}
        elif p_active_jobs == 0:
            workload_score = 25
            breakdown["workload"] = {"score": 25, "max": 25, "reason": "Immediate bandwidth (0 active orders)"}
        elif p_active_jobs == 1:
            workload_score = 18
            breakdown["workload"] = {"score": 18, "max": 25, "reason": "Light workload (1 active job)"}
        elif p_active_jobs == 2:
            workload_score = 10
            breakdown["workload"] = {"score": 10, "max": 25, "reason": "Moderate queue (2 active jobs)"}
        else:
            workload_score = 2
            breakdown["workload"] = {"score": 2, "max": 25, "reason": f"High queue ({p_active_jobs} active jobs)"}

        # 3. Rating & Track Record (Max 20 pts)
        rating_score = round((min(p_rating, 5.0) / 5.0) * 20.0, 1)
        breakdown["rating"] = {
            "score": rating_score,
            "max": 20,
            "reason": f"Student performance rating ({p_rating:.1f}/5.0)"
        }

        # 4. Proximity, Zone & Campus Match (Max 15 pts)
        zone_score = 0
        campus_bonus = 5 if (not c_college or not p_college or c_college == p_college) else 0

        if p_zone and (p_zone == complaint_zone or p_zone == "Campus-Wide"):
            zone_score = 10 + campus_bonus
            breakdown["zone"] = {
                "score": zone_score, "max": 15, "reason": f"Stationed in target zone ({complaint_zone}) on campus"
            }
        elif not p_zone:
            zone_score = 7 + campus_bonus
            breakdown["zone"] = {
                "score": zone_score, "max": 15, "reason": "General campus coverage"
            }
        else:
            zone_score = 3 + campus_bonus
            breakdown["zone"] = {
                "score": zone_score, "max": 15, "reason": f"Located in {p_zone} (requires inter-zone transit)"
            }

        total_score = round(min(100, category_score + workload_score + rating_score + zone_score), 1)

        if total_score >= 80:
            recommendation = "Optimal Match (Auto-Dispatch)"
        elif total_score >= 60:
            recommendation = "Suitable Match"
        else:
            recommendation = "Low Compatibility"

        return {
            "provider_id": provider_dict.get("id"),
            "provider_name": provider_dict.get("name"),
            "service_category": p_category,
            "rating": p_rating,
            "active_jobs": p_active_jobs,
            "is_available": p_available,
            "total_score": total_score,
            "recommendation": recommendation,
            "breakdown": breakdown,
        }

    def rank_providers(self, providers_list, complaint_dict):
        scored = [self.score_provider(p, complaint_dict) for p in providers_list]
        scored.sort(key=lambda x: x["total_score"], reverse=True)
        return scored

provider_matcher = ProviderMatcher()
