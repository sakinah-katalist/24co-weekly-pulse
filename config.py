# ─────────────────────────────────────────────
# Gov Leads Monitor — Configuration
# Secrets are read from environment variables.
# Locally: create a .env file (see .env.example).
# Streamlit Cloud: set these in App Settings → Secrets.
# ─────────────────────────────────────────────
import os as _os

NOTION_TOKEN = _os.environ.get("NOTION_TOKEN", "")

# ── Database IDs ──────────────────────────────────────────────────────────
MARKETING_LEADS_DB_ID = _os.environ.get("MARKETING_LEADS_DB_ID", "199b1ded-82ca-8030-96fc-c3cfa0024f76")
PAST_CLASSES_DB_ID    = _os.environ.get("PAST_CLASSES_DB_ID",    "132b1ded-82ca-80ce-aac5-f48060e58c62")
SALES_CRM_DB_ID       = _os.environ.get("SALES_CRM_DB_ID",       "8aa1672a-ac29-4454-9acc-b32f3cda12a1")

# ── Notion field names — mapped from your live database schemas ───────────
LEADS_FIELDS = {
    "contact_name":  "Preferred Name/Nickname",  # Title (contact person's name)
    "org_name":      "Company Name",             # Text (company/organisation)
    "org_type":      "Company/Individual",        # Select: Individual / Company / Unsure
    "contact_email": "Email Address",
    "contact_phone": "Phone Number",
    "lead_source":   "Channel",                  # Status: Facebook, LinkedIn, Contact Form…
    "status":        "Contact Status",           # Status: New, Contacted, Hot Lead…
    "date":          "Submitted at",             # Date
    "enquiry":       "How can we help?",         # Select: Trainings, Canva Services…
    "area":          "Area of Interest",         # Select: Generative AI, Canva, etc.
    "notes":         "Notes",
    # Hot lead is detected from Contact Status value, not a checkbox:
    # "[Training] Hot Lead" or "[Canva] Hot Lead"
}

CLASSES_FIELDS = {
    "org_name":   "Company/Sector",   # Title
    "class_name": "Class Name",       # Text
    "date":       "Class Date",       # Date
    "feedback":   "Feedback Forms",   # URL (link to feedback form)
    "signup":     "Sign Up",          # URL (sign-up link)
    # Note: no attendee count field in this database
}

CRM_FIELDS = {
    "org_name":    "Customer",           # Title
    "deal_value":  "Invoiced Amount",    # Number (RM) — your revenue field
    "stage":       "Status",             # Select: Paid, Closed, Almost Confirmed…
    "close_date":  "Money Received on",  # Date — when payment was received
    "train_date":  "Training Date",      # Date — when training was delivered
    "owner":       "Account Owner",      # Person
    "course":      "Course",             # Text
    "contact":     "Contact",            # Text
    "pax":         "No of pax",          # Number
    "gross_profit":"Gross Profit",       # Rollup (RM)
}

# ─────────────────────────────────────────────
# Email — Gmail App Password
# ─────────────────────────────────────────────
# HOW TO GET A GMAIL APP PASSWORD:
#  1. Enable 2-Step Verification on your Google account
#  2. Go to myaccount.google.com → Security → App passwords
#  3. Select app: Mail, device: Other → name it "Gov Leads Monitor"
#  4. Copy the 16-character password (no spaces) below

EMAIL_FROM     = _os.environ.get("EMAIL_FROM",     "tengku@twenty-four.io")
EMAIL_PASSWORD = _os.environ.get("EMAIL_PASSWORD", "")
EMAIL_TO       = ["sakinah@katalist.my", "elaikha@katalist.my", "syafiq@katalist.my", "andy@katalist.my", "mubiin@katalist.my"]
EMAIL_CC       = []

# ─────────────────────────────────────────────
# Report settings
# ─────────────────────────────────────────────
REPORT_OUTPUT_DIR = "."                     # Where PDFs are saved locally
WEEKS_TO_COMPARE  = 4                       # How many prior weeks shown in revenue chart

# ─────────────────────────────────────────────
# Org name expansions — short name → full name
# Add to this list whenever a new org appears.
# ─────────────────────────────────────────────
ORG_FULL_NAMES = {
    # ── Week of 11–17 August 2026 ──
    "CCB":                    "Cycle & Carriage Bintang (CCB)",
    "MSU 4.0 | Management":   "Management and Science University (MSU) 4.0 — Management Cohort",
    "Zakat Selangor":         "Lembaga Zakat Selangor (MAIS)",
    "E-Idaman":               "E-Idaman Sdn Bhd (federal solid waste concession — Kedah & Perlis)",
    "Cybernetics":            "Cybernetics International College of Technology (CICT)",
    "KKM BPM":                "Kementerian Kesihatan Malaysia — Bahagian Pengurusan Maklumat",
    "Achieve Tech Sdn Bhd (for KKDW tender)":
        "Achieve Tech Sdn Bhd — for Kementerian Kemajuan Desa dan Wilayah (KKDW)",
    # ── Week of 4–10 August 2026 ──
    "UCSI":                   "UCSI University",
    "Hornbill Skyways":       "Hornbill Skyways Sdn Bhd (Sarawak state-owned aviation)",
    "MAIWP International University": "Universiti Antarabangsa MAIWP (UniMAIWP)",
    "Permodalan Nasional Berhad": "Permodalan Nasional Berhad (PNB)",
    "Brunei Gas Carriers Sdn Bhd": "Brunei Gas Carriers Sdn Bhd (BGC — Brunei government-owned)",
    # ── Week of 28 July – 3 August 2026 ──
    "Ministry of Digital":    "Kementerian Digital (Ministry of Digital)",
    "Kelab Pegawai Wanita TUDM": "Kelab Pegawai Wanita TUDM (Royal Malaysian Air Force — Women Officers' Club)",
    "MPOC":                   "Malaysian Palm Oil Council (MPOC)",
    "Sauber (for Pasukan Polis Udara)": "Sauber — for Pasukan Polis Udara (PDRM Air Operations Force)",
    "MSU 3.0 | Lecturers":    "Management and Science University (MSU) 3.0 — Lecturers Cohort",
    "KLN | Sesi 1":           "Kementerian Luar Negeri Malaysia (Ministry of Foreign Affairs) — Sesi 1",
    "ICU JPM":                "Unit Penyelarasan Pelaksanaan, Jabatan Perdana Menteri (ICU JPM)",
    "JANM":                   "Jabatan Akauntan Negara Malaysia (Accountant General's Department)",
    # ── Week of 21–27 July 2026 ──
    # Exact entry needed so prefix-matching on "Kementerian Dalam Negeri"
    # doesn't mangle the division suffix.
    "Kementerian Dalam Negeri (KDN) — Bahagian Kawalan dan Penguatkuasaan":
        "Kementerian Dalam Negeri (Ministry of Home Affairs) — Bahagian Kawalan dan Penguatkuasaan",
    "Teraju Bumiputera Corporation": "TERAJU — Unit Peneraju Agenda Bumiputera (Prime Minister's Department)",
    "Perbadanan PR1MA Malaysia": "Perbadanan PR1MA Malaysia (1Malaysia People's Housing Programme)",
    "Malaysia Rail Link Sdn Bhd": "Malaysia Rail Link Sdn Bhd (MRL — East Coast Rail Link, MOF-owned)",
    "Malaysian Institute of Accountants": "Malaysian Institute of Accountants (MIA)",
    "Universiti Malaysia Kelantan": "Universiti Malaysia Kelantan (UMK)",
    "Takaful Malaysia":       "Syarikat Takaful Malaysia Keluarga Berhad",
    "FELCRA":                 "FELCRA Berhad (Federal Land Consolidation and Rehabilitation Authority)",
    "Cyberview":              "Cyberview Sdn Bhd (Cyberjaya Tech Hub Enabler — MOF-owned)",
    "Terengganu Incorporated": "Terengganu Incorporated Sdn Bhd (Terengganu State investment arm)",
    "MSU | 14th Series":      "Management and Science University (MSU) — 14th Series",
    # ── Week of 14–20 July 2026 sessions ──
    "Ekonomi":                "Kementerian Ekonomi Malaysia (Ministry of Economy)",
    "UniKL RCMP":             "Universiti Kuala Lumpur — Royal College of Medicine Perak (UniKL RCMP)",
    # ── Week of 14–20 July 2026 leads ──
    "UniKL MITEC, Johor":     "Universiti Kuala Lumpur — Malaysian Institute of Industrial Technology (UniKL MITEC), Johor",
    "Akademi Sains Malaysia": "Akademi Sains Malaysia (Academy of Sciences Malaysia — ASM)",
    "WISDEC MTIB":            "WISDEC — Wood Industry Skills Development Centre (Malaysian Timber Industry Board)",
    "MUIP":                   "Majlis Ugama Islam dan Adat Resam Melayu Pahang (MUIP)",
    "Kementerian Dalam Negeri": "Kementerian Dalam Negeri (Ministry of Home Affairs — KDN)",
    # ── Kementerian Kesihatan Malaysia (MOH — Tier 1) ──
    "KKM":                    "Kementerian Kesihatan Malaysia (Ministry of Health)",
    "KKM BPM":                "Kementerian Kesihatan Malaysia — Bahagian Pengurusan Maklumat",
    "KKM - BTM":              "Kementerian Kesihatan Malaysia — Bahagian Teknologi Maklumat",
    "KKM - BTM - Gen AI":     "Kementerian Kesihatan Malaysia — Bahagian Teknologi Maklumat",
    "KKM BTM":                "Kementerian Kesihatan Malaysia — Bahagian Teknologi Maklumat",
    "KKM - BKKM HQ":         "Kementerian Kesihatan Malaysia — BKKM Headquarters",
    "KKM - Bahagian Kompetensi": "Kementerian Kesihatan Malaysia — Bahagian Kompetensi",
    "KKM Program Keselamatan dan Kualiti Makanan (PKKM)":
                              "Kementerian Kesihatan Malaysia — Program Keselamatan dan Kualiti Makanan",
    "KKM Unit digital":       "Kementerian Kesihatan Malaysia — Unit Digital",
    "KKM (gigi)":             "Kementerian Kesihatan Malaysia — Program Kesihatan Pergigian",
    "KKM (Pendidikan Kesihatan)": "Kementerian Kesihatan Malaysia — Pendidikan Kesihatan",
    "KKM (Program Kesihatan Pergigian)": "Kementerian Kesihatan Malaysia — Program Kesihatan Pergigian",
    "KKM - Bahagian Perkhidmatan Kejuruteraan":
                              "Kementerian Kesihatan Malaysia — Bahagian Perkhidmatan Kejuruteraan",

    # ── Other Tier 1 Ministries ──
    "JPM":                    "Jabatan Perdana Menteri (Prime Minister's Department)",
    "(ICU, JPM) Unit Penyelarasan Pelaksanaan":
                              "Unit Penyelarasan Pelaksanaan — Jabatan Perdana Menteri",
    "KDN":                    "Kementerian Dalam Negeri (Ministry of Home Affairs)",
    "MINISTRY OF HOME AFFAIRS (KEMENTERIAN DALAM NEGERI)":
                              "Kementerian Dalam Negeri (Ministry of Home Affairs)",
    "MINISTRY OF HOME AFFAIRS":
                              "Kementerian Dalam Negeri (Ministry of Home Affairs)",
    "MINDEF":                 "Kementerian Pertahanan Malaysia (Ministry of Defence)",
    "MINISTRY OF DEFENCE":    "Kementerian Pertahanan Malaysia (Ministry of Defence)",
    "MOF":                    "Kementerian Kewangan Malaysia (Ministry of Finance)",
    "MINISTRY OF FINANCE":    "Kementerian Kewangan Malaysia (Ministry of Finance)",
    "MOE":                    "Kementerian Pendidikan Malaysia (Ministry of Education)",
    "MINISTRY OF EDUCATION":  "Kementerian Pendidikan Malaysia (Ministry of Education)",
    "MOH":                    "Kementerian Kesihatan Malaysia (Ministry of Health)",
    "MINISTRY OF HEALTH":     "Kementerian Kesihatan Malaysia (Ministry of Health)",
    "MITI":                   "Kementerian Perdagangan Antarabangsa dan Industri (Ministry of International Trade & Industry)",
    "MINISTRY OF INTERNATIONAL TRADE AND INDUSTRY":
                              "Kementerian Perdagangan Antarabangsa dan Industri (MITI)",
    "KD":                     "Kementerian Digitalisasi (Ministry of Digital)",
    "MINISTRY OF DIGITAL":    "Kementerian Digitalisasi (Ministry of Digital)",

    # ── Statutory Bodies & Agencies ──
    "MTIB":                   "Malaysian Timber Industry Board (Lembaga Perindustrian Kayu Malaysia)",
    "MTIB - Siri 2":          "Malaysian Timber Industry Board — Siri 2",
    "MBPJ":                   "Majlis Bandaraya Petaling Jaya (Petaling Jaya City Council)",
    "(MBPJ) Majlis Bandaraya Petaling Jaya":
                              "Majlis Bandaraya Petaling Jaya (Petaling Jaya City Council)",
    "BSN":                    "Bank Simpanan Nasional (National Savings Bank)",
    "MOTAC":                  "Kementerian Pelancongan, Seni dan Budaya (Ministry of Tourism, Arts & Culture)",
    "PSCC":                   "Public Service Chinese Community (PSCC) Malaysia",
    "CyberView":              "CyberView Sdn Bhd (MSC Malaysia cybersecurity hub)",
    "Zoo Negara":             "Zoo Negara Malaysia (National Zoo)",
    "SIDC":                   "Securities Industry Development Corporation",
    "Cenviro":                "Cenviro Sdn Bhd (government environmental services — Kualiti Alam group)",

    # ── Public Universities & Research ──
    "PTPKM UPM":              "Pusat Teknologi dan Pengurusan Kriptologi Malaysia — Universiti Putra Malaysia",
    "(PTPKM UPM) Pusat Teknologi dan Pengurusan Kriptologi Malaysia":
                              "Pusat Teknologi dan Pengurusan Kriptologi Malaysia — CyberSecurity Malaysia / UPM",
    "UTEM":                   "Universiti Teknikal Malaysia Melaka",
    "Universiti Teknikal Malaysia Melaka (UTEM)":
                              "Universiti Teknikal Malaysia Melaka (UTEM)",
    "MSU":                    "Management and Science University (MSU)",
    "MSU | Lecturers":        "Management and Science University (MSU) — Lecturers Cohort",
    "MSU | Management":       "Management and Science University (MSU) — Management Cohort",
    "Jabatan Kerajaan Tempatan (JKT)":
                              "Jabatan Kerajaan Tempatan (Department of Local Government)",
    "Jabatan Kebajikan Malaysia": "Jabatan Kebajikan Masyarakat Malaysia (Social Welfare Dept)",
    "Akademi PKNS":           "Akademi PKNS — Perbadanan Kemajuan Negeri Selangor",
    "Majlis Perbandaran Manjung": "Majlis Perbandaran Manjung (Manjung Municipal Council)",
    "Kementerian Kesihatan Malaysia (KKM)":
                              "Kementerian Kesihatan Malaysia (Ministry of Health)",
    "Schneider Electric Malaysia": "Schneider Electric Malaysia (GovTech energy infrastructure partner)",

    # ── KKM sub-divisions (searched & confirmed Jun 2026) ──
    "KKM BKKM":              "Kementerian Kesihatan Malaysia — Bahagian Keselamatan dan Kualiti Makanan (BKKM / Food Safety & Quality Division)",
    "KKM - BKKM":            "Kementerian Kesihatan Malaysia — Bahagian Keselamatan dan Kualiti Makanan (BKKM)",
    "BKKM":                  "Bahagian Keselamatan dan Kualiti Makanan (Food Safety & Quality Division — under KKM)",
    "KKM Zon Utara (perlis, penang, kedah)":
                             "Kementerian Kesihatan Malaysia — Zon Utara (Perlis, Pulau Pinang, Kedah)",

    # ── State Health Departments ──
    "Jabatan Kesihatan Negeri Sabah (JKNS) - BKKM":
                             "Jabatan Kesihatan Negeri Sabah — Bahagian Keselamatan dan Kualiti Makanan (BKKM)",
    "Jabatan Kesihatan Negeri Sabah (JKNS)":
                             "Jabatan Kesihatan Negeri Sabah (State Health Dept, Sabah — under KKM)",
    "Jabatan Kesihatan Negeri Sabah":
                             "Jabatan Kesihatan Negeri Sabah (State Health Dept, Sabah — under KKM)",
    "Jabatan Kesihatan Negeri Sembilan (JKNS)":
                             "Jabatan Kesihatan Negeri Sembilan (State Health Dept, Negeri Sembilan — under KKM)",
    "Jabatan Kesihatan Negeri Sembilan":
                             "Jabatan Kesihatan Negeri Sembilan (State Health Dept, Negeri Sembilan — under KKM)",
    "JKNS":                  "Jabatan Kesihatan Negeri (State Health Department — under KKM)",

    # ── Digital / National departments ──
    "Jabatan Digital Negara": "Jabatan Digital Negara (National Digital Department / JDN) — Kementerian Digitalisasi",
    "JDN":                    "Jabatan Digital Negara (National Digital Department)",

    # ── Tabung Haji variants ──
    "Lembaga Tabung Haji HQ (LTH)": "Lembaga Tabung Haji — Ibu Pejabat (Headquarters)",
    "Lembaga Tabung Haji HQ":        "Lembaga Tabung Haji — Ibu Pejabat (Headquarters)",

    # ── New orgs added Jun 2026 ──
    "PLANMalaysia":                   "PLANMalaysia (Jabatan Perancangan Bandar dan Desa — Department of Town & Country Planning)",
    "KWSP | EPF":                     "Kumpulan Wang Simpanan Pekerja — Employees Provident Fund (EPF)",
    "KWSP":                           "Kumpulan Wang Simpanan Pekerja (Employees Provident Fund / EPF)",
    "EPF":                            "Employees Provident Fund (Kumpulan Wang Simpanan Pekerja / KWSP)",
    "Yayasan Terengganu":             "Yayasan Terengganu (Terengganu State Foundation)",
    "Kementerian Ekonomi":            "Kementerian Ekonomi Malaysia (Ministry of Economy)",
    "Kementerian Luar Negeri (KLN)":  "Kementerian Luar Negeri Malaysia (Ministry of Foreign Affairs)",
    "KLN":                            "Kementerian Luar Negeri Malaysia (Ministry of Foreign Affairs)",
    "FELCRA Kelantan":                "Federal Land Consolidation and Rehabilitation Authority (FELCRA) — Cawangan Kelantan",
    "FELCRA":                         "Federal Land Consolidation and Rehabilitation Authority (FELCRA)",
    "MSU - Canva Siri 2":             "Management and Science University (MSU) — Canva Siri 2",
    "Kementerian Kesihatan Malaysia KKM": "Kementerian Kesihatan Malaysia (Ministry of Health)",

    # ── Federal Ministries (Tier 1 + others) ──
    "KPKT":   "Kementerian Perumahan dan Kerajaan Tempatan (Ministry of Housing and Local Government)",
    "KKR":    "Kementerian Kerja Raya Malaysia (Ministry of Works)",
    "MOT":    "Kementerian Pengangkutan Malaysia (Ministry of Transport)",
    "MOW":    "Kementerian Kerja Raya Malaysia (Ministry of Works)",
    "KPT":    "Kementerian Pengajian Tinggi Malaysia (Ministry of Higher Education)",
    "MOHE":   "Kementerian Pengajian Tinggi Malaysia (Ministry of Higher Education)",
    "KKMM":   "Kementerian Komunikasi dan Multimedia Malaysia (Ministry of Communications & Multimedia)",
    "KKDW":   "Kementerian Kemajuan Desa dan Wilayah (Ministry of Rural and Regional Development)",
    "KKS":    "Kementerian Kesejahteraan Bandar, Perumahan dan Kerajaan Tempatan",

    # ── Statutory Bodies & GLCs ──
    "BNM":    "Bank Negara Malaysia (Central Bank of Malaysia)",
    "SC":     "Securities Commission Malaysia (Suruhanjaya Sekuriti Malaysia)",
    "LHDN":   "Lembaga Hasil Dalam Negeri Malaysia (Inland Revenue Board of Malaysia / IRBM)",
    "IRBM":   "Inland Revenue Board of Malaysia (Lembaga Hasil Dalam Negeri / LHDN)",
    "PERKESO":"Pertubuhan Keselamatan Sosial (Social Security Organisation / SOCSO)",
    "SOCSO":  "Social Security Organisation Malaysia (Pertubuhan Keselamatan Sosial / PERKESO)",
    "KWAP":   "Kumpulan Wang Amanah Persaraan (Retirement Fund Incorporated)",
    "LTAT":   "Lembaga Tabung Angkatan Tentera (Armed Forces Fund Board)",
    "Tabung Haji": "Lembaga Tabung Haji (Pilgrim's Fund Board of Malaysia)",
    "LTH":    "Lembaga Tabung Haji (Pilgrim's Fund Board of Malaysia)",
    "PTPTN":  "Perbadanan Tabung Pendidikan Tinggi Nasional (National Higher Education Fund Corporation)",
    "MARA":   "Majlis Amanah Rakyat (Council of Trust for Indigenous People)",
    "FELDA":  "Lembaga Kemajuan Tanah Persekutuan — Federal Land Development Authority (FELDA)",
    "PNB":    "Permodalan Nasional Berhad (National Equity Corporation)",
    "Khazanah": "Khazanah Nasional Berhad (Malaysia's sovereign wealth fund)",
    "TNB":    "Tenaga Nasional Berhad (National Energy Corporation)",
    "TM":     "Telekom Malaysia Berhad",
    "MAHB":   "Malaysia Airports Holdings Berhad",
    "Petronas":   "Petroliam Nasional Berhad (PETRONAS — Malaysia's national oil company)",
    "PETRONAS":   "Petroliam Nasional Berhad (Malaysia's national oil company)",
    "Instep":     "InStep — Institut Pengembangan dan Kepimpinan Industri Petroleum (Petronas)",
    "Instep x MAHB Ipoh": "InStep (Petronas) × Malaysia Airports Holdings Berhad (MAHB) — Ipoh",
    "AmanahRaya": "Amanah Raya Berhad (Public Trustee Corporation of Malaysia)",
    "AmanahRaya Trustees Berhad": "Amanah Raya Berhad (Public Trustee Corporation of Malaysia)",

    # ── Law Enforcement & Defence ──
    "PDRM":   "Polis Diraja Malaysia (Royal Malaysian Police)",
    "ATM":    "Angkatan Tentera Malaysia (Malaysian Armed Forces)",
    "JPAM":   "Jabatan Pertahanan Awam Malaysia (Civil Defence Department)",
    "JBPM":   "Jabatan Bomba dan Penyelamat Malaysia (Fire and Rescue Department)",
    "RELA":   "Jabatan Sukarelawan Malaysia — Relawan Malaysia (RELA)",
    "SPRM":   "Suruhanjaya Pencegahan Rasuah Malaysia — Malaysian Anti-Corruption Commission (MACC)",
    "MACC":   "Malaysian Anti-Corruption Commission (Suruhanjaya Pencegahan Rasuah Malaysia / SPRM)",

    # ── Public Departments ──
    "JPA":    "Jabatan Perkhidmatan Awam Malaysia (Public Service Department)",
    "JKR":    "Jabatan Kerja Raya Malaysia (Public Works Department)",
    "JPS":    "Jabatan Pengairan dan Saliran Malaysia (Department of Irrigation and Drainage)",
    "JPJ":    "Jabatan Pengangkutan Jalan Malaysia (Road Transport Department)",
    "JPN":    "Jabatan Pendaftaran Negara Malaysia (National Registration Department)",
    "JKDM":   "Jabatan Kastam Diraja Malaysia (Royal Malaysian Customs Department)",
    "DOSM":   "Jabatan Perangkaan Malaysia (Department of Statistics Malaysia)",
    "JKT":    "Jabatan Kerajaan Tempatan (Department of Local Government)",

    # ── Digital & Tech Agencies ──
    "MDEC":   "Malaysia Digital Economy Corporation (Perbadanan Ekonomi Digital Malaysia)",
    "MDeC":   "Malaysia Digital Economy Corporation (Perbadanan Ekonomi Digital Malaysia)",
    "MCMC":   "Malaysian Communications and Multimedia Commission (Suruhanjaya Komunikasi dan Multimedia)",
    "SKMM":   "Suruhanjaya Komunikasi dan Multimedia Malaysia (Malaysian Communications and Multimedia Commission)",
    "MIMOS":  "MIMOS Berhad (Malaysia's national applied ICT research and development centre)",
    "CyberSecurity Malaysia": "CyberSecurity Malaysia (Agensi Keselamatan Siber Nasional)",
    "MyIPO":  "Intellectual Property Corporation of Malaysia (Perbadanan Harta Intelek Malaysia)",

    # ── Public Universities ──
    "UPM":    "Universiti Putra Malaysia",
    "UiTM":   "Universiti Teknologi MARA",
    "UTM":    "Universiti Teknologi Malaysia",
    "UM":     "Universiti Malaya (University of Malaya)",
    "UKM":    "Universiti Kebangsaan Malaysia (National University of Malaysia)",
    "USM":    "Universiti Sains Malaysia (University of Science Malaysia)",
    "UMP":    "Universiti Malaysia Pahang Al-Sultan Abdullah",
    "UTHM":   "Universiti Tun Hussein Onn Malaysia",
    "UPSI":   "Universiti Pendidikan Sultan Idris",
    "UniMAP": "Universiti Malaysia Perlis",
    "UMS":    "Universiti Malaysia Sabah",
    "UNIMAS": "Universiti Malaysia Sarawak",
    "UniSZA": "Universiti Sultan Zainal Abidin",
    "UTeM":   "Universiti Teknikal Malaysia Melaka",
    "IPG":    "Institut Pendidikan Guru Malaysia (Teacher Education Institute Malaysia)",

    # ── Local Councils ──
    "DBKL":   "Dewan Bandaraya Kuala Lumpur (Kuala Lumpur City Hall)",
    "MBSA":   "Majlis Bandaraya Shah Alam (Shah Alam City Council)",
    "MPAJ":   "Majlis Perbandaran Ampang Jaya (Ampang Jaya Municipal Council)",
    "MPKlang":"Majlis Perbandaran Klang (Klang Municipal Council)",
    "MPSJ":   "Majlis Perbandaran Subang Jaya (Subang Jaya Municipal Council)",
}
