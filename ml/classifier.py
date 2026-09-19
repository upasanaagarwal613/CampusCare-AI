import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Curated campus dataset with broad multi-domain coverage including Civil & Structural
CAMPUS_TRAINING_DATA = [
    # Electrical
    ("Power outage in room 302, entire circuit tripped", "Electrical"),
    ("Sparks coming out of the electrical outlet near the desk", "Electrical"),
    ("Electrical switchboard is sparking and wires are exposed dangerously", "Electrical"),
    ("Ceiling fan not working and making buzzing sound", "Electrical"),
    ("Tube light flickering constantly in study hall", "Electrical"),
    ("Switch board is loose and wires are exposed dangerously", "Electrical"),
    ("No electricity in 3rd floor wing of hostel block A", "Electrical"),
    ("Main circuit breaker keeps tripping when plugging in laptop", "Electrical"),
    ("Study lamp socket burnt and smelling like burning plastic", "Electrical"),
    ("Corridor lights completely dark at night", "Electrical"),
    ("Emergency backup generator not kicking in for lab computers", "Electrical"),
    ("Switchboard sparking with electrical short circuit", "Electrical"),
    ("Power socket burnt and dead", "Electrical"),

    # Plumbing
    ("Severe water pipe leakage under the bathroom sink", "Plumbing"),
    ("Water pipe is leaking under the basin", "Plumbing"),
    ("Toilet flush is completely broken and overflowing onto floor", "Plumbing"),
    ("The toilet is blocked and water won't flush down", "Plumbing"),
    ("Bathroom drain is blocked with standing water", "Plumbing"),
    ("No running water in the morning in hostel wing B", "Plumbing"),
    ("Shower drain is clogged with standing stagnant water", "Plumbing"),
    ("Drinking water dispenser tap is leaking continuously", "Plumbing"),
    ("Water pressure is extremely low on the 4th floor", "Plumbing"),
    ("Sewage drain backflow smelling terrible in ground floor restroom", "Plumbing"),
    ("Rusty brown water coming from taps", "Plumbing"),
    ("Water pipe has burst and the bathroom is flooding", "Plumbing"),
    ("Burst pipe spraying water across corridor", "Plumbing"),
    ("Hot water geyser not heating water at all", "Plumbing"),
    ("Washbasin tap continuously dripping water", "Plumbing"),

    # HVAC
    ("The AC is not cooling the classroom properly", "HVAC"),
    ("Air conditioner not cooling and blowing warm air", "HVAC"),
    ("Air conditioner in room 204 blowing hot air instead of cold", "HVAC"),
    ("AC thermostat display is dead and unit won't turn on", "HVAC"),
    ("AC unit leaking water dripping onto study table", "HVAC"),
    ("AC is not cooling, room is suffocating and humid", "HVAC"),
    ("AC won't turn on and remote is dead", "HVAC"),
    ("Severe burning smell coming from ventilation duct", "HVAC"),
    ("Room heating not working in cold winter night", "HVAC"),
    ("Extremely loud rattling noise from centralized HVAC vent", "HVAC"),
    ("Classroom AC remote missing or receiver unresponsive", "HVAC"),
    ("Chilled air not circulating, central air conditioner blower broken", "HVAC"),

    # Internet & IT
    ("The campus internet is down, cannot connect to WiFi or portal", "Internet & IT"),
    ("Internet connection completely down across dorms", "Internet & IT"),
    ("Campus WiFi hostel router offline, no signal in dorm", "Internet & IT"),
    ("Ethernet wall port LAN cable not detecting connection", "Internet & IT"),
    ("Captive portal login loop failing with DNS error", "Internet & IT"),
    ("Extremely slow internet speeds under 100kbps during exam submission", "Internet & IT"),
    ("Access point rebooting every 5 minutes in library", "Internet & IT"),
    ("Cannot connect to eduroam or student network SSID", "Internet & IT"),
    ("Lab computer switches disconnected from campus server", "Internet & IT"),
    ("Smart projector in seminar hall not displaying HDMI or WiFi feed", "Internet & IT"),
    ("Audio mic system feedback and speaker failure in auditorium", "Internet & IT"),

    # Carpentry & Furniture
    ("The classroom chair is broken and wobbling dangerously", "Carpentry & Furniture"),
    ("The classroom door is broken and won't shut or lock", "Carpentry & Furniture"),
    ("Broken chair in study room needs repair or replacement", "Carpentry & Furniture"),
    ("Room door lock cylinder jammed, key got stuck inside", "Carpentry & Furniture"),
    ("Wooden window latch broken, window banging in high wind", "Carpentry & Furniture"),
    ("Study chair leg snapped, unsafe to sit on", "Carpentry & Furniture"),
    ("Bunk bed frame loose and squeaking dangerously", "Carpentry & Furniture"),
    ("Wardrobe closet hinge broken, door hanging off", "Carpentry & Furniture"),
    ("Study table surface cracked with sharp splinters", "Carpentry & Furniture"),
    ("Balcony door sliding track blocked and jammed", "Carpentry & Furniture"),
    ("Bookshelf collapsed off the wall bracket", "Carpentry & Furniture"),
    ("Classroom bench wood detached and nails sticking out", "Carpentry & Furniture"),

    # Sanitation & Cleaning
    ("Overflowing garbage bins outside hostel entrance attracting insects", "Sanitation & Cleaning"),
    ("Bathroom hasn't been cleaned in days, unhygienic condition", "Sanitation & Cleaning"),
    ("Pest infestation with cockroaches in pantry cupboard", "Sanitation & Cleaning"),
    ("Spilled chemical or liquid residue on staircase floor", "Sanitation & Cleaning"),
    ("Foul odor from compost bin near dining hall", "Sanitation & Cleaning"),
    ("Dust and debris all over hallway after maintenance work", "Sanitation & Cleaning"),
    ("Soap dispensers empty and paper towels missing in all restrooms", "Sanitation & Cleaning"),
    ("Stray animal mess in corridor needs immediate sanitization", "Sanitation & Cleaning"),

    # Safety, Fire & Security
    ("Fire extinguisher pressure gauge empty in science block", "Safety & Security"),
    ("Emergency exit door locked or chained shut unlawfully", "Safety & Security"),
    ("CCTV camera angle blinded or wire severed outside dorm", "Safety & Security"),
    ("Smoke alarm chirping continuously or broken sensor", "Safety & Security"),
    ("Main gate biometric turnstile access reader malfunctioning", "Safety & Security"),
    ("Chemical fume hood alarm sounding in chemistry research lab", "Safety & Security"),

    # Civil & Structural
    ("The ceiling has a structural crack expanding across the room", "Civil & Structural"),
    ("The roof is leaking during rain, rainwater seeping into ceiling", "Civil & Structural"),
    ("The wall has developed a large crack and plaster falling", "Civil & Structural"),
    ("The classroom floor tiles are broken and cracked", "Civil & Structural"),
    ("Structural cracks appearing on hostel building pillars", "Civil & Structural"),
    ("Roof damage causing rainwater leaking through slab in library", "Civil & Structural"),
    ("Broken floor tiles causing tripping hazard on stairs", "Civil & Structural"),
    ("Damaged flooring and broken marble tiles in hallway", "Civil & Structural"),
    ("Masonry work crumbling and wall plaster peeling off", "Civil & Structural"),
    ("Building structure concrete spalling with rebar visible", "Civil & Structural"),
    ("Pothole on main campus walkway near student activity center", "Civil & Structural"),
    ("Civil repair needed for cracked concrete stairs and boundary wall", "Civil & Structural"),
    ("Roof leakage during heavy rain flooding top floor rooms", "Civil & Structural"),
    ("Door frame masonry cracked and crumbling away from wall", "Civil & Structural"),

    # Elevator & Mechanical
    ("Hostel elevator stuck between 2nd and 3rd floors with passengers", "Elevator & Mechanical"),
    ("Lift buttons unresponsive and lift car vibrating severely", "Elevator & Mechanical"),
    ("Water pump motor in basement making screeching loud noise", "Elevator & Mechanical"),
    ("Elevator breakdown door not opening on ground floor", "Elevator & Mechanical"),

    # Lab Equipment & Research
    ("Oscilloscope power supply blown in electronics laboratory", "Lab Equipment"),
    ("Centrifuge machine unbalanced and shaking violently", "Lab Equipment"),
    ("Autoclave steam pressure valve not sealing properly", "Lab Equipment"),
    ("Microscope lens stage loose and coarse adjustment stripped", "Lab Equipment"),
]

# Required specialty skill mapping per category
CATEGORY_SKILLS = {
    "Electrical": "Licensed Electrician / Power Systems",
    "Plumbing": "Plumbing & Hydraulics Specialist",
    "HVAC": "HVAC & Climate Control Specialist",
    "Internet & IT": "Network & IT Support Specialist",
    "Carpentry & Furniture": "Carpentry & Hardware Technician",
    "Sanitation & Cleaning": "Sanitation & Hygiene Services",
    "Safety & Security": "Safety & Security Operations",
    "Civil & Structural": "Civil & Structural Masonry Specialist",
    "Elevator & Mechanical": "Mechanical & Elevator Maintenance",
    "Lab Equipment": "Laboratory Systems Specialist",
    "General Maintenance": "General Facility Maintenance"
}

# Suggested actionable guidance for students
CATEGORY_ACTIONS = {
    "Electrical": "Keep distance from affected wiring/switches; certified electrician dispatched.",
    "Plumbing": "Avoid using connected fixtures; plumbing technician alerted for water stoppage.",
    "HVAC": "Keep room ventilated; HVAC technician scheduled for climate inspection.",
    "Internet & IT": "IT gateway diagnostics running; network engineer reviewing AP status.",
    "Carpentry & Furniture": "Item marked for repair; carpenter assigned for fixture service.",
    "Sanitation & Cleaning": "Custodial staff notified for rapid cleanup and sanitation.",
    "Safety & Security": "Campus safety operations notified for immediate verification.",
    "Civil & Structural": "Avoid standing directly beneath affected area; civil engineers alerted.",
    "Elevator & Mechanical": "Elevator safety protocols engaged; lift mechanics responding.",
    "Lab Equipment": "Power off equipment safely; lab custodian technician notified.",
    "General Maintenance": "Work order created for facilities inspection."
}

# Urgency detection patterns with context
CRITICAL_PATTERNS = [
    r"\bburst(?:\s+pipe)?\b", r"\bpipe\s+burst\b", r"\bsparks?\b", r"\bsparking\b",
    r"\bburning\b", r"\bfire\b", r"\bsmoke\b", r"\bfloods?\b", r"\bflooding\b",
    r"\boverflowing\b", r"\bhazard\b", r"\bemergency\b", r"\bexposed\s+wires?\b",
    r"\bwires?\s+(?:are\s+)?exposed\b", r"\bdanger(?:ous)?\b", r"\belectric\s+shock\b",
    r"\bgas\s+smell\b", r"\bgas\s+leak\b", r"\bstuck\s+inside\b", r"\bpassengers?\b",
    r"\bshaking\s+violently\b", r"\bmajor\s+leakage\b", r"\bunsafe\b", r"\bsos\b", r"\bcollapse\b"
]

HIGH_PATTERNS = [
    r"\bmalfunctioning\b", r"\bnot\s+functioning\b", r"\bwon'?t\s+turn\s+on\b",
    r"\bnot\s+working\b", r"\bnot\s+cooling\b", r"\bno\s+cooling\b", r"\bno\s+water\b",
    r"\bno\s+electricity\b", r"\boutage\b", r"\bblackout\b", r"\bjammed\b", r"\bstuck\b",
    r"\bbroken\b", r"\bexam\b", r"\bsevere\b", r"\bleaking\s+continuously\b",
    r"\bpest\s+infestation\b", r"\bextinguisher\b", r"\burgent\b", r"\bblocked\b"
]

MEDIUM_PATTERNS = [
    r"\bflickering\b", r"\bslow\b", r"\bclogged\b", r"\bsmell\b", r"\bloose\b",
    r"\brattling\b", r"\bnoisy\b", r"\bempty\b", r"\bdirty\b", r"\bcrack(?:ed)?\b",
    r"\btripped\b", r"\bseepage\b", r"\bdamaged\b", r"\bhumid\b", r"\bleaking\b",
    r"\bleak\b", r"\bleakage\b", r"\bdown\b"
]



class ComplaintClassifier:
    def __init__(self):
        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english", lowercase=True)),
            ("clf", MultinomialNB(alpha=0.1))
        ])
        self.is_trained = False
        self._train()

    def _train(self):
        texts = [item[0] for item in CAMPUS_TRAINING_DATA]
        labels = [item[1] for item in CAMPUS_TRAINING_DATA]
        self.model.fit(texts, labels)
        self.is_trained = True

    def classify(self, title: str, description: str):
        full_text = f"{title} {description}".strip()
        if not full_text:
            return {
                "predicted_category": "General Maintenance",
                "confidence_score": 0.5,
                "confidence_level": "Low confidence",
                "predicted_urgency": "Medium",
                "urgency_score": 0.5,
                "keywords_matched": [],
                "required_skill": CATEGORY_SKILLS["General Maintenance"],
                "suggested_action": CATEGORY_ACTIONS["General Maintenance"]
            }

        # Predict category and confidence
        probs = self.model.predict_proba([full_text])[0]
        classes = self.model.classes_
        best_idx = np.argmax(probs)
        predicted_category = str(classes[best_idx])
        raw_confidence = float(probs[best_idx])

        lower_text = full_text.lower()

        # Context-aware heuristics to prevent misclassification of key problem types
        # 1. Civil & Structural check (takes precedence when roof, ceiling, wall crack, floor tiles, masonry mentioned)
        has_civil_indicators = any(term in lower_text for term in [
            "structural crack", "structure crack", "ceiling crack", "wall crack", "floor tile", "floor tiles",
            "tiles are broken", "broken tile", "broken tiles", "damaged floor", "damaged flooring", "roof damage",
            "roof is leaking", "roof leaking", "roof leakage", "leaking during rain", "leaking through roof",
            "plaster falling", "concrete", "masonry", "pothole", "structural", "civil repair"
        ])
        if has_civil_indicators:
            # Differentiate roof leakage / ceiling damage from purely plumbing fixtures
            is_pure_plumbing_fixture = any(p in lower_text for p in ["toilet", "flush", "sink", "geyser", "tap", "shower drain", "sewage"])
            if not is_pure_plumbing_fixture:
                predicted_category = "Civil & Structural"
                raw_confidence = max(raw_confidence, 0.78)

        # 2. Obvious Category Heuristics & Fallbacks (protects common student phrasing)
        if any(term in lower_text for term in ["toilet", "blocked drain", "drain is blocked", "water pipe", "flush broken", "bathroom drain", "tap dripping", "sewage"]):
            if "ac" not in lower_text and "roof" not in lower_text:
                predicted_category = "Plumbing"
                raw_confidence = max(raw_confidence, 0.82)
        elif any(term in lower_text for term in ["sparking", "sparks", "switchboard", "exposed wire", "exposed wires", "power outage", "short circuit", "circuit breaker", "electric shock"]):
            predicted_category = "Electrical"
            raw_confidence = max(raw_confidence, 0.82)
        elif any(term in lower_text for term in ["not cooling", "no cooling", "air conditioner", "ac unit", "thermostat", "central ac", "blowing hot air"]):
            predicted_category = "HVAC"
            raw_confidence = max(raw_confidence, 0.82)
        elif any(term in lower_text for term in ["internet is down", "campus internet", "wifi offline", "wifi down", "no wifi", "router offline", "eduroam"]):
            predicted_category = "Internet & IT"
            raw_confidence = max(raw_confidence, 0.82)
        elif any(term in lower_text for term in ["chair is broken", "broken chair", "broken door", "door is broken", "window latch", "desk broken", "bunk bed", "cupboard"]):
            if not has_civil_indicators:
                predicted_category = "Carpentry & Furniture"
                raw_confidence = max(raw_confidence, 0.82)

        # 3. Dynamic fallback for very low confidence edge cases
        if raw_confidence < 0.35:
            if any(k in lower_text for k in ["wire", "switch", "bulb", "fan", "current", "voltage", "fuse", "spark"]):
                predicted_category = "Electrical"
            elif any(k in lower_text for k in ["pipe", "tap", "sink", "flush", "water", "drain", "leak"]):
                predicted_category = "Plumbing"
            elif any(k in lower_text for k in ["cool", "hot", "air", "filter", "ac", "vent", "thermostat"]):
                predicted_category = "HVAC"
            elif any(k in lower_text for k in ["net", "wifi", "router", "lan", "cable", "port", "internet"]):
                predicted_category = "Internet & IT"
            elif any(k in lower_text for k in ["fire", "hazard", "cctv", "security", "guard", "alarm", "danger"]):
                predicted_category = "Safety & Security"
            elif any(k in lower_text for k in ["lift", "elevator", "motor", "pump"]):
                predicted_category = "Elevator & Mechanical"
            elif any(k in lower_text for k in ["bench", "chair", "table", "lock", "door", "hinge", "bed"]):
                predicted_category = "Carpentry & Furniture"
            elif any(k in lower_text for k in ["clean", "dustbin", "trash", "garbage", "roach", "smell"]):
                predicted_category = "Sanitation & Cleaning"
            elif any(k in lower_text for k in ["structural", "crack", "roof", "masonry", "tile", "plaster", "concrete"]):
                predicted_category = "Civil & Structural"
            elif any(k in lower_text for k in ["lab", "sensor", "circuit", "scope", "device", "meter"]):
                predicted_category = "Lab Equipment"

        # Honest confidence calculation — do not force 0.5 floor
        confidence_score = round(raw_confidence, 2)
        if confidence_score >= 0.80:
            confidence_level = "High confidence"
        elif confidence_score >= 0.60:
            confidence_level = "Medium confidence"
        else:
            confidence_level = "Low confidence"

        # Urgency pattern matching
        matched_crit = []
        for pat in CRITICAL_PATTERNS:
            found = re.findall(pat, lower_text)
            if found:
                matched_crit.extend(found)

        matched_high = []
        for pat in HIGH_PATTERNS:
            found = re.findall(pat, lower_text)
            if found:
                matched_high.extend(found)

        matched_med = []
        for pat in MEDIUM_PATTERNS:
            found = re.findall(pat, lower_text)
            if found:
                matched_med.extend(found)

        # De-duplicate matches while preserving order
        unique_matches = []
        for m in (matched_crit + matched_high + matched_med):
            if m not in unique_matches:
                unique_matches.append(m)

        if matched_crit:
            urgency = "Critical"
            urgency_score = min(0.98, 0.85 + (len(set(matched_crit)) * 0.05))
        elif matched_high:
            urgency = "High"
            urgency_score = min(0.80, 0.65 + (len(set(matched_high)) * 0.05))
        elif matched_med:
            urgency = "Medium"
            urgency_score = 0.50
        else:
            urgency = "Low"
            urgency_score = 0.30

        return {
            "predicted_category": predicted_category,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "predicted_urgency": urgency,
            "urgency_score": round(urgency_score, 2),
            "keywords_matched": unique_matches,
            "required_skill": CATEGORY_SKILLS.get(predicted_category, "Facility Maintenance"),
            "suggested_action": CATEGORY_ACTIONS.get(predicted_category, "Review issue details and dispatch provider.")
        }

nlp_classifier = ComplaintClassifier()

