import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Curated campus dataset with broad multi-domain coverage
CAMPUS_TRAINING_DATA = [
    # Electrical
    ("Power outage in room 302, entire circuit tripped", "Electrical"),
    ("Sparks coming out of the electrical outlet near the desk", "Electrical"),
    ("Ceiling fan not working and making buzzing sound", "Electrical"),
    ("Tube light flickering constantly in study hall", "Electrical"),
    ("Switch board is loose and wires are exposed dangerously", "Electrical"),
    ("No electricity in 3rd floor wing of hostel block A", "Electrical"),
    ("Main circuit breaker keeps tripping when plugging in laptop", "Electrical"),
    ("Study lamp socket burnt and smelling like burning plastic", "Electrical"),
    ("Corridor lights completely dark at night", "Electrical"),
    ("Emergency backup generator not kicking in for lab computers", "Electrical"),

    # Plumbing
    ("Severe water pipe leakage under the bathroom sink", "Plumbing"),
    ("Toilet flush is completely broken and overflowing onto floor", "Plumbing"),
    ("No running water in the morning in hostel wing B", "Plumbing"),
    ("Shower drain is clogged with standing stagnant water", "Plumbing"),
    ("Drinking water dispenser tap is leaking continuously", "Plumbing"),
    ("Water pressure is extremely low on the 4th floor", "Plumbing"),
    ("Sewage drain backflow smelling terrible in ground floor restroom", "Plumbing"),
    ("Rusty brown water coming from taps", "Plumbing"),
    ("Burst pipe spraying water across corridor", "Plumbing"),
    ("Hot water geyser not heating water at all", "Plumbing"),

    # HVAC
    ("Air conditioner in room 204 blowing hot air instead of cold", "HVAC"),
    ("AC thermostat display is dead and unit won't turn on", "HVAC"),
    ("AC unit leaking water dripping onto study table", "HVAC"),
    ("Severe burning smell coming from ventilation duct", "HVAC"),
    ("Room heating not working in cold winter night", "HVAC"),
    ("Extremely loud rattling noise from centralized HVAC vent", "HVAC"),
    ("Classroom AC remote missing or receiver unresponsive", "HVAC"),
    ("Chilled air not circulating, room is humid and suffocating", "HVAC"),

    # Internet & IT
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
    ("Room door lock cylinder jammed, key got stuck inside", "Carpentry & Furniture"),
    ("Wooden window latch broken, window banging in high wind", "Carpentry & Furniture"),
    ("Study chair leg snapped, unsafe to sit on", "Carpentry & Furniture"),
    ("Bunk bed frame loose and squeaking dangerously", "Carpentry & Furniture"),
    ("Wardrobe closet hinge broken, door hanging off", "Carpentry & Furniture"),
    ("Study table surface cracked with sharp splinters", "Carpentry & Furniture"),
    ("Balcony door sliding track blocked and jammed", "Carpentry & Furniture"),
    ("Bookshelf collapsed off the wall bracket", "Carpentry & Furniture"),

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
    ("Deep crack expanding on lecture hall ceiling plaster", "Civil & Structural"),
    ("Rainwater seepage leaking through roof in top floor library", "Civil & Structural"),
    ("Broken floor tiles causing tripping hazard on stairs", "Civil & Structural"),
    ("Pothole on main campus walkway near student activity center", "Civil & Structural"),

    # Elevator & Mechanical
    ("Hostel elevator stuck between 2nd and 3rd floors with passengers", "Elevator & Mechanical"),
    ("Lift buttons unresponsive and lift car vibrating severely", "Elevator & Mechanical"),
    ("Water pump motor in basement making screeching loud noise", "Elevator & Mechanical"),

    # Lab Equipment & Research
    ("Oscilloscope power supply blown in electronics laboratory", "Lab Equipment"),
    ("Centrifuge machine unbalanced and shaking violently", "Lab Equipment"),
    ("Autoclave steam pressure valve not sealing properly", "Lab Equipment"),
    ("Microscope lens stage loose and coarse adjustment stripped", "Lab Equipment"),
]

# Severity keywords with explainable urgency score weights
CRITICAL_KEYWORDS = [
    "burst", "sparks", "burning", "fire", "smoke", "flood", "flooding", "overflowing",
    "hazard", "emergency", "exposed wires", "danger", "electric shock", "gas smell",
    "stuck inside", "passengers", "seepage", "fume hood", "shaking violently", "sos"
]

HIGH_KEYWORDS = [
    "urgent", "no water", "outage", "blackout", "jammed", "stuck", "broken", 
    "exam", "collapsed", "severe", "leaking continuously", "pest infestation", "extinguisher"
]

MEDIUM_KEYWORDS = [
    "not working", "flickering", "slow", "clogged", "smell", "loose", "rattling",
    "noisy", "empty", "dirty", "crack", "tripped"
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
                "predicted_urgency": "Medium",
                "urgency_score": 0.5,
                "keywords_matched": [],
            }

        # Predict category and confidence
        probs = self.model.predict_proba([full_text])[0]
        classes = self.model.classes_
        best_idx = np.argmax(probs)
        predicted_category = str(classes[best_idx])
        confidence_score = float(probs[best_idx])

        # Dynamic fallback for new custom problems: keyword heuristics
        lower_text = full_text.lower()
        if confidence_score < 0.35:
            if any(k in lower_text for k in ["wire", "switch", "bulb", "fan", "current", "voltage", "fuse"]):
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
            elif any(k in lower_text for k in ["lab", "sensor", "circuit", "scope", "device", "meter"]):
                predicted_category = "Lab Equipment"

        # Urgency scoring
        matched_crit = [kw for kw in CRITICAL_KEYWORDS if kw in lower_text]
        matched_high = [kw for kw in HIGH_KEYWORDS if kw in lower_text]
        matched_med = [kw for kw in MEDIUM_KEYWORDS if kw in lower_text]

        keywords_matched = matched_crit + matched_high + matched_med

        if matched_crit:
            urgency = "Critical"
            urgency_score = min(0.98, 0.85 + (len(matched_crit) * 0.05))
        elif matched_high:
            urgency = "High"
            urgency_score = min(0.80, 0.65 + (len(matched_high) * 0.05))
        elif matched_med:
            urgency = "Medium"
            urgency_score = 0.50
        else:
            urgency = "Low"
            urgency_score = 0.30

        return {
            "predicted_category": predicted_category,
            "confidence_score": round(max(confidence_score, 0.5), 2),
            "predicted_urgency": urgency,
            "urgency_score": round(urgency_score, 2),
            "keywords_matched": keywords_matched,
        }

nlp_classifier = ComplaintClassifier()
