"""Government lead classification — Tier 1, Hot, Standard."""

import re

TIER1_MAP = {
    "KDN": ["kdn", "home affairs", "pdrm", "royal malaysia police", "polis diraja",
             "immigration department", "jabatan imigresen", "national registration",
             "jabatan pendaftaran", "jnd"],
    "MINDEF": ["mindef", "ministry of defence", "ministry of defense", "tentera",
               "angkatan tentera", "atm", "armed forces", "defence agency"],
    "MOF": ["mof", "ministry of finance", "kementerian kewangan", "treasury",
            "perbendaharaan", "glc oversight", "procurement division"],
    "JPM": ["jpm", "prime minister", "jabatan perdana menteri", "mampu",
            "bpen", "pmo"],
    "KD": ["kd", "ministry of digital", "kementerian digital", "mydigital",
           "digital economy", "malaysia digital economy"],
    "MOE": ["moe", "ministry of education", "kementerian pendidikan", "kpm",
            "curriculum", "sekolah", "university", "universiti"],
    "MOH": ["moh", "ministry of health", "kementerian kesihatan", "kkm",
            "hospital", "health it", "public health"],
    "MITI": ["miti", "ministry of investment", "ministry of trade", "mida",
             "industry 4.0", "perindustrian", "perdagangan"],
}

GOV_KEYWORDS = [
    "ministry", "kementerian", "department", "jabatan", "majlis", "perbadanan",
    "suruhanjaya", "lembaga", "tribunal", "authority", "badan", "agensi",
    "kerajaan", "government", "federal", "state government", "municipal",
    "dbkl", "mpsj", "mbpj", "mbb", "mpkk", "mbi", "mps",
    "glc", "government-linked", "petronas", "khazanah", "kwsp", "epf",
    "socso", "perkeso", "lhdn", "customs", "kastam", "police", "polis",
    "tentera", "army", "navy", "air force", "bomba", "fire", "forestry",
    "perhutanan", "agriculture", "pertanian", "rural", "luar bandar",
    "ict", "it contractor", "systems integrator", "public sector",
    "e-government", "myeg", "pos malaysia", "telekom", "tm",
    "govtech", "gov tech", "gov-tech",
]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def classify_org(org_name: str, org_type: str = "") -> dict:
    """
    Returns dict with keys: is_gov, tier1_ministry, is_hot (from Notion), color_code.
    color_code: 'gold' | 'red' | 'teal' | None
    """
    combined = _norm(f"{org_name} {org_type}")

    # Check Tier 1
    tier1_ministry = None
    for ministry, keywords in TIER1_MAP.items():
        if any(kw in combined for kw in keywords):
            tier1_ministry = ministry
            break

    # Check general gov
    is_gov = tier1_ministry is not None or any(kw in combined for kw in GOV_KEYWORDS)

    return {
        "is_gov": is_gov,
        "tier1_ministry": tier1_ministry,
    }


def get_color(tier1_ministry: str | None, is_hot: bool) -> str:
    if tier1_ministry:
        return "gold"
    if is_hot:
        return "red"
    return "teal"
