# Curated ICD-9 codes used for synthetic patient generation and diagnosis lookups.
# Format: {icd9_code: (short_title, long_title)}

ICD9_COMMON: dict[str, tuple[str, str]] = {
    "250.00": ("Diabetes mellitus w/o complication", "Diabetes mellitus without mention of complication, type II or unspecified type, not stated as uncontrolled"),
    "250.01": ("Diabetes mellitus w/o complication", "Diabetes mellitus without mention of complication, type I, not stated as uncontrolled"),
    "401.9":  ("Hypertension NOS", "Unspecified essential hypertension"),
    "496":    ("Chr airway obstruct NEC", "Chronic airway obstruction, not elsewhere classified"),
    "428.0":  ("CHF NOS", "Congestive heart failure, unspecified"),
    "427.31": ("Atrial fibrillation", "Atrial fibrillation"),
    "584.9":  ("Acute renal failure NOS", "Acute renal failure, unspecified"),
    "585.3":  ("Chr kidney dis stage III", "Chronic kidney disease, Stage III (moderate)"),
    "585.4":  ("Chr kidney dis stage IV", "Chronic kidney disease, Stage IV (severe)"),
    "585.5":  ("Chr kidney dis stage V", "Chronic kidney disease, Stage V"),
    "038.9":  ("Septicemia NOS", "Unspecified septicemia"),
    "486":    ("Pneumonia, organism NOS", "Pneumonia, organism unspecified"),
    "410.91": ("AMI NOS, initial episode", "Acute myocardial infarction of unspecified site, initial episode of care"),
    "434.91": ("Cerebral art occlusion NOS", "Cerebral artery occlusion, unspecified, with cerebral infarction"),
    "414.01": ("Crnry athrscl natve vssl", "Coronary atherosclerosis of native coronary artery"),
    "272.4":  ("Hyperlipidemia NEC/NOS", "Other and unspecified hyperlipidemia"),
    "285.9":  ("Anemia NOS", "Anemia, unspecified"),
    "276.1":  ("Hyposmolality", "Hyposmolality and/or hyponatremia"),
    "276.51": ("Dehydration", "Dehydration"),
    "518.81": ("Acute resp failure", "Acute respiratory failure"),
    "507.0":  ("Pneumonitis d/t food/vomit", "Pneumonitis due to inhalation of food or vomitus"),
    "599.0":  ("Urin tract infection NOS", "Urinary tract infection, site not specified"),
    "530.81": ("Esophageal reflux", "Esophageal reflux"),
    "311":    ("Depressive disorder NEC", "Depressive disorder, not elsewhere classified"),
    "296.30": ("Maj dep aff dis-recur-unsp", "Major depressive affective disorder, recurrent episode, unspecified"),
    "V58.61": ("Long-term use anticoagul", "Long-term (current) use of anticoagulants"),
    "V10.3":  ("Hx-breast malignancy", "Personal history of malignant neoplasm of breast"),
}

# Reverse lookup: keyword → list of ICD9 codes
KEYWORD_TO_ICD9: dict[str, list[str]] = {
    "diabetes":     ["250.00", "250.01"],
    "hypertension": ["401.9"],
    "copd":         ["496"],
    "chf":          ["428.0"],
    "heart failure": ["428.0"],
    "afib":         ["427.31"],
    "atrial fibrillation": ["427.31"],
    "aki":          ["584.9"],
    "acute kidney": ["584.9"],
    "ckd":          ["585.3", "585.4", "585.5"],
    "chronic kidney": ["585.3", "585.4", "585.5"],
    "sepsis":       ["038.9"],
    "pneumonia":    ["486"],
    "mi":           ["410.91"],
    "myocardial infarction": ["410.91"],
    "stroke":       ["434.91"],
    "cad":          ["414.01"],
    "coronary artery": ["414.01"],
    "hyperlipidemia": ["272.4"],
    "anemia":       ["285.9"],
    "uti":          ["599.0"],
    "respiratory failure": ["518.81"],
}


def keyword_to_icd9(keyword: str) -> list[str]:
    keyword = keyword.lower().strip()
    return KEYWORD_TO_ICD9.get(keyword, [])
