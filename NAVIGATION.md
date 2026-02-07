# 🗺️ Project Navigation Guide

The codebase has been reorganized for clarity! Here's where everything is:

## 📁 Folder Structure

```
Failures/
│
├── 📖 docs/                     ← ALL DOCUMENTATION HERE
│   ├── START_HERE.md                  # Your first step
│   ├── ROADMAP.md                     # Complete learning path
│   ├── QUICKSTART.md                  # Fast start guide
│   ├── LEARNING_GUIDE.md              # Phase 1 approach
│   ├── BUILDING_SYSTEMS.md            # Phase 2 guide
│   ├── SYSTEMS_QUICKSTART.md          # Systems fast start
│   ├── SYSTEMS_SUMMARY.md             # Quick reference
│   ├── CHEATSHEET.md                  # Pattern reference
│   ├── COMPONENT_CHECKLIST.md         # Track components
│   ├── MY_PROGRESS.md                 # Your personal tracker
│   ├── PROJECT_SUMMARY.md             # Project overview
│   ├── EXERCISES.md                   # Exercise info
│   └── STUDENT_GUIDE.md               # Additional help
│
├── 🎓 exercises/                ← PHASE 1: LEARN PATTERNS
│   ├── ex1_db_starter.py              # Connection pools (TODO)
│   ├── ex2_network_starter.py         # Retry logic (TODO)
│   ├── ex3_ratelimit_starter.py       # Rate limiting (TODO)
│   ├── test_ex1.py                    # Tests for ex1
│   ├── README.md                      # Exercise guide
│   └── SOLUTIONS.md                   # Hints & solutions
│
├── 🏗️ components/               ← PHASE 2: BUILD SYSTEMS
│   ├── common/                        # Reusable code
│   │   └── __init__.py
│   ├── auth_system/                   # Authentication system
│   │   ├── README.md                  # Complete guide
│   │   ├── api.py                     # Endpoints (TODO)
│   │   ├── config.py                  # Configuration
│   │   ├── schema.sql                 # Database schema
│   │   └── .env.example               # Environment template
│   ├── payment_processing/            # Coming soon
│   ├── file_upload/                   # Coming soon
│   ├── notifications/                 # Coming soon
│   └── api_gateway/                   # Coming soon
│
├── 🔧 reference/                ← WORKING EXAMPLES
│   ├── db_failures.py                 # Database patterns
│   ├── network_failures.py            # Network patterns
│   ├── rate_limiting.py               # Rate limit patterns
│   ├── circuit_breaker.py             # Circuit breaker
│   ├── resource_failures.py           # Resource patterns
│   └── README.md                      # Reference guide
│
├── 🛠️ tools/                    ← UTILITIES
│   ├── launcher.py                    # Interactive launcher
│   ├── test_scenarios.py              # Automated tests
│   └── README.md                      # Tools guide
│
├── README.md                    ← START HERE!
└── requirements.txt             ← Dependencies
```

## 🚀 Quick Navigation

### I'm brand new here
1. Read: [README.md](README.md)
2. Then: [docs/START_HERE.md](docs/START_HERE.md)
3. Then: [docs/ROADMAP.md](docs/ROADMAP.md)

### I want to do Phase 1 exercises
1. Read: [exercises/README.md](exercises/README.md)
2. Code: [exercises/ex1_db_starter.py](exercises/ex1_db_starter.py)
3. Test: `python exercises/test_ex1.py`

### I finished Phase 1, ready for Phase 2
1. Read: [docs/BUILDING_SYSTEMS.md](docs/BUILDING_SYSTEMS.md)
2. Read: [components/auth_system/README.md](components/auth_system/README.md)
3. Code: [components/auth_system/api.py](components/auth_system/api.py)

### I want to see working examples
1. Browse: [reference/README.md](reference/README.md)
2. Run: `python tools/launcher.py`
3. Test: `uvicorn reference.db_failures:app --port 8000`

### I need quick help/reference
1. Patterns: [docs/CHEATSHEET.md](docs/CHEATSHEET.md)
2. Systems: [docs/SYSTEMS_SUMMARY.md](docs/SYSTEMS_SUMMARY.md)
3. Progress: [docs/MY_PROGRESS.md](docs/MY_PROGRESS.md)

## 📊 What Moved Where?

### Documentation (→ docs/)
- `START_HERE.md` → `docs/START_HERE.md`
- `BUILDING_SYSTEMS.md` → `docs/BUILDING_SYSTEMS.md`
- `CHEATSHEET.md` → `docs/CHEATSHEET.md`
- All other `.md` files in root → `docs/`

### Reference Code (→ reference/)
- `db_failures.py` → `reference/db_failures.py`
- `network_failures.py` → `reference/network_failures.py`
- `rate_limiting.py` → `reference/rate_limiting.py`
- `circuit_breaker.py` → `reference/circuit_breaker.py`
- `resource_failures.py` → `reference/resource_failures.py`

### Tools (→ tools/)
- `launcher.py` → `tools/launcher.py`
- `test_scenarios.py` → `tools/test_scenarios.py`

### Unchanged
- `exercises/` - Still in same place
- `components/` - Still in same place
- `README.md` - Still in root
- `requirements.txt` - Still in root

## ⚡ Updated Commands

### Old Way → New Way

**Running reference examples:**
```bash
# Before
uvicorn db_failures:app --port 8000

# Now
uvicorn reference.db_failures:app --port 8000
```

**Running launcher:**
```bash
# Before
python launcher.py

# Now
python tools/launcher.py
```

**Running tests:**
```bash
# Before
python test_scenarios.py

# Now
python tools/test_scenarios.py
```

**Reading docs:**
```bash
# Before
code START_HERE.md

# Now
code docs/START_HERE.md
```

## 💡 Why This Structure?

**Clean Root:**
- Only essential files (README, requirements)
- Easy to understand at a glance

**Organized by Purpose:**
- `docs/` = All reading material
- `exercises/` = Hands-on learning
- `components/` = Building systems
- `reference/` = Working examples
- `tools/` = Utilities

**Better Navigation:**
- Know where to find things
- Logical grouping
- Scales as project grows

## 🎯 Next Steps

1. **Update your bookmarks** to new file locations
2. **Use `docs/` prefix** when reading documentation
3. **Use `reference.` prefix** when running examples
4. **Continue your learning journey!**

---

**Everything is still here, just better organized!** 📚✨
