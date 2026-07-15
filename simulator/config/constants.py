"""
NEXUS Simulator — Karnataka-specific constants and domain vocabulary.
All crime types, IPC sections, MO vocabulary, Kannada name pools,
district names, rank hierarchy, and vehicle prefixes live here.
"""
from __future__ import annotations
from typing import Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# KARNATAKA DISTRICTS (all 31 revenue districts)
# ─────────────────────────────────────────────────────────────────────────────
KARNATAKA_DISTRICTS: List[Dict] = [
    {"id": "KA-BLR", "name": "Bengaluru Urban",    "hq": "Bengaluru",    "type": "metro",      "population_density": "very_high"},
    {"id": "KA-BLR-R","name": "Bengaluru Rural",   "hq": "Bengaluru",    "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-MYS",  "name": "Mysuru",             "hq": "Mysuru",       "type": "urban",      "population_density": "high"},
    {"id": "KA-MGL",  "name": "Dakshina Kannada",   "hq": "Mangaluru",   "type": "urban",      "population_density": "high"},
    {"id": "KA-HBL",  "name": "Hubballi-Dharwad",   "hq": "Hubballi",    "type": "urban",      "population_density": "high"},
    {"id": "KA-BLG",  "name": "Belagavi",            "hq": "Belagavi",    "type": "urban",      "population_density": "medium"},
    {"id": "KA-KLP",  "name": "Kalaburagi",          "hq": "Kalaburagi",  "type": "urban",      "population_density": "medium"},
    {"id": "KA-DVG",  "name": "Davanagere",          "hq": "Davanagere",  "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-SHV",  "name": "Shivamogga",          "hq": "Shivamogga",  "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-TKR",  "name": "Tumakuru",            "hq": "Tumakuru",    "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-RCR",  "name": "Raichur",             "hq": "Raichur",     "type": "semi_urban", "population_density": "low"},
    {"id": "KA-BDR",  "name": "Bidar",               "hq": "Bidar",       "type": "semi_urban", "population_density": "low"},
    {"id": "KA-VJP",  "name": "Vijayapura",          "hq": "Vijayapura",  "type": "semi_urban", "population_density": "low"},
    {"id": "KA-BSD",  "name": "Bagalkote",           "hq": "Bagalkote",   "type": "rural",      "population_density": "low"},
    {"id": "KA-HSN",  "name": "Hassan",              "hq": "Hassan",      "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-CKM",  "name": "Chikkamagaluru",      "hq": "Chikkamagaluru","type": "rural",   "population_density": "low"},
    {"id": "KA-KDG",  "name": "Kodagu",              "hq": "Madikeri",    "type": "rural",      "population_density": "very_low"},
    {"id": "KA-UDR",  "name": "Udupi",               "hq": "Udupi",       "type": "urban",      "population_density": "medium"},
    {"id": "KA-MDY",  "name": "Mandya",              "hq": "Mandya",      "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-CHT",  "name": "Chamarajanagara",     "hq": "Chamarajanagara","type": "rural",  "population_density": "low"},
    {"id": "KA-KLR",  "name": "Kolar",               "hq": "Kolar",       "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-CHB",  "name": "Chikkaballapura",     "hq": "Chikkaballapura","type": "semi_urban","population_density": "medium"},
    {"id": "KA-RMN",  "name": "Ramanagara",          "hq": "Ramanagara",  "type": "semi_urban", "population_density": "medium"},
    {"id": "KA-GBG",  "name": "Gadag",               "hq": "Gadag",       "type": "rural",      "population_density": "low"},
    {"id": "KA-HVR",  "name": "Haveri",              "hq": "Haveri",       "type": "rural",      "population_density": "low"},
    {"id": "KA-KPT",  "name": "Koppal",              "hq": "Koppal",      "type": "rural",      "population_density": "low"},
    {"id": "KA-YDG",  "name": "Yadgir",              "hq": "Yadgir",      "type": "rural",      "population_density": "very_low"},
    {"id": "KA-VKT",  "name": "Vijayanagara",        "hq": "Hosapete",    "type": "semi_urban", "population_density": "low"},
    {"id": "KA-CTV",  "name": "Chitradurga",         "hq": "Chitradurga", "type": "semi_urban", "population_density": "low"},
    {"id": "KA-BLR2", "name": "Ballari",             "hq": "Ballari",     "type": "urban",      "population_density": "medium"},
    {"id": "KA-RBG",  "name": "Dharwad",             "hq": "Dharwad",     "type": "urban",      "population_density": "medium"},
]

# ─────────────────────────────────────────────────────────────────────────────
# CRIME TYPE TAXONOMY
# ─────────────────────────────────────────────────────────────────────────────
CRIME_CATEGORIES: List[Dict] = [
    # Property crimes
    {"id": "THEFT",      "name": "Theft",               "ipc": "379",    "severity": 2, "category": "property", "typical_duration_min": 5,  "typical_duration_max": 30},
    {"id": "BURGLARY",   "name": "House Breaking",       "ipc": "457",    "severity": 3, "category": "property", "typical_duration_min": 15, "typical_duration_max": 90},
    {"id": "ROBBERY",    "name": "Robbery",              "ipc": "392",    "severity": 4, "category": "property", "typical_duration_min": 2,  "typical_duration_max": 15},
    {"id": "DACOITY",    "name": "Dacoity",              "ipc": "395",    "severity": 5, "category": "property", "typical_duration_min": 10, "typical_duration_max": 60},
    {"id": "CHAIN",      "name": "Chain Snatching",      "ipc": "392",    "severity": 3, "category": "property", "typical_duration_min": 1,  "typical_duration_max": 5},
    {"id": "VEH_THEFT",  "name": "Vehicle Theft",        "ipc": "379",    "severity": 2, "category": "property", "typical_duration_min": 5,  "typical_duration_max": 20},
    {"id": "PICK",       "name": "Pickpocketing",        "ipc": "379",    "severity": 1, "category": "property", "typical_duration_min": 1,  "typical_duration_max": 3},
    {"id": "TRESPASS",   "name": "Criminal Trespass",    "ipc": "447",    "severity": 2, "category": "property", "typical_duration_min": 10, "typical_duration_max": 120},
    {"id": "ARSON",      "name": "Arson",                "ipc": "436",    "severity": 4, "category": "property", "typical_duration_min": 5,  "typical_duration_max": 30},
    # Violent crimes
    {"id": "ASSAULT",    "name": "Assault",              "ipc": "324",    "severity": 3, "category": "violent",  "typical_duration_min": 2,  "typical_duration_max": 20},
    {"id": "MURDER",     "name": "Murder",               "ipc": "302",    "severity": 6, "category": "violent",  "typical_duration_min": 5,  "typical_duration_max": 60},
    {"id": "ATTEMPT_M",  "name": "Attempt to Murder",    "ipc": "307",    "severity": 5, "category": "violent",  "typical_duration_min": 5,  "typical_duration_max": 30},
    {"id": "KIDNAP",     "name": "Kidnapping",           "ipc": "363",    "severity": 5, "category": "violent",  "typical_duration_min": 30, "typical_duration_max": 1440},
    {"id": "RIOTING",    "name": "Rioting",              "ipc": "147",    "severity": 4, "category": "violent",  "typical_duration_min": 10, "typical_duration_max": 180},
    # Fraud & cyber
    {"id": "FRAUD",      "name": "Cheating/Fraud",       "ipc": "420",    "severity": 3, "category": "fraud",    "typical_duration_min": 60, "typical_duration_max": 43200},
    {"id": "CYBER",      "name": "Cyber Crime",          "ipc": "66C_IT", "severity": 3, "category": "cyber",    "typical_duration_min": 5,  "typical_duration_max": 1440},
    {"id": "ATM_FRAUD",  "name": "ATM Skimming",         "ipc": "379",    "severity": 3, "category": "cyber",    "typical_duration_min": 10, "typical_duration_max": 60},
    # Drug related
    {"id": "NARCOTICS",  "name": "Drug Trafficking",     "ipc": "NDPS_20","severity": 4, "category": "narcotics","typical_duration_min": 0,  "typical_duration_max": 0},
    {"id": "POSSESS",    "name": "Drug Possession",      "ipc": "NDPS_27","severity": 3, "category": "narcotics","typical_duration_min": 0,  "typical_duration_max": 0},
    # Traffic
    {"id": "HIT_RUN",    "name": "Hit and Run",          "ipc": "304A",   "severity": 4, "category": "traffic",  "typical_duration_min": 1,  "typical_duration_max": 5},
    {"id": "DRUNK_DRV",  "name": "Drunk Driving",        "ipc": "185MV",  "severity": 2, "category": "traffic",  "typical_duration_min": 0,  "typical_duration_max": 0},
]

# ─────────────────────────────────────────────────────────────────────────────
# MODUS OPERANDI VOCABULARY
# ─────────────────────────────────────────────────────────────────────────────
MO_ENTRY_METHODS = ["rear_entry", "window_entry", "front_door", "roof_entry",
                     "tunneling", "fake_delivery", "fake_police", "social_engineering",
                     "digital_access", "open_access", "forced_entry"]

MO_TIME_SLOTS = ["early_morning_0400_0600", "morning_0600_0900",
                  "mid_morning_0900_1200", "afternoon_1200_1600",
                  "evening_1600_1900", "night_1900_2200", "late_night_2200_0400"]

MO_TARGET_TYPES = ["residential_house", "apartment", "shop", "bank", "atm",
                    "school", "temple", "hospital", "market", "street",
                    "bus_stand", "railway_station", "vehicle_parked"]

MO_ESCAPE_VEHICLES = ["motorcycle", "car", "auto_rickshaw", "bicycle",
                        "on_foot", "public_bus", "unknown"]

MO_WEAPONS = ["knife", "iron_rod", "country_bomb", "firearm", "none",
               "bare_hands", "acid", "rope", "stone"]

MO_STOLEN_PROPERTY = ["cash", "gold_jewellery", "mobile_phone", "laptop",
                        "vehicle", "electronics", "documents", "none",
                        "mixed_valuables", "livestock"]

MO_NUM_OFFENDERS = [1, 1, 1, 2, 2, 2, 3, 3, 4, 5]  # weighted distribution

# ─────────────────────────────────────────────────────────────────────────────
# KANNADA NAME POOLS
# ─────────────────────────────────────────────────────────────────────────────
KN_MALE_FIRST_NAMES = [
    "ರಾಜೇಶ್", "ಸುರೇಶ್", "ರಾಮೇಶ್", "ಮಹೇಶ್", "ವಿನಯ್", "ಅಜಯ್", "ಸಂದೀಪ್",
    "ಪ್ರಕಾಶ್", "ಶಿವಕುಮಾರ್", "ರಾಘವೇಂದ್ರ", "ಸತೀಶ್", "ನಾಗರಾಜ್", "ಕಿರಣ್",
    "ದೀಪಕ್", "ಅನಿಲ್", "ರಮೇಶ್", "ಗಣೇಶ್", "ಮಂಜುನಾಥ್", "ಬಸವರಾಜ್", "ಅಭಿಷೇಕ್",
    "ನವೀನ್", "ಪ್ರಶಾಂತ್", "ಅರ್ಜುನ್", "ಹರ್ಷ", "ರೋಹಿತ್", "ತೇಜಸ್", "ಆಕಾಶ್",
    "ವಿಕ್ರಮ್", "ಶ್ರೀಕಾಂತ್", "ಉಮೇಶ್", "ಮೋಹನ್", "ಗೌರವ್", "ಯೋಗೇಶ್"
]

KN_FEMALE_FIRST_NAMES = [
    "ಪ್ರಿಯಾ", "ದೀಪಾ", "ಅನಿತಾ", "ಸೀತಾ", "ಕವಿತಾ", "ಶಾಂತಾ", "ಲಕ್ಷ್ಮಿ",
    "ಸರಿತಾ", "ನಿತ್ಯಾ", "ಮೀರಾ", "ವಿದ್ಯಾ", "ಪೂಜಾ", "ಅಂಜಲಿ", "ಸ್ವಾತಿ",
    "ರೇಖಾ", "ಸುಮ಼ಾ", "ಶೃತಿ", "ಮಧು", "ಅಮಲಾ", "ಗೀತಾ", "ಭಾರತಿ",
    "ರಾಧಾ", "ಸಂಗೀತಾ", "ನಿರ್ಮಲಾ", "ಜ್ಯೋತಿ", "ಸ್ನೇಹಾ", "ಸುಜಾತಾ"
]

KN_SURNAMES = [
    "ಶೆಟ್ಟಿ", "ಕುಮಾರ್", "ರೆಡ್ಡಿ", "ಪಾಟೀಲ್", "ಗೌಡ", "ನಾಯ್ಕ್", "ಹೆಗಡೆ",
    "ಜೋಶಿ", "ದೇಸಾಯಿ", "ಮೂರ್ತಿ", "ರಾವ್", "ಶಾಸ್ತ್ರಿ", "ಅಯ್ಯರ್", "ಭಟ್",
    "ಅರಸ್", "ವೊಕ್ಕಲಿಗ", "ಲಿಂಗಾಯತ್", "ತಂತ್ರಿ", "ಉಡುಪ", "ಕಾಮತ್",
    "ಅಡಿಗ", "ಪ್ರಭು", "ನಂಬಿಯಾರ್", "ಕೃಷ್ಣಮೂರ್ತಿ", "ಸ್ವಾಮಿ"
]

EN_MALE_FIRST_NAMES = [
    "Rajesh", "Suresh", "Ramesh", "Mahesh", "Vinay", "Ajay", "Sandeep",
    "Prakash", "Shivakumar", "Raghavendra", "Satish", "Nagaraj", "Kiran",
    "Deepak", "Anil", "Ganesh", "Manjunath", "Basavaraj", "Abhishek",
    "Naveen", "Prashanth", "Arjun", "Harsh", "Rohit", "Tejas", "Akash",
    "Vikram", "Srikanth", "Umesh", "Mohan", "Gaurav", "Yogesh", "Ravi"
]

EN_FEMALE_FIRST_NAMES = [
    "Priya", "Deepa", "Anita", "Seeta", "Kavitha", "Shantha", "Lakshmi",
    "Saritha", "Nitya", "Meera", "Vidya", "Pooja", "Anjali", "Swathi",
    "Rekha", "Suma", "Shruthi", "Madhu", "Amala", "Geetha", "Bharathi",
    "Radha", "Sangeetha", "Nirmala", "Jyothi", "Sneha", "Sujatha"
]

EN_SURNAMES = [
    "Shetty", "Kumar", "Reddy", "Patil", "Gowda", "Naik", "Hegde",
    "Joshi", "Desai", "Murthy", "Rao", "Shastri", "Ayyar", "Bhat",
    "Aras", "Vokkaliga", "Lingayat", "Tantri", "Udupi", "Kamath",
    "Adiga", "Prabhu", "Nambiar", "Krishnamurthy", "Swamy", "Raju",
    "Verma", "Sharma", "Singh", "Nayak", "Thakur", "Pillai"
]

# ─────────────────────────────────────────────────────────────────────────────
# POLICE RANK HIERARCHY
# ─────────────────────────────────────────────────────────────────────────────
POLICE_RANKS = [
    {"rank": "DGP",     "level": 10, "abbr": "DGP"},
    {"rank": "ADGP",    "level": 9,  "abbr": "ADGP"},
    {"rank": "IGP",     "level": 8,  "abbr": "IGP"},
    {"rank": "DIG",     "level": 7,  "abbr": "DIG"},
    {"rank": "SP",      "level": 6,  "abbr": "SP"},
    {"rank": "ASP",     "level": 5,  "abbr": "ASP"},
    {"rank": "DSP",     "level": 5,  "abbr": "DSP"},
    {"rank": "Inspector","level": 4, "abbr": "PI"},
    {"rank": "Sub-Inspector","level": 3,"abbr": "PSI"},
    {"rank": "ASI",     "level": 2,  "abbr": "APSI"},
    {"rank": "Head Constable","level": 2,"abbr": "HC"},
    {"rank": "Constable","level": 1, "abbr": "PC"},
]

# ─────────────────────────────────────────────────────────────────────────────
# VEHICLE REGISTRATION PREFIXES (Karnataka RTO codes)
# ─────────────────────────────────────────────────────────────────────────────
KARNATAKA_RTO_CODES = [
    "KA-01", "KA-02", "KA-03", "KA-04", "KA-05",  # Bengaluru
    "KA-09", "KA-10",                               # Mysuru
    "KA-19", "KA-20",                               # Mangaluru
    "KA-25", "KA-26",                               # Hubballi-Dharwad
    "KA-22", "KA-23", "KA-24",                      # Belagavi
    "KA-32",                                         # Kalaburagi
    "KA-17",                                         # Davanagere
    "KA-14",                                         # Shivamogga
    "KA-06", "KA-07",                               # Tumakuru
    "KA-36",                                         # Raichur
    "KA-38",                                         # Bidar
    "KA-28",                                         # Vijayapura
    "KA-11",                                         # Hassan
    "KA-18",                                         # Chikkamagaluru
    "KA-12",                                         # Kodagu
    "KA-13",                                         # Udupi
    "KA-08",                                         # Mandya
    "KA-57",                                         # Chamarajanagara
    "KA-04",                                         # Kolar
    "KA-41",                                         # Chikkaballapura
    "KA-42",                                         # Ramanagara
]

VEHICLE_TYPES = [
    {"type": "motorcycle",  "weight": 0.40, "fuel": ["petrol"]},
    {"type": "car",         "weight": 0.30, "fuel": ["petrol", "diesel", "cng"]},
    {"type": "auto_rickshaw","weight": 0.12, "fuel": ["cng", "petrol"]},
    {"type": "truck",       "weight": 0.08, "fuel": ["diesel"]},
    {"type": "van",         "weight": 0.05, "fuel": ["diesel", "petrol"]},
    {"type": "bicycle",     "weight": 0.03, "fuel": ["none"]},
    {"type": "tractor",     "weight": 0.02, "fuel": ["diesel"]},
]

# ─────────────────────────────────────────────────────────────────────────────
# KARNATAKA FESTIVALS & EVENTS (with crime risk modifiers by type)
# ─────────────────────────────────────────────────────────────────────────────
FESTIVALS = [
    {"name": "Dasara",        "month": 10, "day": 2,  "duration_days": 10, "risk": {"CHAIN": 2.0, "PICK": 2.5, "THEFT": 1.8}},
    {"name": "Ugadi",         "month": 3,  "day": 22, "duration_days": 3,  "risk": {"THEFT": 1.5, "BURGLARY": 1.3}},
    {"name": "Diwali",        "month": 11, "day": 1,  "duration_days": 5,  "risk": {"CHAIN": 1.8, "VEH_THEFT": 1.5, "PICK": 2.0}},
    {"name": "Eid_ul_Fitr",   "month": 4,  "day": 10, "duration_days": 3,  "risk": {"CHAIN": 1.6, "THEFT": 1.4}},
    {"name": "Christmas",     "month": 12, "day": 24, "duration_days": 3,  "risk": {"PICK": 1.7, "VEH_THEFT": 1.4}},
    {"name": "Rajyotsava",    "month": 11, "day": 1,  "duration_days": 1,  "risk": {"RIOTING": 1.5, "ASSAULT": 1.3}},
    {"name": "Republic_Day",  "month": 1,  "day": 26, "duration_days": 1,  "risk": {"CHAIN": 1.3, "PICK": 1.5}},
    {"name": "Ganesha",       "month": 9,  "day": 7,  "duration_days": 10, "risk": {"CHAIN": 1.9, "PICK": 2.2, "THEFT": 1.6}},
]

# ─────────────────────────────────────────────────────────────────────────────
# FIR DESCRIPTION TEMPLATES (English + Kannada)
# ─────────────────────────────────────────────────────────────────────────────
FIR_DESC_TEMPLATES_EN = {
    "THEFT": [
        "The complainant reported that the accused stole {item} valued at Rs. {amount} from {location} on {date}.",
        "Unknown person(s) committed theft of {item} from {location}. Complainant noticed the theft at {time}.",
        "Gold {item} stolen from house while complainant was away. Total loss estimated at Rs. {amount}.",
    ],
    "BURGLARY": [
        "The accused broke into the complainant's house by {entry_method} and stole {item} worth Rs. {amount}.",
        "Housebreaking reported. Offenders entered through {entry_method} and decamped with {item}.",
        "Unknown persons broke {entry_method} and committed theft of {item}. Case registered u/s {ipc} IPC.",
    ],
    "ROBBERY": [
        "The complainant was accosted by {num} accused persons who threatened with {weapon} and snatched {item}.",
        "Armed robbery committed near {location}. Accused fled on {vehicle} after snatching {item}.",
        "Complainant robbed of {item} worth Rs. {amount} by {num} unknown persons.",
    ],
    "CHAIN": [
        "The complainant was traveling when {num} persons on motorcycle snatched gold chain worth Rs. {amount}.",
        "Chain snatching incident reported near {location}. Two persons on {vehicle} snatched chain and fled.",
        "Accused snatched gold chain weighing {weight} grams from complainant near {location}.",
    ],
    "VEH_THEFT": [
        "Complainant's {vehicle_type} bearing registration {vehicle_reg} was stolen from {location}.",
        "Vehicle theft reported. {vehicle_type} ({vehicle_reg}) parked at {location} found missing.",
        "{vehicle_type} stolen from {location} between {time1} and {time2}.",
    ],
    "CYBER": [
        "Complainant received fraudulent call/message and was cheated of Rs. {amount} through online transfer.",
        "Accused posing as bank official defrauded complainant of Rs. {amount} by obtaining OTP.",
        "UPI fraud reported. Complainant transferred Rs. {amount} to fraudulent account.",
    ],
    "FRAUD": [
        "Accused obtained Rs. {amount} from complainant on false pretext of {pretext}.",
        "Cheating case. Accused promised {pretext} and collected Rs. {amount} without fulfilling obligations.",
        "Complainant cheated of Rs. {amount} by accused who posed as {pretext}.",
    ],
    "ASSAULT": [
        "The accused assaulted the complainant with {weapon} causing injuries near {location}.",
        "Physical assault reported. Accused attacked complainant over {reason} at {location}.",
        "Complainant was attacked by {num} persons. Injuries sustained. Admitted to hospital.",
    ],
    "MURDER": [
        "Deceased found with fatal injuries at {location}. Suspected homicide. Post-mortem ordered.",
        "Body of deceased found at {location}. Accused identified as {relation} of deceased.",
        "Murder committed at {location}. Accused attacked deceased with {weapon} over {reason}.",
    ],
    "NARCOTICS": [
        "Accused apprehended with {weight}g of {drug_type} near {location}. Contraband seized.",
        "Drug trafficking case. Accused intercepted at {location} with {drug_type} worth Rs. {amount}.",
        "{num} accused arrested with ganja/{drug_type} weighing {weight}kg near {location}.",
    ],
}

FIR_DESC_TEMPLATES_KN = {
    "THEFT": [
        "ದೂರುದಾರರು ವರದಿ ಮಾಡಿದ ಪ್ರಕಾರ ಆರೋಪಿಯು {location} ದಿಂದ ರೂ. {amount} ಮೌಲ್ಯದ {item} ಕದ್ದಿದ್ದಾನೆ.",
        "ಅಜ್ಞಾತ ವ್ಯಕ್ತಿ(ಗಳು) {location} ದಿಂದ {item} ಕದ್ದಿದ್ದಾರೆ. {time} ಗಂಟೆಗೆ ಕಳ್ಳತನ ಗೊತ್ತಾಯಿತು.",
    ],
    "BURGLARY": [
        "ಆರೋಪಿಯು {entry_method} ಮೂಲಕ ದೂರುದಾರರ ಮನೆಗೆ ನುಗ್ಗಿ ರೂ. {amount} ಮೌಲ್ಯದ {item} ಕದ್ದಿದ್ದಾನೆ.",
        "ಮನೆಯ ಬಾಗಿಲು {entry_method} ಮೂಲಕ ತೆರೆದು {item} ಕದ್ದಿದ್ದಾರೆ. ಪ್ರಕರಣ ನೋಂದಾಯಿಸಲಾಗಿದೆ.",
    ],
    "CHAIN": [
        "ದೂರುದಾರರು ಸಂಚಾರ ಮಾಡುತ್ತಿದ್ದಾಗ {num} ವ್ಯಕ್ತಿಗಳು ಮೋಟಾರ್ ಸೈಕಲ್ ಮೇಲೆ ಬಂದು ರೂ. {amount} ಮೌಲ್ಯದ ಚಿನ್ನದ ಸರ ಎಳೆದುಕೊಂಡು ಓಡಿದ್ದಾರೆ.",
    ],
    "VEH_THEFT": [
        "ದೂರುದಾರರ {vehicle_type} ({vehicle_reg}) ವಾಹನವು {location} ನಿಂದ ಕಾಣೆಯಾಗಿದೆ.",
    ],
    "CYBER": [
        "ದೂರುದಾರರಿಗೆ ವಂಚಕ ಕರೆ ಬಂದು OTP ಪಡೆದು ರೂ. {amount} ವಂಚಿಸಲಾಗಿದೆ.",
    ],
    "ASSAULT": [
        "ಆರೋಪಿಯು {weapon} ಬಳಸಿ ದೂರುದಾರರ ಮೇಲೆ {location} ಬಳಿ ಹಲ್ಲೆ ಮಾಡಿದ್ದಾನೆ.",
    ],
}

# IPC section descriptions
IPC_DESCRIPTIONS = {
    "379": "Theft",
    "457": "Lurking house-trespass or house-breaking by night",
    "392": "Robbery",
    "395": "Dacoity",
    "447": "Criminal trespass",
    "436": "Mischief by fire or explosive substance",
    "324": "Voluntarily causing hurt by dangerous weapons",
    "302": "Murder",
    "307": "Attempt to commit murder",
    "363": "Punishment for kidnapping",
    "147": "Punishment for rioting",
    "420": "Cheating and dishonestly inducing delivery of property",
    "66C_IT": "Identity theft under IT Act",
    "304A": "Causing death by negligence",
    "185MV": "Driving by a drunken person under Motor Vehicles Act",
    "NDPS_20": "Punishment for contravention in relation to cannabis plant and cannabis",
    "NDPS_27": "Punishment for consumption of any narcotic drug or psychotropic substance",
}

# Gang specializations
GANG_SPECIALIZATIONS = [
    "chain_snatching", "vehicle_theft", "house_breaking", "atm_fraud",
    "cyber_fraud", "robbery", "narcotics", "extortion", "kidnapping", "arson"
]

# Evidence types
EVIDENCE_TYPES = [
    "physical_object", "cctv_footage", "witness_statement", "forensic_report",
    "call_records", "bank_records", "vehicle_tracking", "fingerprints",
    "dna_sample", "digital_evidence", "confession", "recovered_property"
]

# Patrol vehicle types
PATROL_VEHICLE_TYPES = ["patrol_car", "motorcycle", "jeep", "van"]

# Drug types for narcotics cases
DRUG_TYPES = ["ganja", "heroin", "methamphetamine", "cocaine", "brown_sugar",
               "MDMA", "charas", "opium"]

# Fake pretext types for fraud
FRAUD_PRETEXTS = [
    "government_scheme", "lottery_win", "job_offer", "loan_approval",
    "property_deal", "investment_scheme", "marriage_proposal", "relief_fund"
]

# Assault reasons
ASSAULT_REASONS = [
    "personal_enmity", "property_dispute", "road_rage", "domestic_dispute",
    "business_dispute", "community_tension", "alcohol_related", "political_rivalry"
]

# Relationship types for kidnapping/assault
VICTIM_RELATIONS = [
    "neighbor", "acquaintance", "stranger", "relative", "colleague",
    "business_partner", "ex_partner", "landlord", "tenant"
]

Constants = {
    "DISTRICTS": KARNATAKA_DISTRICTS,
    "CRIME_CATEGORIES": CRIME_CATEGORIES,
    "MO_ENTRY_METHODS": MO_ENTRY_METHODS,
    "MO_TIME_SLOTS": MO_TIME_SLOTS,
    "MO_TARGET_TYPES": MO_TARGET_TYPES,
    "MO_ESCAPE_VEHICLES": MO_ESCAPE_VEHICLES,
    "MO_WEAPONS": MO_WEAPONS,
    "MO_STOLEN_PROPERTY": MO_STOLEN_PROPERTY,
    "KN_MALE_FIRST": KN_MALE_FIRST_NAMES,
    "KN_FEMALE_FIRST": KN_FEMALE_FIRST_NAMES,
    "KN_SURNAMES": KN_SURNAMES,
    "EN_MALE_FIRST": EN_MALE_FIRST_NAMES,
    "EN_FEMALE_FIRST": EN_FEMALE_FIRST_NAMES,
    "EN_SURNAMES": EN_SURNAMES,
    "POLICE_RANKS": POLICE_RANKS,
    "RTO_CODES": KARNATAKA_RTO_CODES,
    "VEHICLE_TYPES": VEHICLE_TYPES,
    "FESTIVALS": FESTIVALS,
    "FIR_DESC_EN": FIR_DESC_TEMPLATES_EN,
    "FIR_DESC_KN": FIR_DESC_TEMPLATES_KN,
    "IPC_DESCRIPTIONS": IPC_DESCRIPTIONS,
    "GANG_SPECIALIZATIONS": GANG_SPECIALIZATIONS,
    "EVIDENCE_TYPES": EVIDENCE_TYPES,
    "PATROL_VEHICLE_TYPES": PATROL_VEHICLE_TYPES,
    "DRUG_TYPES": DRUG_TYPES,
    "FRAUD_PRETEXTS": FRAUD_PRETEXTS,
    "ASSAULT_REASONS": ASSAULT_REASONS,
    "VICTIM_RELATIONS": VICTIM_RELATIONS,
}
