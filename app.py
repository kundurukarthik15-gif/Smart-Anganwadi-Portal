# ================================================================
#  SMART ANGANWADI PORTAL — app.py  v3.0
#  Production-Ready Flask + Supabase Backend
#  Modules: Auth · Centers · Children · Beneficiaries
#           Stock · Distribution · Meetings · Stories
#           BMI & Nutrition · Dashboard · Reports
# ================================================================

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
import base64

import bcrypt
import jwt
from dotenv import load_dotenv
from flask import Flask, request, jsonify, g, send_file, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client

# ReportLab Imports
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Gemini AI (optional — graceful fallback if key not set)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"⚠️  Failed to import google.generativeai: {e}")
    GEMINI_AVAILABLE = False
    logger_placeholder = None

load_dotenv()

# ── App setup ───────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────
JWT_SECRET      = os.getenv("JWT_SECRET", "smart_anganwadi_secret_2024")
JWT_ALGORITHM   = "HS256"
JWT_EXPIRY_DAYS = int(os.getenv("JWT_EXPIRY_DAYS", 7))
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
SUPABASE_PHOTO_BUCKET = os.getenv("SUPABASE_PHOTO_BUCKET", "attendance-photos")
PORT            = int(os.getenv("PORT", 5000))
FLASK_ENV       = os.getenv("FLASK_ENV", "production")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")

# ── Supabase client ─────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Gemini client ────────────────────────────────────────────────
gemini_model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        logging.getLogger(__name__).info("✅ Gemini AI initialized successfully")
    except Exception as _e:
        logging.getLogger(__name__).warning(f"⚠️  Gemini init failed: {_e}")
else:
    logging.getLogger(__name__).warning("⚠️  Gemini API key not configured — AI endpoint will return 503")


# ================================================================
#  HELPERS
# ================================================================

def ok(data=None, message="Success", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status

def err(message="Error", status=400):
    return jsonify({"success": False, "message": message}), status

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def today_iso():
    return datetime.now(timezone.utc).date().isoformat()

def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_pw(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def make_token(user_id: str, center_id: str, email: str) -> str:
    payload = {
        "sub":       user_id,
        "center_id": center_id,
        "email":     email,
        "iat":       datetime.now(timezone.utc),
        "exp":       datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def require(*fields):
    """Return (ok, missing_msg) for required fields in request JSON."""
    data    = request.get_json() or {}
    missing = [f for f in fields if not data.get(f)]
    return (True, None) if not missing else (False, f"Missing: {', '.join(missing)}")

def compute_bmi(height_cm: float, weight_kg: float) -> float:
    """BMI = weight_kg / (height_m)^2, rounded to 1 decimal."""
    if not height_cm or height_cm <= 0:
        return 0.0
    return round(weight_kg / ((height_cm / 100) ** 2), 1)

def classify_bmi(bmi: float) -> str:
    if bmi < 14.0:  return "Severe Underweight"
    if bmi < 16.0:  return "Underweight"
    if bmi < 22.0:  return "Normal"
    if bmi < 26.0:  return "Overweight"
    return "Obese"

BMI_NUTRITION_STATUS = {
    "Severe Underweight": "Severely malnourished — immediate nutritional intervention required.",
    "Underweight":        "Mildly underweight — increase calorie and protein intake.",
    "Normal":             "Healthy weight — continue balanced diet.",
    "Overweight":         "Slightly overweight — reduce fried and sugary foods.",
    "Obese":              "Obese — medical referral and dietary change required.",
}


# ================================================================
#  AUTH MIDDLEWARE
# ================================================================

# In-memory cache for verified Supabase tokens to prevent redundant Auth API calls
# Structure: { token_str: (user_dict, expiry_datetime) }
TOKEN_CACHE = {}
# Cache resolved user profile info to prevent parallel database queries
# Structure: { token_str: (resolved_user_dict, expiry_datetime) }
RESOLVED_USER_CACHE = {}


def verify_supabase_token(token):
    """Verify Supabase token using the official Supabase Auth client SDK."""
    from datetime import datetime, timezone, timedelta
    
    # 1. Check cache first to avoid bottleneck on parallel requests
    now = datetime.now(timezone.utc)
    if token in TOKEN_CACHE:
        sb_user, expiry = TOKEN_CACHE[token]
        if now < expiry:
            return sb_user
        else:
            TOKEN_CACHE.pop(token, None) # remove expired entry
            
    try:
        # Call the official Supabase client to get the user from the JWT
        res = supabase.auth.get_user(token)
        if res and res.user:
            # Defensive date parsing helper
            def parse_date(val):
                if not val:
                    return None
                if hasattr(val, "isoformat"):
                    return val.isoformat()
                return str(val)

            # Convert user object to dictionary format matching the rest of the code
            user_dict = {
                "id": res.user.id,
                "email": res.user.email,
                "email_confirmed_at": parse_date(res.user.email_confirmed_at),
                "confirmed_at": parse_date(res.user.confirmed_at),
                "user_metadata": res.user.user_metadata or {}
            }
            # Cache the successfully verified token for 10 minutes
            TOKEN_CACHE[token] = (user_dict, now + timedelta(minutes=10))
            return user_dict
    except Exception as e:
        logger.error(f"Error calling supabase.auth.get_user: {e}")
        
    return None


def auto_provision_user(sb_user):
    """Automatically create Center Profile, User Profile, and Initial Dashboard Config (default stock entries) for a new Supabase user."""
    email = sb_user.get("email")
    user_id = sb_user.get("id")
    full_name = "Google User"
    profile_photo = None
    
    user_metadata = sb_user.get("user_metadata")
    if user_metadata:
        full_name = (
            user_metadata.get("full_name") or
            user_metadata.get("name") or
            user_metadata.get("preferred_username") or
            "Google User"
        )
        profile_photo = (
            user_metadata.get("avatar_url") or
            user_metadata.get("picture")
        )
        
    # Check if user already exists (double safety)
    user_check = supabase.table("users").select("id").eq("id", user_id).execute()
    if user_check.data:
        return user_check.data[0]
        
    # 1. Create Center Profile
    center_id = str(uuid.uuid4())
    center_record = {
        "id": center_id,
        "center_name": f"{full_name}'s Center",
        "district": "Default District",
        "mandal": "Default Mandal",
        "village": "Default Village",
        "address": "Default Center Address",
        "mobile": None,
        "created_at": now_iso()
    }
    supabase.table("centers").insert(center_record).execute()
    
    # 2. Create User Profile
    user_record = {
        "id": user_id,
        "full_name": full_name,
        "email": email.strip().lower(),
        "password_hash": hash_pw(str(uuid.uuid4())), # dummy password hash for security
        "mobile": None,
        "center_id": center_id,
        "created_at": now_iso()
    }
    
    # Try inserting with profile_photo, fall back without if column is missing
    user_record["profile_photo"] = profile_photo
    try:
        supabase.table("users").insert(user_record).execute()
    except Exception as e:
        logger.warning(f"Failed to insert with profile_photo, trying without: {e}")
        user_record.pop("profile_photo", None)
        supabase.table("users").insert(user_record).execute()
    
    # 3. Seed Default Stock Entries (Initial Dashboard Configuration)
    default_stocks = [
        {"item_name": "Eggs", "min_quantity": 50.0, "unit": "units"},
        {"item_name": "Milk (Litres)", "min_quantity": 20.0, "unit": "litres"},
        {"item_name": "Dates", "min_quantity": 10.0, "unit": "kg"},
        {"item_name": "Chikki", "min_quantity": 30.0, "unit": "packets"},
        {"item_name": "Rice (kg)", "min_quantity": 40.0, "unit": "kg"},
        {"item_name": "Dal (kg)", "min_quantity": 15.0, "unit": "kg"}
    ]
    stock_records = []
    for stock in default_stocks:
        stock_records.append({
            "id": str(uuid.uuid4()),
            "item_name": stock["item_name"],
            "quantity_received": 0.0,
            "quantity_distributed": 0.0,
            "remaining_quantity": 0.0,
            "min_quantity": stock["min_quantity"],
            "unit": stock["unit"],
            "received_date": today_iso(),
            "supplier": "Government Supply",
            "notes": "Initial Seed Stock",
            "center_id": center_id,
            "created_at": now_iso()
        })
    try:
        supabase.table("stock_entries").insert(stock_records).execute()
    except Exception as se_err:
        logger.warning(f"Failed to seed stock entries: {se_err}")
    
    # Return the created user with center joined
    res = supabase.table("users") \
        .select("*, centers(id, center_name, district, mandal, village, address)") \
        .eq("id", user_id) \
        .execute()
    return res.data[0] if res.data else None


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return err("Authorization token missing", 401)
        token = header.split(" ", 1)[1]
        
        # 1. Check resolved user cache first to prevent database lookup bottleneck on parallel loads
        now = datetime.now(timezone.utc)
        if token in RESOLVED_USER_CACHE:
            cached_user, expiry = RESOLVED_USER_CACHE[token]
            if now < expiry:
                g.user = cached_user
                g.user_id = cached_user["id"]
                g.center_id = cached_user["center_id"]
                return f(*args, **kwargs)
            else:
                RESOLVED_USER_CACHE.pop(token, None)
        
        user_id = None
        is_supabase_user = False
        sb_user = None
        
        # 2. Try local JWT first (for demo/fallback users)
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload["sub"]
        except (jwt.InvalidSignatureError, jwt.InvalidTokenError) as local_exc:
            # 3. Try Supabase Auth verification directly via REST API
            sb_user = verify_supabase_token(token)
            if sb_user:
                user_id = sb_user.get("id")
                is_supabase_user = True
                # Check if email is verified
                if not sb_user.get("email_confirmed_at") and not sb_user.get("confirmed_at"):
                    return err("Please verify your email address before accessing the portal.", 403)
            else:
                return err("Session expired or invalid — please log in again", 401)
        except jwt.ExpiredSignatureError:
            return err("Token expired — please log in again", 401)

        # Look up user in public.users
        res = supabase.table("users") \
            .select("*, centers(id, center_name, district, mandal, village, address)") \
            .eq("id", user_id) \
            .execute()
            
        if not res.data:
            if is_supabase_user and sb_user:
                # User exists in Supabase Auth (e.g. Google Login) but profile hasn't been created yet.
                # Auto-provision profile, center, and stock config.
                provisioned_user = auto_provision_user(sb_user)
                if not provisioned_user:
                    return err("User profile provisioning failed", 500)
                g.user = provisioned_user
            else:
                return err("User not found", 401)
        else:
            g.user = res.data[0]

        g.user_id   = g.user["id"]
        g.center_id = g.user["center_id"]
        
        # Cache the resolved user details for 10 minutes
        RESOLVED_USER_CACHE[token] = (g.user, now + timedelta(minutes=10))
        return f(*args, **kwargs)
    return wrapper


# ================================================================
#  HEALTH
# ================================================================

@app.route("/", methods=["GET"])
def root():
    return send_from_directory(".", "index.html")

@app.route("/styles.css", methods=["GET"])
def serve_css():
    return send_from_directory(".", "styles.css")

@app.route("/script.js", methods=["GET"])
def serve_js():
    return send_from_directory(".", "script.js")

@app.route("/hero_illustration.png", methods=["GET"])
def serve_hero_img():
    return send_from_directory(".", "hero_illustration.png")

@app.route("/api/health", methods=["GET"])
def health():
    return ok({"status": "ok", "timestamp": now_iso()})


# ================================================================
#  AUTH
# ================================================================

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    if not data.get("email") or not data.get("password"):
        return err("Email and password are required", 400)

    email = data["email"].strip().lower()
    password = data["password"]

    # 1. Try to authenticate with Supabase Auth first
    try:
        auth_res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if auth_res and auth_res.user:
            sb_user = auth_res.user
            session = auth_res.session
            
            # Check if email is verified
            if not sb_user.email_confirmed_at and not sb_user.confirmed_at:
                return err("Please verify your email address before accessing the portal.", 403)
                
            # Fetch user profile from public.users
            res = supabase.table("users") \
                .select("*, centers(id, center_name, district, mandal, village, address)") \
                .eq("id", sb_user.id) \
                .execute()
                
            # Convert user to dict format for consistency in auto_provision_user
            sb_user_dict = {
                "id": sb_user.id,
                "email": sb_user.email,
                "user_metadata": sb_user.user_metadata,
                "email_confirmed_at": sb_user.email_confirmed_at,
                "confirmed_at": sb_user.confirmed_at
            }
            
            if not res.data:
                # User has auth record but no profile record. Auto-provision them.
                user_data = auto_provision_user(sb_user_dict)
                if not user_data:
                    return err("User profile not found", 401)
            else:
                user_data = res.data[0]
                
            return ok({
                "token": session.access_token,
                "user": {
                    "id":        user_data["id"],
                    "full_name": user_data["full_name"],
                    "email":     user_data["email"],
                    "mobile":    user_data.get("mobile", ""),
                    "center_id": user_data["center_id"],
                },
                "center": user_data.get("centers", {}),
            }, "Login successful")
    except Exception as e:
        logger.info(f"Supabase login failed: {e}. Trying local fallback...")

    # 2. Local Fallback for Demo Accounts
    res = supabase.table("users") \
        .select("*, centers(id, center_name, district, mandal, village, address)") \
        .eq("email", email) \
        .execute()

    if not res.data:
        return err("Invalid email or password", 401)

    user = res.data[0]
    if not verify_pw(password, user["password_hash"]):
        return err("Invalid email or password", 401)

    token = make_token(user["id"], user["center_id"], user["email"])
    return ok({
        "token": token,
        "user": {
            "id":        user["id"],
            "full_name": user["full_name"],
            "email":     user["email"],
            "mobile":    user.get("mobile", ""),
            "center_id": user["center_id"],
        },
        "center": user.get("centers", {}),
    }, "Login successful")


@app.route("/api/auth/logout", methods=["POST"])
@auth_required
def logout():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token = header.split(" ", 1)[1]
        TOKEN_CACHE.pop(token, None)
        RESOLVED_USER_CACHE.pop(token, None)
    return ok(None, "Logged out successfully")


@app.route("/api/auth/profile", methods=["GET"])
@auth_required
def profile():
    u = g.user
    return ok({
        "id":            u["id"],
        "full_name":     u["full_name"],
        "email":         u["email"],
        "mobile":        u.get("mobile", ""),
        "center_id":     u["center_id"],
        "profile_photo": u.get("profile_photo"),
        "center":        u.get("centers", {}),
    })


@app.route("/api/auth/profile", methods=["PUT"])
@auth_required
def update_profile():
    data = request.get_json() or {}
    allowed = ["full_name", "email", "mobile"]
    updates = {k: v.strip() for k, v in data.items() if k in allowed and v is not None}
    
    if not updates:
        return err("No valid fields to update", 400)
        
    if "full_name" in updates and not updates["full_name"]:
        return err("Full name cannot be empty", 400)
    if "email" in updates and not updates["email"]:
        return err("Email cannot be empty", 400)
        
    try:
        res = supabase.table("users").update(updates).eq("id", g.user_id).execute()
        if not res.data:
            return err("User profile not found", 404)
            
        # Evict cache
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1]
            RESOLVED_USER_CACHE.pop(token, None)
            TOKEN_CACHE.pop(token, None)
            
        return ok(res.data[0], "Profile updated successfully")
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        return err(str(e), 500)


@app.route("/api/auth/register", methods=["POST"])
def register():
    """Public registration using Supabase Auth."""
    data = request.get_json() or {}
    for f in ["full_name", "email", "password", "center_name", "district", "mandal", "village"]:
        if not data.get(f):
            return err(f"Field '{f}' is required", 400)

    if len(data["password"]) < 6:
        return err("Password must be at least 6 characters", 400)

    email = data["email"].strip().lower()
    
    # Check if email is already in public.users
    if supabase.table("users").select("id").eq("email", email).execute().data:
        return err("Email already registered", 409)

    try:
        # Create user in Supabase Auth
        auth_res = supabase.auth.sign_up({
            "email": email,
            "password": data["password"]
        })
        if not auth_res or not auth_res.user:
            return err("Registration failed on auth server", 500)
        
        sb_user = auth_res.user
    except Exception as e:
        logger.error(f"Supabase signUp error: {e}")
        return err(str(e), 400)

    # Find or create center based on center_name, district, mandal, village
    center_query = (
        supabase.table("centers")
        .select("id")
        .eq("center_name", data["center_name"].strip())
        .eq("district", data["district"].strip())
        .eq("mandal", data["mandal"].strip())
        .eq("village", data["village"].strip())
        .execute()
    )
    
    if center_query.data:
        center_id = center_query.data[0]["id"]
    else:
        # Create new center
        center_id = str(uuid.uuid4())
        center_record = {
            "id": center_id,
            "center_name": data["center_name"].strip(),
            "district": data["district"].strip(),
            "mandal": data["mandal"].strip(),
            "village": data["village"].strip(),
            "address": data.get("address", "").strip(),
            "mobile": data.get("mobile", "").strip(),
            "created_at": now_iso(),
        }
        supabase.table("centers").insert(center_record).execute()
        
        # Seed standard stock entries for new center (Initial Dashboard Configuration)
        default_stocks = [
            {"item_name": "Eggs", "min_quantity": 50.0, "unit": "units"},
            {"item_name": "Milk (Litres)", "min_quantity": 20.0, "unit": "litres"},
            {"item_name": "Dates", "min_quantity": 10.0, "unit": "kg"},
            {"item_name": "Chikki", "min_quantity": 30.0, "unit": "packets"},
            {"item_name": "Rice (kg)", "min_quantity": 40.0, "unit": "kg"},
            {"item_name": "Dal (kg)", "min_quantity": 15.0, "unit": "kg"}
        ]
        stock_records = []
        for stock in default_stocks:
            stock_records.append({
                "id": str(uuid.uuid4()),
                "item_name": stock["item_name"],
                "quantity_received": 0.0,
                "quantity_distributed": 0.0,
                "remaining_quantity": 0.0,
                "min_quantity": stock["min_quantity"],
                "unit": stock["unit"],
                "received_date": today_iso(),
                "supplier": "Government Supply",
                "notes": "Initial Seed Stock",
                "center_id": center_id,
                "created_at": now_iso()
            })
        try:
            supabase.table("stock_entries").insert(stock_records).execute()
        except Exception as se_err:
            logger.warning(f"Failed to seed stock entries: {se_err}")

    # Create the user profile in public.users linked to Supabase User ID
    record = {
        "id":            sb_user.id,
        "full_name":     data["full_name"].strip(),
        "email":         email,
        "password_hash": hash_pw(data["password"]),
        "mobile":        data.get("mobile", "").strip(),
        "center_id":     center_id,
        "created_at":    now_iso(),
    }
    
    try:
        supabase.table("users").insert(record).execute()
    except Exception as e:
        logger.error(f"Failed to insert user profile: {e}")
        # Try to delete user from Supabase Auth to keep state consistent?
        # Supabase Python SDK doesn't let us delete users unless using admin API
        return err("Registration failed: profile creation error", 500)

    token = None
    if auth_res.session:
        token = auth_res.session.access_token

    return ok({
        "token": token,
        "user": {
            "id":        record["id"],
            "full_name": record["full_name"],
            "email":     record["email"],
            "mobile":    record["mobile"],
            "center_id": record["center_id"],
        },
        "verified": sb_user.email_confirmed_at is not None or sb_user.confirmed_at is not None
    }, "Verification email sent successfully. Please check your inbox and verify your account.", 201)


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return err("Email is required", 400)
    
    try:
        supabase.auth.reset_password_for_email(email.strip().lower())
        return ok(None, "Password reset email sent successfully.")
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return err(str(e), 500)


# ================================================================
#  CENTERS
# ================================================================

@app.route("/api/centers/me", methods=["GET"])
@auth_required
def my_center():
    res = supabase.table("centers").select("*").eq("id", g.center_id).execute()
    return ok(res.data[0] if res.data else None)


@app.route("/api/centers", methods=["GET"])
def list_centers():
    res = supabase.table("centers").select("id, center_name, district, mandal, village").execute()
    return ok(res.data or [])


# ================================================================
#  CHILDREN
# ================================================================

@app.route("/api/children", methods=["GET"])
@auth_required
def get_children():
    search = request.args.get("search", "").lower()
    gender = request.args.get("gender", "")

    q = supabase.table("children").select("*").eq("center_id", g.center_id)
    if gender:
        q = q.eq("gender", gender)
    data = q.order("created_at", desc=True).execute().data or []

    if search:
        data = [c for c in data
                if search in c.get("child_name", "").lower()
                or search in c.get("parent_name", "").lower()]
    return ok(data)


@app.route("/api/children/<child_id>", methods=["GET"])
@auth_required
def get_child(child_id):
    res = supabase.table("children").select("*") \
        .eq("id", child_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("Child not found", 404)
    return ok(res.data[0])


@app.route("/api/children", methods=["POST"])
@auth_required
def create_child():
    data = request.get_json() or {}
    for f in ["child_name", "age", "gender"]:
        if data.get(f) is None or str(data.get(f, "")).strip() == "":
            return err(f"Field '{f}' is required", 400)

    try:
        age = int(data["age"])
        assert 0 <= age <= 12
    except Exception:
        return err("Age must be 0–12", 400)

    if data["gender"] not in ("Male", "Female"):
        return err("Gender must be 'Male' or 'Female'", 400)

    record = {
        "id":            str(uuid.uuid4()),
        "child_name":    data["child_name"].strip(),
        "age":           age,
        "gender":        data["gender"],
        "parent_name":   data.get("parent_name", "").strip(),
        "parent_mobile": data.get("parent_mobile", "").strip(),
        "address":       data.get("address", "").strip(),
        "center_id":     g.center_id,
        "created_at":    now_iso(),
    }
    res = supabase.table("children").insert(record).execute()
    if not res.data:
        return err("Failed to add child", 500)
    return ok(res.data[0], "Child added successfully", 201)


@app.route("/api/children/<child_id>", methods=["PUT"])
@auth_required
def update_child(child_id):
    if not supabase.table("children").select("id") \
            .eq("id", child_id).eq("center_id", g.center_id).execute().data:
        return err("Child not found", 404)

    data    = request.get_json() or {}
    allowed = {"child_name", "age", "gender", "parent_name", "parent_mobile", "address"}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return err("No valid fields to update", 400)

    res = supabase.table("children").update(updates).eq("id", child_id).execute()
    return ok(res.data[0] if res.data else None, "Child updated")


@app.route("/api/children/<child_id>", methods=["DELETE"])
@auth_required
def delete_child(child_id):
    if not supabase.table("children").select("id") \
            .eq("id", child_id).eq("center_id", g.center_id).execute().data:
        return err("Child not found", 404)
    supabase.table("children").delete().eq("id", child_id).execute()
    return ok(None, "Child deleted")


# ================================================================
#  BENEFICIARIES
# ================================================================

@app.route("/api/beneficiaries", methods=["GET"])
@auth_required
def get_beneficiaries():
    category = request.args.get("category", "")
    search   = request.args.get("search", "").lower()

    q = supabase.table("beneficiaries").select("*").eq("center_id", g.center_id)
    if category:
        q = q.eq("category", category)
    data = q.order("created_at", desc=True).execute().data or []

    if search:
        data = [b for b in data if search in b.get("name", "").lower()]
    return ok(data)


@app.route("/api/beneficiaries", methods=["POST"])
@auth_required
def create_beneficiary():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("category"):
        return err("Fields 'name' and 'category' are required", 400)

    if data["category"] not in ("Pregnant Woman", "Lactating Mother"):
        return err("Category must be 'Pregnant Woman' or 'Lactating Mother'", 400)

    record = {
        "id":         str(uuid.uuid4()),
        "name":       data["name"].strip(),
        "category":   data["category"],
        "mobile":     data.get("mobile", "").strip(),
        "address":    data.get("address", "").strip(),
        "center_id":  g.center_id,
        "created_at": now_iso(),
    }
    res = supabase.table("beneficiaries").insert(record).execute()
    if not res.data:
        return err("Failed to add beneficiary", 500)
    return ok(res.data[0], "Beneficiary added", 201)


@app.route("/api/beneficiaries/<bid>", methods=["PUT"])
@auth_required
def update_beneficiary(bid):
    if not supabase.table("beneficiaries").select("id") \
            .eq("id", bid).eq("center_id", g.center_id).execute().data:
        return err("Beneficiary not found", 404)

    data    = request.get_json() or {}
    allowed = {"name", "category", "mobile", "address"}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return err("No valid fields", 400)

    res = supabase.table("beneficiaries").update(updates).eq("id", bid).execute()
    return ok(res.data[0] if res.data else None, "Beneficiary updated")


@app.route("/api/beneficiaries/<bid>", methods=["DELETE"])
@auth_required
def delete_beneficiary(bid):
    if not supabase.table("beneficiaries").select("id") \
            .eq("id", bid).eq("center_id", g.center_id).execute().data:
        return err("Beneficiary not found", 404)
    supabase.table("beneficiaries").delete().eq("id", bid).execute()
    return ok(None, "Beneficiary deleted")


# ================================================================
#  STOCK
# ================================================================

@app.route("/api/stocks", methods=["GET"])
@auth_required
def get_stocks():
    data = supabase.table("stock_entries").select("*") \
        .eq("center_id", g.center_id).order("created_at", desc=True).execute().data or []
    for item in data:
        item["low_stock"] = (item.get("remaining_quantity") or 0) <= (item.get("min_quantity") or 20)
    return ok(data)


@app.route("/api/stocks/add", methods=["POST"])
@auth_required
def add_stock():
    data = request.get_json() or {}
    if not data.get("item_name") or not data.get("quantity_received"):
        return err("Fields 'item_name' and 'quantity_received' are required", 400)

    try:
        qty = float(data["quantity_received"])
        assert qty > 0
    except Exception:
        return err("quantity_received must be a positive number", 400)

    # Upsert: add to existing item if same name
    existing = supabase.table("stock_entries") \
        .select("*").eq("center_id", g.center_id) \
        .eq("item_name", data["item_name"]).execute().data

    if existing:
        item = existing[0]
        updates = {
            "quantity_received":  item["quantity_received"] + qty,
            "remaining_quantity": item["remaining_quantity"] + qty,
            "received_date":      data.get("received_date", today_iso()),
        }
        res = supabase.table("stock_entries").update(updates).eq("id", item["id"]).execute()
        _log_stock(item["id"], "Added", qty, data.get("supplier", ""), g.center_id)
        return ok(res.data[0] if res.data else None, f"Stock updated: +{qty}")

    record = {
        "id":                   str(uuid.uuid4()),
        "item_name":            data["item_name"].strip(),
        "quantity_received":    qty,
        "quantity_distributed": 0,
        "remaining_quantity":   qty,
        "min_quantity":         float(data.get("min_quantity") or 20),
        "unit":                 data.get("unit", "units"),
        "received_date":        data.get("received_date", today_iso()),
        "supplier":             data.get("supplier", "").strip(),
        "notes":                data.get("notes", "").strip(),
        "center_id":            g.center_id,
        "created_at":           now_iso(),
    }
    res = supabase.table("stock_entries").insert(record).execute()
    if not res.data:
        return err("Failed to add stock", 500)

    _log_stock(record["id"], "Added", qty, data.get("supplier", ""), g.center_id)
    return ok(res.data[0], "Stock added", 201)


@app.route("/api/stocks/<stock_id>", methods=["PUT"])
@auth_required
def update_stock(stock_id):
    item = supabase.table("stock_entries").select("*") \
        .eq("id", stock_id).eq("center_id", g.center_id).execute().data
    if not item:
        return err("Stock item not found", 404)

    data    = request.get_json() or {}
    allowed = {"item_name", "quantity_received", "remaining_quantity",
               "min_quantity", "unit", "supplier", "notes", "received_date"}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return err("No valid fields", 400)

    res = supabase.table("stock_entries").update(updates).eq("id", stock_id).execute()
    return ok(res.data[0] if res.data else None, "Stock updated")


@app.route("/api/stocks/<stock_id>", methods=["DELETE"])
@auth_required
def delete_stock(stock_id):
    if not supabase.table("stock_entries").select("id") \
            .eq("id", stock_id).eq("center_id", g.center_id).execute().data:
        return err("Stock item not found", 404)
    supabase.table("stock_entries").delete().eq("id", stock_id).execute()
    return ok(None, "Stock item deleted")


@app.route("/api/stocks/distribute", methods=["POST"])
@auth_required
def distribute_stock():
    data = request.get_json() or {}
    for f in ["stock_id", "quantity", "distributed_to"]:
        if not data.get(f):
            return err(f"Field '{f}' is required", 400)

    try:
        qty = float(data["quantity"])
        assert qty > 0
    except Exception:
        return err("Quantity must be a positive number", 400)

    stock = supabase.table("stock_entries").select("*") \
        .eq("id", data["stock_id"]).eq("center_id", g.center_id).execute().data
    if not stock:
        return err("Stock item not found", 404)

    item = stock[0]
    remaining = item.get("remaining_quantity") or 0
    if remaining < qty:
        return err(f"Insufficient stock — available: {remaining} {item.get('unit','units')}", 400)

    new_remaining = remaining - qty
    new_dist      = (item.get("quantity_distributed") or 0) + qty

    supabase.table("stock_entries").update({
        "quantity_distributed": new_dist,
        "remaining_quantity":   new_remaining,
    }).eq("id", item["id"]).execute()

    dist_record = {
        "id":                str(uuid.uuid4()),
        "stock_id":          item["id"],
        "item_name":         item["item_name"],
        "quantity":          qty,
        "distributed_to":    data["distributed_to"].strip(),
        "distribution_date": data.get("distribution_date", today_iso()),
        "distributed_by":    data.get("distributed_by", g.user.get("full_name", "Staff")),
        "beneficiary_id":    data.get("beneficiary_id"),
        "center_id":         g.center_id,
        "created_at":        now_iso(),
    }
    supabase.table("stock_distribution").insert(dist_record).execute()
    _log_stock(item["id"], "Distributed", qty, data["distributed_to"], g.center_id)

    return ok({
        "item_name":          item["item_name"],
        "distributed":        qty,
        "remaining_quantity": new_remaining,
        "unit":               item.get("unit", "units"),
        "low_stock":          new_remaining <= (item.get("min_quantity") or 20),
    }, f"Distributed {qty} {item.get('unit','units')} of {item['item_name']}")


@app.route("/api/stocks/history", methods=["GET"])
@auth_required
def stock_history():
    data = supabase.table("stock_distribution").select("*") \
        .eq("center_id", g.center_id).order("created_at", desc=True).execute().data or []
    return ok(data)


@app.route("/api/stocks/logs", methods=["GET"])
@auth_required
def stock_logs():
    data = supabase.table("stock_logs").select("*") \
        .eq("center_id", g.center_id).order("created_at", desc=True).execute().data or []
    return ok(data)


def _log_stock(stock_id, action, qty, detail, center_id):
    try:
        supabase.table("stock_logs").insert({
            "id":         str(uuid.uuid4()),
            "stock_id":   stock_id,
            "action":     action,
            "quantity":   qty,
            "detail":     detail or "",
            "center_id":  center_id,
            "created_at": now_iso(),
        }).execute()
    except Exception as exc:
        logger.warning(f"Stock log failed: {exc}")


# ================================================================
#  BMI & NUTRITION
# ================================================================

@app.route("/api/bmi", methods=["GET"])
@auth_required
def get_bmi_records():
    """GET /api/bmi?child_id=&category=&search="""
    child_id = request.args.get("child_id", "")
    category = request.args.get("category", "")
    search   = request.args.get("search", "").lower()

    q = supabase.table("bmi_records").select("*").eq("center_id", g.center_id)
    if child_id:
        q = q.eq("child_id", child_id)
    if category:
        q = q.eq("bmi_category", category)

    data = q.order("measurement_date", desc=True).execute().data or []
    if search:
        data = [r for r in data if search in r.get("child_name", "").lower()]
    return ok(data)


@app.route("/api/bmi/<record_id>", methods=["GET"])
@auth_required
def get_bmi_record(record_id):
    res = supabase.table("bmi_records").select("*") \
        .eq("id", record_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("BMI record not found", 404)
    return ok(res.data[0])


@app.route("/api/bmi", methods=["POST"])
@auth_required
def create_bmi_record():
    """POST /api/bmi
    Body: { child_id?, child_name, age, gender, height_cm, weight_kg,
            measurement_date?, notes?, ai_recommendation? }
    """
    data = request.get_json() or {}
    required_fields = ["child_name", "age", "gender", "height_cm", "weight_kg"]
    for f in required_fields:
        if data.get(f) is None:
            return err(f"Field '{f}' is required", 400)

    try:
        height = float(data["height_cm"])
        weight = float(data["weight_kg"])
        age    = int(data["age"])
        assert height >= 40 and weight >= 2 and 0 <= age <= 12
    except Exception:
        return err("height_cm ≥ 40, weight_kg ≥ 2, age 0–12", 400)

    if data["gender"] not in ("Male", "Female"):
        return err("Gender must be 'Male' or 'Female'", 400)

    bmi      = compute_bmi(height, weight)
    category = classify_bmi(bmi)
    status   = BMI_NUTRITION_STATUS[category]

    record = {
        "id":                  str(uuid.uuid4()),
        "child_id":            data.get("child_id") or None,
        "center_id":           g.center_id,
        "recorded_by":         g.user_id,
        "child_name":          data["child_name"].strip(),
        "age_at_measurement":  age,
        "gender":              data["gender"],
        "height_cm":           height,
        "weight_kg":           weight,
        "bmi_value":           bmi,
        "bmi_category":        category,
        "nutrition_status":    status,
        "ai_recommendation":   data.get("ai_recommendation"),
        "measurement_date":    data.get("measurement_date", today_iso()),
        "notes":               data.get("notes", "").strip(),
        "created_at":          now_iso(),
    }

    try:
        res = supabase.table("bmi_records").insert(record).execute()
        if not res.data:
            return err("Failed to save BMI record", 500)
        return ok(res.data[0], "BMI record saved", 201)
    except Exception as e:
        logger.error(f"Error saving BMI record: {e}", exc_info=True)
        return err(f"Database error: {str(e)}", 500)


@app.route("/api/bmi/<record_id>", methods=["PUT"])
@auth_required
def update_bmi_record(record_id):
    existing = supabase.table("bmi_records").select("*") \
        .eq("id", record_id).eq("center_id", g.center_id).execute().data
    if not existing:
        return err("BMI record not found", 404)

    data    = request.get_json() or {}
    updates = {}

    # Recalculate BMI if measurements changed
    height = float(data.get("height_cm") or existing[0]["height_cm"])
    weight = float(data.get("weight_kg") or existing[0]["weight_kg"])

    if "height_cm" in data or "weight_kg" in data:
        bmi           = compute_bmi(height, weight)
        category      = classify_bmi(bmi)
        updates.update({
            "height_cm":         height,
            "weight_kg":         weight,
            "bmi_value":         bmi,
            "bmi_category":      category,
            "nutrition_status":  BMI_NUTRITION_STATUS[category],
            "ai_recommendation": None,  # reset AI cache on re-measurement
        })

    allowed = {"child_name", "age_at_measurement", "gender",
               "measurement_date", "notes", "ai_recommendation"}
    updates.update({k: v for k, v in data.items() if k in allowed and v is not None})

    if not updates:
        return err("No valid fields to update", 400)

    try:
        res = supabase.table("bmi_records").update(updates).eq("id", record_id).execute()
        return ok(res.data[0] if res.data else None, "BMI record updated")
    except Exception as e:
        logger.error(f"Error updating BMI record: {e}", exc_info=True)
        return err(f"Database error: {str(e)}", 500)


@app.route("/api/bmi/<record_id>", methods=["DELETE"])
@auth_required
def delete_bmi_record(record_id):
    if not supabase.table("bmi_records").select("id") \
            .eq("id", record_id).eq("center_id", g.center_id).execute().data:
        return err("BMI record not found", 404)
    try:
        supabase.table("bmi_records").delete().eq("id", record_id).execute()
        return ok(None, "BMI record deleted")
    except Exception as e:
        logger.error(f"Error deleting BMI record: {e}", exc_info=True)
        return err(f"Database error: {str(e)}", 500)


@app.route("/api/bmi/<record_id>/ai", methods=["PATCH"])
@auth_required
def save_ai_recommendation(record_id):
    """PATCH /api/bmi/<id>/ai — { ai_recommendation: {...} }"""
    data = request.get_json() or {}
    if "ai_recommendation" not in data:
        return err("Field 'ai_recommendation' is required", 400)

    if not supabase.table("bmi_records").select("id") \
            .eq("id", record_id).eq("center_id", g.center_id).execute().data:
        return err("BMI record not found", 404)

    res = supabase.table("bmi_records") \
        .update({"ai_recommendation": data["ai_recommendation"]}) \
        .eq("id", record_id).execute()
    return ok(res.data[0] if res.data else None, "AI recommendation saved")


@app.route("/api/bmi/<record_id>/generate-ai", methods=["POST"])
@auth_required
def generate_ai_recommendation(record_id):
    """
    POST /api/bmi/<id>/generate-ai
    Calls Gemini 1.5 Flash to generate a full nutrition recommendation
    for the child, stores it in bmi_records, and returns it.
    """
    if not gemini_model:
        return err(
            "Gemini AI is not configured. Please set GEMINI_API_KEY in .env",
            503
        )

    # Fetch the BMI record
    res = supabase.table("bmi_records").select("*") \
        .eq("id", record_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("BMI record not found", 404)

    rec = res.data[0]

    # Build the prompt
    prompt = f"""You are a certified child nutrition assistant working with the Indian government's Anganwadi (ICDS) program.

A child has been measured at an Anganwadi center. Based on the following data, provide a complete, practical, and compassionate nutrition recommendation suitable for rural Indian families.

CHILD DETAILS:
- Name: {rec['child_name']}
- Age: {rec['age_at_measurement']} years
- Gender: {rec['gender']}
- Height: {rec['height_cm']} cm
- Weight: {rec['weight_kg']} kg
- BMI: {rec['bmi_value']}
- BMI Category: {rec['bmi_category']}
- Nutrition Status: {rec.get('nutrition_status', '')}
- Measurement Date: {rec.get('measurement_date', '')}

INSTRUCTIONS:
Respond ONLY in valid JSON format with exactly this structure — no markdown, no extra text:

{{
  "assessment": "2–3 sentence clinical summary of the child's nutritional status based on BMI and age",
  "recommended_foods": ["food1", "food2", "food3", "food4", "food5", "food6", "food7", "food8"],
  "foods_to_avoid": ["food1", "food2", "food3", "food4"],
  "daily_meals": {{
    "Early Morning (6-7am)": "specific Indian meal suggestion",
    "Breakfast (8-9am)": "specific Indian meal suggestion",
    "Mid Morning (11am)": "healthy snack suggestion",
    "Lunch (1pm)": "specific Indian meal suggestion",
    "Evening (4pm)": "healthy snack suggestion",
    "Dinner (7pm)": "specific Indian meal suggestion"
  }},
  "health_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
  "followup": "Specific follow-up action and timeline recommendation for Anganwadi staff"
}}

IMPORTANT:
- All food recommendations must be affordable, locally available in rural Telangana/Andhra Pradesh
- Use simple Telugu-friendly food names where appropriate (e.g., ragi, jowar, bajra, dal, sabzi)
- Recommendations must be age-appropriate for {rec['age_at_measurement']}-year-old children
- Be specific — no generic advice
- For Severe Underweight: recommend urgent intervention, therapeutic foods, PHC referral
- For Normal: focus on maintaining and variety
- For Overweight/Obese: focus on activity and reducing junk food without restricting calories
"""

    try:
        logger.info(f"Calling Gemini for BMI record {record_id} — {rec['child_name']}")
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature":     0.3,
                "top_p":           0.8,
                "max_output_tokens": 1500,
            }
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        import json
        ai_data = json.loads(raw)

        # Validate required keys
        required_keys = {"assessment", "recommended_foods", "foods_to_avoid",
                         "daily_meals", "health_tips", "followup"}
        missing = required_keys - set(ai_data.keys())
        if missing:
            return err(f"Gemini response missing fields: {missing}", 502)

        # Save to database
        supabase.table("bmi_records") \
            .update({"ai_recommendation": ai_data}) \
            .eq("id", record_id).execute()

        logger.info(f"✅ Gemini AI recommendation saved for {rec['child_name']}")
        return ok(ai_data, "AI recommendation generated successfully")

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}\nRaw: {raw[:300]}")
        return err("Gemini returned malformed JSON. Please try again.", 502)

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return err(f"AI generation failed: {str(e)}", 502)


@app.route("/api/generate-nutrition", methods=["POST"])
def generate_nutrition_public():
    """
    POST /api/generate-nutrition
    Public endpoint to generate AI recommendations from raw JSON data (for local frontend).
    """
    if not gemini_model:
        return err(
            "Gemini AI is not configured. Please set GEMINI_API_KEY in .env",
            503
        )

    data = request.get_json() or {}
    required = ["child_name", "age", "gender", "height_cm", "weight_kg", "bmi_value", "bmi_category"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return err(f"Missing fields: {', '.join(missing)}", 400)

    prompt = f"""You are a certified child nutrition assistant working with the Indian government's Anganwadi (ICDS) program.

A child has been measured at an Anganwadi center. Based on the following data, provide a complete, practical, and compassionate nutrition recommendation suitable for rural Indian families.

CHILD DETAILS:
- Name: {data['child_name']}
- Age: {data['age']} years
- Gender: {data['gender']}
- Height: {data['height_cm']} cm
- Weight: {data['weight_kg']} kg
- BMI: {data['bmi_value']}
- BMI Category: {data['bmi_category']}
- Nutrition Status: {data.get('nutrition_status', '')}
- Measurement Date: {data.get('measurement_date', '')}

INSTRUCTIONS:
Respond ONLY in valid JSON format with exactly this structure — no markdown, no extra text:

{{
  "assessment": "2–3 sentence clinical summary of the child's nutritional status based on BMI and age",
  "recommended_foods": ["food1", "food2", "food3", "food4", "food5", "food6", "food7", "food8"],
  "foods_to_avoid": ["food1", "food2", "food3", "food4"],
  "daily_meals": {{
    "Early Morning (6-7am)": "specific Indian meal suggestion",
    "Breakfast (8-9am)": "specific Indian meal suggestion",
    "Mid Morning (11am)": "healthy snack suggestion",
    "Lunch (1pm)": "specific Indian meal suggestion",
    "Evening (4pm)": "healthy snack suggestion",
    "Dinner (7pm)": "specific Indian meal suggestion"
  }},
  "health_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
  "followup": "Specific follow-up action and timeline recommendation for Anganwadi staff"
}}

IMPORTANT:
- All food recommendations must be affordable, locally available in rural Telangana/Andhra Pradesh
- Use simple Telugu-friendly food names where appropriate (e.g., ragi, jowar, bajra, dal, sabzi)
- Recommendations must be age-appropriate for {data['age']}-year-old children
- Be specific — no generic advice
- For Severe Underweight: recommend urgent intervention, therapeutic foods, PHC referral
- For Normal: focus on maintaining and variety
- For Overweight/Obese: focus on activity and reducing junk food without restricting calories
"""

    try:
        logger.info(f"Calling Gemini for public nutrition endpoint — {data['child_name']}")
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature":     0.3,
                "top_p":           0.8,
                "max_output_tokens": 1500,
            }
        )

        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        import json
        ai_data = json.loads(raw)

        return ok(ai_data, "AI recommendation generated successfully")

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return err(f"AI generation failed: {str(e)}", 502)


@app.route("/api/bmi/summary", methods=["GET"])
@auth_required
def bmi_summary():
    """GET /api/bmi/summary — counts by category for dashboard widgets."""
    data = supabase.table("bmi_records").select("bmi_category") \
        .eq("center_id", g.center_id).execute().data or []

    cats  = ["Severe Underweight", "Underweight", "Normal", "Overweight", "Obese"]
    total = len(data)
    counts = {c: sum(1 for r in data if r.get("bmi_category") == c) for c in cats}

    return ok({
        "total":             total,
        "by_category":       counts,
        "normal_count":      counts["Normal"],
        "underweight_count": counts["Underweight"],
        "severe_count":      counts["Severe Underweight"],
        "overweight_count":  counts["Overweight"],
        "obese_count":       counts["Obese"],
        "needs_attention":   counts["Severe Underweight"] + counts["Underweight"],
    })


# ================================================================
#  DAILY MEALS
# ================================================================

@app.route("/api/daily-meals", methods=["GET"])
@auth_required
def get_daily_meals():
    data = supabase.table("daily_meals").select("*") \
        .eq("center_id", g.center_id).order("meal_date", desc=True).execute().data or []
    return ok(data)

@app.route("/api/daily-meals", methods=["POST"])
@auth_required
def save_daily_meal():
    data = request.get_json() or {}
    meal_date = data.get("meal_date", today_iso())
    
    existing = supabase.table("daily_meals").select("*") \
        .eq("center_id", g.center_id).eq("meal_date", meal_date).execute().data
        
    record = {
        "children_served": int(data.get("children_served", 0)),
        "beneficiaries_served": int(data.get("beneficiaries_served", 0)),
        "menu_served": data.get("menu_served", "").strip(),
        "center_id": g.center_id,
        "meal_date": meal_date,
    }
    
    if existing:
        res = supabase.table("daily_meals").update(record).eq("id", existing[0]["id"]).execute()
        return ok(res.data[0] if res.data else None, "Meal record updated")
    else:
        record["id"] = str(uuid.uuid4())
        record["created_at"] = now_iso()
        res = supabase.table("daily_meals").insert(record).execute()
        if not res.data:
            return err("Failed to save meal record", 500)
        return ok(res.data[0], "Meal record saved", 201)


# ================================================================
#  MEETINGS
# ================================================================


# ================================================================
#  STUDENT ATTENDANCE
# ================================================================

@app.route("/api/attendance", methods=["GET"])
@auth_required
def get_attendance():
    date_str = request.args.get("date", today_iso())
    data = supabase.table("attendance").select("*") \
        .eq("center_id", g.center_id).eq("attendance_date", date_str).execute().data or []
    return ok(data)

@app.route("/api/attendance", methods=["POST"])
@auth_required
def save_attendance():
    data = request.get_json() or {}
    date_str = data.get("date", today_iso())
    records = data.get("records", {})
    
    # Delete existing records for this date and center
    supabase.table("attendance").delete().eq("center_id", g.center_id).eq("attendance_date", date_str).execute()
    
    inserts = []
    for child_id, status in records.items():
        if status in ("Present", "Absent"):
            inserts.append({
                "child_id": child_id,
                "center_id": g.center_id,
                "attendance_date": date_str,
                "status": status,
                "recorded_by": g.user_id,
                "created_at": now_iso()
            })
            
    if inserts:
        res = supabase.table("attendance").insert(inserts).execute()
        if not hasattr(res, 'data') and res is None:
            return err("Failed to save attendance", 500)
    return ok(None, "Attendance saved successfully", 201)


@app.route("/api/attendance/history", methods=["GET"])
@auth_required
def get_attendance_history():
    """Get summarized attendance history for all dates for this center."""
    att_logs = supabase.table("attendance").select("*").eq("center_id", g.center_id).execute().data or []
    
    # Group by date locally
    from collections import defaultdict
    grouped = defaultdict(list)
    for log in att_logs:
        grouped[log.get("attendance_date")].append(log)
        
    history = []
    for date_str, logs in grouped.items():
        records = {l["child_id"]: l["status"] for l in logs}
        history.append({
            "date": date_str,
            "records": records,
            "saved": True
        })
        
    # Sort history by date descending
    history.sort(key=lambda x: x["date"], reverse=True)
    return ok(history)


# ================================================================
#  ATTENDANCE PHOTOS (Supabase Storage + DB)
# ================================================================


@app.route("/api/attendance/photos", methods=["POST"])
@auth_required
def upload_attendance_photo():
    """Accept JSON: { filename, content_base64, child_id? , notes? }
    Stores the file in Supabase Storage and records metadata in DB.
    """
    data = request.get_json() or {}
    for f in ("filename", "content_base64"):
        if not data.get(f):
            return err("Fields 'filename' and 'content_base64' are required", 400)

    filename = data["filename"].strip()
    ext = os.path.splitext(filename)[1] if os.path.splitext(filename)[1] else ".jpg"
    path = f"{g.center_id}/{str(uuid.uuid4())}{ext}"

    try:
        file_bytes = base64.b64decode(data["content_base64"])
    except Exception:
        return err("Invalid base64 image data", 400)

    try:
        supabase.storage.from_(SUPABASE_PHOTO_BUCKET).upload(path, file_bytes)
    except Exception as e:
        logger.warning(f"Attendance photo upload failed: {e}")
        return err("Failed to upload image to storage", 500)

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_PHOTO_BUCKET}/{path}"

    record = {
        "id":         str(uuid.uuid4()),
        "image_path": path,
        "image_url":  public_url,
        "child_id":   data.get("child_id"),
        "upload_date": data.get("upload_date", today_iso()),
        "uploaded_by": g.user_id,
        "center_id":  g.center_id,
        "notes":      data.get("notes", ""),
        "created_at": now_iso(),
    }

    res = supabase.table("attendance_photos").insert(record).execute()
    if not res.data:
        return err("Failed to save photo metadata", 500)
    return ok(res.data[0], "Photo uploaded", 201)


@app.route("/api/attendance/photos", methods=["GET"])
@auth_required
def list_attendance_photos():
    """List attendance photos for the logged-in user's center."""
    child_id = request.args.get("child_id")
    q = supabase.table("attendance_photos").select("*").eq("center_id", g.center_id)
    if child_id:
        q = q.eq("child_id", child_id)
    data = q.order("created_at", desc=True).execute().data or []
    return ok(data)


@app.route("/api/attendance/photos/<photo_id>", methods=["DELETE"])
@auth_required
def delete_attendance_photo(photo_id):
    res = supabase.table("attendance_photos").select("*") \
        .eq("id", photo_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("Photo not found", 404)
    photo = res.data[0]

    # Attempt to remove from storage (ignore errors but log)
    try:
        supabase.storage.from_(SUPABASE_PHOTO_BUCKET).remove([photo.get("image_path")])
    except Exception as e:
        logger.warning(f"Failed to delete storage object {photo.get('image_path')}: {e}")

    supabase.table("attendance_photos").delete().eq("id", photo_id).execute()
    return ok(None, "Photo deleted")


@app.route("/api/meetings", methods=["GET"])
@auth_required
def get_meetings():
    filter_val = request.args.get("filter", "all")
    data = supabase.table("meetings").select("*") \
        .eq("center_id", g.center_id).order("meeting_date").execute().data or []

    now_str = now_iso()
    if filter_val == "upcoming":
        data = [m for m in data if m.get("meeting_date", "") >= now_str]
    elif filter_val == "past":
        data = [m for m in data if m.get("meeting_date", "") < now_str]
    return ok(data)


@app.route("/api/meetings", methods=["POST"])
@auth_required
def create_meeting():
    data = request.get_json() or {}
    if not data.get("title") or not data.get("meeting_date"):
        return err("'title' and 'meeting_date' are required", 400)

    record = {
        "id":           str(uuid.uuid4()),
        "title":        data["title"].strip(),
        "description":  data.get("description", "").strip(),
        "meeting_date": data["meeting_date"],
        "location":     data.get("location", "Center Hall").strip(),
        "center_id":    g.center_id,
        "created_by":   g.user_id,
        "created_at":   now_iso(),
    }
    res = supabase.table("meetings").insert(record).execute()
    if not res.data:
        return err("Failed to create meeting", 500)
    return ok(res.data[0], "Meeting created", 201)


@app.route("/api/meetings/<mid>", methods=["PUT"])
@auth_required
def update_meeting(mid):
    if not supabase.table("meetings").select("id") \
            .eq("id", mid).eq("center_id", g.center_id).execute().data:
        return err("Meeting not found", 404)

    data    = request.get_json() or {}
    allowed = {"title", "description", "meeting_date", "location"}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return err("No valid fields", 400)

    res = supabase.table("meetings").update(updates).eq("id", mid).execute()
    return ok(res.data[0] if res.data else None, "Meeting updated")


@app.route("/api/meetings/<mid>", methods=["DELETE"])
@auth_required
def delete_meeting(mid):
    if not supabase.table("meetings").select("id") \
            .eq("id", mid).eq("center_id", g.center_id).execute().data:
        return err("Meeting not found", 404)
    supabase.table("meetings").delete().eq("id", mid).execute()
    return ok(None, "Meeting deleted")


# ================================================================
#  STORIES
# ================================================================

@app.route("/api/stories", methods=["GET"])
@auth_required
def get_stories():
    language     = request.args.get("language", "")
    category     = request.args.get("category", "")
    content_type = request.args.get("content_type", "")
    search       = request.args.get("search", "").lower()

    # Return ALL global stories + stories from the user's own center
    q = supabase.table("stories").select("*")
    if language:
        q = q.eq("language", language)
    if category:
        q = q.eq("category", category)
    if content_type:
        q = q.eq("content_type", content_type)

    all_data = q.order("uploaded_at", desc=True).execute().data or []

    # Filter: keep global stories OR stories from this center
    data = [
        s for s in all_data
        if s.get("is_global", True) or s.get("center_id") == g.center_id
    ]

    if search:
        data = [s for s in data
                if search in s.get("title", "").lower()
                or search in (s.get("preview") or "").lower()]
    return ok(data)


@app.route("/api/stories", methods=["POST"])
@auth_required
def upload_story():
    data = request.get_json() or {}
    if not data.get("title") or not data.get("language"):
        return err("'title' and 'language' are required", 400)

    if data["language"] not in ("English", "Telugu", "Hindi"):
        return err("Language must be English, Telugu, or Hindi", 400)

    content_type = data.get("content_type", "text")
    if content_type not in ("url", "video", "pdf", "text"):
        return err("content_type must be url, video, pdf, or text", 400)

    # Validate required fields per content_type
    url_link    = data.get("url_link", "").strip()
    pdf_url     = data.get("pdf_url", "").strip()
    video_url   = data.get("video_url", "").strip()
    youtube_url = data.get("youtube_url", "").strip()
    audio_url   = data.get("audio_url", "").strip()

    if content_type == "url" and not url_link:
        return err("url_link is required for content_type 'url'", 400)
    if content_type == "pdf" and not pdf_url:
        return err("pdf_url is required for content_type 'pdf'", 400)
    if content_type == "video" and not (video_url or youtube_url):
        return err("video_url or youtube_url is required for content_type 'video'", 400)

    is_global = bool(data.get("is_global", True))   # default: visible to all

    record = {
        "id":           str(uuid.uuid4()),
        "title":        data["title"].strip(),
        "language":     data["language"],
        "category":     data.get("category", "Moral Stories"),
        "emoji":        data.get("emoji", "📖"),
        "preview":      data.get("preview", "").strip(),
        "has_audio":    bool(audio_url),
        "content_type": content_type,
        "url_link":     url_link,
        "pdf_url":      pdf_url,
        "audio_url":    audio_url,
        "video_url":    video_url,
        "youtube_url":  youtube_url,
        "is_global":    is_global,
        "center_id":    g.center_id,
        "uploaded_by":  g.user_id,
        "uploaded_at":  now_iso(),
    }
    res = supabase.table("stories").insert(record).execute()
    if not res.data:
        return err("Failed to upload story", 500)
    return ok(res.data[0], "Story uploaded", 201)


@app.route("/api/stories/<story_id>", methods=["DELETE"])
@auth_required
def delete_story(story_id):
    if not supabase.table("stories").select("id") \
            .eq("id", story_id).eq("center_id", g.center_id).execute().data:
        return err("Story not found", 404)
    supabase.table("stories").delete().eq("id", story_id).execute()
    return ok(None, "Story deleted")


@app.route("/api/stories/<story_id>", methods=["PUT"])
@auth_required
def update_story(story_id):
    """Update story with new media files."""
    data = request.get_json() or {}
    
    # Check story exists
    story = supabase.table("stories").select("*").eq("id", story_id).eq("center_id", g.center_id).execute().data
    if not story:
        return err("Story not found", 404)
    
    # Update allowed fields
    update_data = {}
    if "title" in data:
        update_data["title"] = data["title"].strip()
    if "preview" in data:
        update_data["preview"] = data["preview"].strip()
    if "pdf_url" in data:
        update_data["pdf_url"] = data["pdf_url"].strip()
    if "video_url" in data:
        update_data["video_url"] = data["video_url"].strip()
    if "youtube_url" in data:
        update_data["youtube_url"] = data["youtube_url"].strip()
    if "audio_url" in data:
        update_data["audio_url"] = data["audio_url"].strip()
        update_data["has_audio"] = bool(data["audio_url"].strip())
    
    if not update_data:
        return err("No valid fields to update", 400)
    
    res = supabase.table("stories").update(update_data).eq("id", story_id).execute()
    if not res.data:
        return err("Update failed", 500)
    
    return ok(res.data[0], "Story updated successfully")


@app.route("/api/upload/file", methods=["POST"])
@auth_required
def upload_file():
    """
    Upload PDF, video, or audio file to Supabase Storage.
    Buckets used:
      story-pdfs   → PDF files  (10 MB max)
      story-videos → Video files (100 MB max)
      story-audio  → Audio files (20 MB max)
    Create each bucket in Supabase Storage → mark as Public.
    """

    if 'file' not in request.files:
        return err("No file provided", 400)

    file = request.files['file']
    if file.filename == '':
        return err("No file selected", 400)

    from werkzeug.utils import secure_filename
    import time

    filename  = secure_filename(file.filename)
    ext       = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # Auto-detect the exact bucket name the user created for PDFs
    pdf_bucket_name = "story-pdfs"
    try:
        buckets = supabase.storage.list_buckets()
        for b in buckets:
            b_name = b.name.lower()
            if "stor" in b_name and "pdf" in b_name:
                pdf_bucket_name = b.id
                break
    except:
        pass

    # Map extension → (file_type, bucket_name)
    EXT_MAP = {
        'pdf':  ('pdf',   pdf_bucket_name),
        'mp4':  ('video', 'story-videos'),
        'webm': ('video', 'story-videos'),
        'avi':  ('video', 'story-videos'),
        'mov':  ('video', 'story-videos'),
        'mkv':  ('video', 'story-videos'),
        'mp3':  ('audio', 'story-audio'),
        'wav':  ('audio', 'story-audio'),
    }
    if ext not in EXT_MAP:
        return err(f"File type .{ext} not allowed. Allowed: pdf, mp4, webm, avi, mov, mkv, mp3, wav", 400)

    file_type, bucket = EXT_MAP[ext]

    # Size limits: PDF 10MB, audio 20MB, video 100MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    max_mb   = {'pdf': 10, 'audio': 20, 'video': 100}[file_type]
    max_size = max_mb * 1024 * 1024
    if file_size > max_size:
        return err(f"File too large. Max {max_mb}MB for {file_type} files.", 400)

    # Unique filename: center_id/timestamp_filename
    unique_name = f"{g.center_id}/{int(time.time())}_{filename}"

    try:
        # Force the bucket to be public just in case
        try:
            supabase.storage.update_bucket(bucket, options={"public": True})
        except:
            pass

        supabase.storage.from_(bucket).upload(
            unique_name,
            file.read(),
            {"content-type": file.content_type or 'application/octet-stream'}
        )
        file_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        return ok(
            {"file_url": file_url, "filename": unique_name, "file_type": file_type, "bucket": bucket},
            "File uploaded successfully"
        )
    except Exception as e:
        logger.error(f"File upload error ({bucket}): {str(e)}")
        err_str = str(e)
        if "Bucket not found" in err_str or "bucket" in err_str.lower():
            return err(
                f"Storage bucket '{bucket}' not found. "
                f"Go to Supabase → Storage → New Bucket → name it '{bucket}' → enable Public.", 400
            )
        return err(f"File upload failed: {err_str}", 500)


# ================================================================
#  SURVEYS
# ================================================================

@app.route("/api/surveys", methods=["GET"])
@auth_required
def get_surveys():
    data  = supabase.table("surveys_feedback").select("*") \
        .eq("center_id", g.center_id).order("submitted_at", desc=True).execute().data or []
    total = len(data)
    avg   = round(sum(s.get("rating", 0) for s in data) / total, 2) if total else 0
    dist  = {str(r): sum(1 for s in data if s.get("rating") == r) for r in range(1, 6)}
    return ok({
        "feedback": data,
        "summary": {
            "total":               total,
            "average_rating":      avg,
            "rating_distribution": dist,
            "positive":            sum(1 for s in data if s.get("rating", 0) >= 4),
        },
    })


@app.route("/api/surveys", methods=["POST"])
@auth_required
def submit_survey():
    data = request.get_json() or {}
    for f in ["parent_name", "feedback", "rating"]:
        if not data.get(f):
            return err(f"Field '{f}' is required", 400)

    try:
        rating = int(data["rating"])
        assert 1 <= rating <= 5
    except Exception:
        return err("Rating must be 1–5", 400)

    record = {
        "id":           str(uuid.uuid4()),
        "parent_name":  data["parent_name"].strip(),
        "mobile":       data.get("mobile", "").strip(),
        "feedback":     data["feedback"].strip(),
        "rating":       rating,
        "center_id":    g.center_id,
        "submitted_at": now_iso(),
    }
    res = supabase.table("surveys_feedback").insert(record).execute()
    if not res.data:
        return err("Failed to submit feedback", 500)
    return ok(res.data[0], "Feedback submitted", 201)


# ================================================================
#  DASHBOARD
# ================================================================

@app.route("/api/dashboard", methods=["GET"])
@auth_required
def dashboard():
    cid     = g.center_id
    now_str = now_iso()

    children      = supabase.table("children").select("id, age, gender") \
        .eq("center_id", cid).execute().data or []
    beneficiaries = supabase.table("beneficiaries").select("id, category") \
        .eq("center_id", cid).execute().data or []
    stocks        = supabase.table("stock_entries").select("id, remaining_quantity, min_quantity") \
        .eq("center_id", cid).execute().data or []
    meetings      = supabase.table("meetings").select("id, title, meeting_date, location") \
        .eq("center_id", cid).gte("meeting_date", now_str).order("meeting_date").limit(5).execute().data or []
    bmi_data      = supabase.table("bmi_records").select("id, bmi_category, child_name") \
        .eq("center_id", cid).execute().data or []
    recent_kids   = supabase.table("children").select("id, child_name, age, gender, parent_name") \
        .eq("center_id", cid).order("created_at", desc=True).limit(5).execute().data or []

    low_stock = [s for s in stocks if
                 (s.get("remaining_quantity") or 0) <= (s.get("min_quantity") or 20)]

    bmi_cats = {}
    for r in bmi_data:
        cat = r.get("bmi_category", "Unknown")
        bmi_cats[cat] = bmi_cats.get(cat, 0) + 1

    return ok({
        "stats": {
            "total_children":        len(children),
            "total_beneficiaries":   len(beneficiaries),
            "total_stock_items":     len(stocks),
            "low_stock_count":       len(low_stock),
            "upcoming_meetings":     len(meetings),
            "total_bmi_records":     len(bmi_data),
            "normal_bmi_count":      bmi_cats.get("Normal", 0),
            "underweight_count":     bmi_cats.get("Underweight", 0),
            "severe_count":          bmi_cats.get("Severe Underweight", 0),
            "overweight_count":      bmi_cats.get("Overweight", 0),
            "pregnant_women":        sum(1 for b in beneficiaries if b.get("category") == "Pregnant Woman"),
            "lactating_mothers":     sum(1 for b in beneficiaries if b.get("category") == "Lactating Mother"),
        },
        "low_stock_alerts":  [{"name": s.get("item_name", ""), **s} for s in low_stock],
        "upcoming_meetings": meetings,
        "recent_children":   recent_kids,
        "bmi_alerts": [
            r for r in bmi_data
            if r.get("bmi_category") in ("Severe Underweight", "Underweight")
        ],
    })


# ================================================================
#  REPORTS
# ================================================================

@app.route("/api/reports/summary", methods=["GET"])
@auth_required
def reports_summary():
    cid = g.center_id

    children      = supabase.table("children").select("id, age, gender").eq("center_id", cid).execute().data or []
    beneficiaries = supabase.table("beneficiaries").select("id, category").eq("center_id", cid).execute().data or []
    stocks        = supabase.table("stock_entries").select("id, item_name, remaining_quantity, quantity_distributed, unit, min_quantity").eq("center_id", cid).execute().data or []
    dists         = supabase.table("stock_distribution").select("id, quantity").eq("center_id", cid).execute().data or []
    stories       = supabase.table("stories").select("id, language, has_audio").eq("center_id", cid).execute().data or []
    meetings      = supabase.table("meetings").select("id").eq("center_id", cid).execute().data or []
    bmi_data      = supabase.table("bmi_records").select("id, bmi_category, age_at_measurement, gender").eq("center_id", cid).execute().data or []

    return ok({
        "children": {
            "total":  len(children),
            "boys":   sum(1 for c in children if c.get("gender") == "Male"),
            "girls":  sum(1 for c in children if c.get("gender") == "Female"),
            "under3": sum(1 for c in children if (c.get("age") or 0) < 3),
            "under5": sum(1 for c in children if 3 <= (c.get("age") or 0) <= 5),
        },
        "beneficiaries": {
            "total":             len(beneficiaries),
            "pregnant_women":    sum(1 for b in beneficiaries if b.get("category") == "Pregnant Woman"),
            "lactating_mothers": sum(1 for b in beneficiaries if b.get("category") == "Lactating Mother"),
        },
        "stock": {
            "total_items":        len(stocks),
            "total_distributed":  sum(d.get("quantity") or 0 for d in dists),
            "low_stock_items":    [s for s in stocks if (s.get("remaining_quantity") or 0) <= (s.get("min_quantity") or 20)],
            "items":              stocks,
        },
        "stories": {
            "total":      len(stories),
            "with_audio": sum(1 for s in stories if s.get("has_audio")),
        },
        "meetings": {"total": len(meetings)},
        "bmi": {
            "total":              len(bmi_data),
            "normal":             sum(1 for r in bmi_data if r.get("bmi_category") == "Normal"),
            "underweight":        sum(1 for r in bmi_data if r.get("bmi_category") == "Underweight"),
            "severe_underweight": sum(1 for r in bmi_data if r.get("bmi_category") == "Severe Underweight"),
            "overweight":         sum(1 for r in bmi_data if r.get("bmi_category") == "Overweight"),
            "obese":              sum(1 for r in bmi_data if r.get("bmi_category") == "Obese"),
            "needs_attention":    sum(1 for r in bmi_data if r.get("bmi_category") in ("Severe Underweight", "Underweight")),
        },
    })
# ================================================================
#  REPORTLAB PDF GENERATION & HEADING CANVAS
# ================================================================

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically calculate the total page count
    and render a professional header/footer on every page.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Draw clean footer line
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(1)
        self.line(36, 45, 559, 45)  # Page margin left/right are 36
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        self.drawString(36, 30, "Smart Anganwadi Portal — Digital Management System")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 30, page_text)
        
        # Draw header decoration band
        self.setFillColor(colors.HexColor("#4F46E5"))
        self.rect(0, 834, 595, 8, fill=True, stroke=False) # Top margin colored band
        
        self.restoreState()


def compile_pdf(report_type, center, staff_name, date_str, data):
    """
    Build a professional PDF document using ReportLab.
    """
    buffer = io.BytesIO()
    
    # Page dimensions A4: 595.27 x 841.89 points. Margins 0.5 inch (36 points)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=36, 
        rightMargin=36, 
        topMargin=54, 
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'HeaderTitle', 
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#FFFFFF"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'HeaderSub', 
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#E0E7FF"),
        spaceAfter=2
    )
    
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#1F2937")
    )
    
    body_normal = ParagraphStyle(
        'BodyNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#374151")
    )
    
    body_light = ParagraphStyle(
        'BodyLight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#6B7280")
    )
    
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )

    story = []
    
    # ── 1. MAIN BANNER ──────────────────────────────────────────────
    # Clean professional header table
    header_data = [
        [
            Paragraph("🏫 Smart Anganwadi Portal", title_style),
            Paragraph(f"<b>Report:</b> {report_type.upper()}<br/><b>Date:</b> {date_str}", ParagraphStyle('HdrR', parent=subtitle_style, alignment=2))
        ],
        [
            Paragraph(f"Center: {center.get('center_name', 'N/A')} | Village: {center.get('village', 'N/A')} | Mandal: {center.get('mandal', 'N/A')} | District: {center.get('district', 'N/A')}", subtitle_style),
            Paragraph(f"Generated by: {staff_name}", ParagraphStyle('HdrR2', parent=subtitle_style, alignment=2))
        ]
    ]
    
    header_table = Table(header_data, colWidths=[320, 203])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#4F46E5")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # ── 2. STATISTICS WIDGET CARDS ──────────────────────────────────
    stats = data.get("stats", {})
    if stats:
        stats_cols = []
        for label, val in stats.items():
            card_text = f"<b>{label}</b><br/><font size=14 color='#4F46E5'><b>{val}</b></font>"
            stats_cols.append(Paragraph(card_text, ParagraphStyle('CardText', parent=body_normal, leading=14, alignment=1)))
            
        stats_table = Table([stats_cols], colWidths=[523.0 / len(stats_cols)] * len(stats_cols))
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 15))

    # ── 3. DATA TABLES ──────────────────────────────────────────────
    columns = data.get("columns", [])
    records = data.get("records", [])
    
    if columns and records:
        table_rows = []
        # Header Row
        table_rows.append([Paragraph(c, table_hdr_style) for c in columns])
        
        # Record Rows
        for rec in records:
            row_cells = []
            for val in rec:
                if isinstance(val, (int, float)):
                    row_cells.append(Paragraph(str(val), body_bold))
                else:
                    row_cells.append(Paragraph(str(val or '—'), body_normal))
            table_rows.append(row_cells)
            
        col_width = 523.0 / len(columns)
        main_table = Table(table_rows, colWidths=[col_width] * len(columns))
        
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ]
        
        # Alternate row backgrounds
        for idx in range(1, len(table_rows)):
            if idx % 2 == 0:
                t_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#F9FAFB")))
                
        main_table.setStyle(TableStyle(t_style))
        story.append(main_table)
        
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ================================================================
#  VILLAGERS REGISTRY ENDPOINTS
# ================================================================

@app.route("/api/villagers", methods=["GET"])
@auth_required
def get_villagers():
    """Retrieve all villagers for the staff center."""
    category = request.args.get("category")
    q = supabase.table("villagers").select("*").eq("center_id", g.center_id)
    if category:
        q = q.eq("category", category)
    res = q.order("name").execute()
    return ok(res.data or [])

@app.route("/api/villagers", methods=["POST"])
@auth_required
def create_villager():
    """Register a new villager."""
    data = request.get_json() or {}
    
    # Required fields
    required = ["name", "age", "gender", "category"]
    for field in required:
        if data.get(field) is None or str(data.get(field)).strip() == "":
            return err(f"Field '{field}' is required", 400)
            
    name = data["name"].strip()
    gender = data["gender"].strip()
    category = data["category"].strip()
    contact = data.get("contact_number", "").strip() if data.get("contact_number") else None
    address = data.get("address", "").strip() if data.get("address") else None
    
    try:
        age = int(data["age"])
        assert age >= 0
    except Exception:
        return err("Age must be a non-negative integer", 400)
        
    if gender not in ["Male", "Female"]:
        return err("Gender must be 'Male' or 'Female'", 400)
        
    valid_categories = ["Child", "Pregnant Woman", "Lactating Mother", "General Resident"]
    if category not in valid_categories:
        return err(f"Category must be one of {valid_categories}", 400)
        
    record = {
        "id": str(uuid.uuid4()),
        "name": name,
        "age": age,
        "gender": gender,
        "category": category,
        "contact_number": contact,
        "address": address,
        "center_id": g.center_id,
        "created_at": now_iso()
    }
    
    res = supabase.table("villagers").insert(record).execute()
    if not res.data:
        return err("Failed to register villager", 500)
    return ok(res.data[0], "Villager registered successfully", 201)

@app.route("/api/villagers/<vid>", methods=["PUT"])
@auth_required
def update_villager(vid):
    """Modify details of an existing villager."""
    existing = supabase.table("villagers").select("id").eq("id", vid).eq("center_id", g.center_id).execute().data
    if not existing:
        return err("Villager record not found", 404)
        
    data = request.get_json() or {}
    allowed = ["name", "age", "gender", "category", "contact_number", "address"]
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    
    if "name" in updates:
        updates["name"] = updates["name"].strip()
        if not updates["name"]:
            return err("Name cannot be empty", 400)
            
    if "age" in updates:
        try:
            updates["age"] = int(updates["age"])
            assert updates["age"] >= 0
        except Exception:
            return err("Age must be a non-negative integer", 400)
            
    if "gender" in updates:
        updates["gender"] = updates["gender"].strip()
        if updates["gender"] not in ["Male", "Female"]:
            return err("Gender must be 'Male' or 'Female'", 400)
            
    if "category" in updates:
        updates["category"] = updates["category"].strip()
        valid_categories = ["Child", "Pregnant Woman", "Lactating Mother", "General Resident"]
        if updates["category"] not in valid_categories:
            return err(f"Category must be one of {valid_categories}", 400)
            
    if "contact_number" in updates:
        updates["contact_number"] = updates["contact_number"].strip() if updates["contact_number"] else None
        
    if "address" in updates:
        updates["address"] = updates["address"].strip() if updates["address"] else None
        
    if not updates:
        return err("No valid fields to update", 400)
        
    res = supabase.table("villagers").update(updates).eq("id", vid).execute()
    return ok(res.data[0] if res.data else None, "Villager record updated successfully")

@app.route("/api/villagers/<vid>", methods=["DELETE"])
@auth_required
def delete_villager(vid):
    """Remove a villager record."""
    existing = supabase.table("villagers").select("id").eq("id", vid).eq("center_id", g.center_id).execute().data
    if not existing:
        return err("Villager record not found", 404)
        
    supabase.table("villagers").delete().eq("id", vid).execute()
    return ok(None, "Villager record deleted successfully")


# ================================================================
#  VILLAGE SURVEY ENDPOINTS
# ================================================================

@app.route("/api/village-surveys", methods=["GET"])
@auth_required
def get_village_surveys():
    """Retrieve all village surveys for the staff center."""
    res = supabase.table("village_survey") \
        .select("*") \
        .eq("center_id", g.center_id) \
        .order("survey_year", desc=True) \
        .order("survey_month", desc=True) \
        .execute()
    return ok(res.data or [])


@app.route("/api/village-surveys", methods=["POST"])
@auth_required
def create_village_survey():
    """Submit a monthly or yearly village survey."""
    data = request.get_json() or {}
    
    # Required fields
    required = ["village_name", "total_population", "total_families", "total_children", "pregnant_women", "lactating_mothers", "survey_year"]
    for field in required:
        if data.get(field) is None or str(data.get(field)).strip() == "":
            return err(f"Field '{field}' is required", 400)

    try:
        pop = int(data["total_population"])
        families = int(data["total_families"])
        kids = int(data["total_children"])
        preg = int(data["pregnant_women"])
        lact = int(data["lactating_mothers"])
        year = int(data["survey_year"])
        
        # Month is optional (Yearly survey if blank or None)
        month_val = data.get("survey_month")
        month = int(month_val) if (month_val is not None and str(month_val).strip() != "") else None
        
        assert pop >= 0 and families >= 0 and kids >= 0 and preg >= 0 and lact >= 0 and year >= 2000
        if month is not None:
            assert 1 <= month <= 12
    except Exception:
        return err("Ensure demographic counts are non-negative, year >= 2000, and month is 1-12 or blank.", 400)

    # Perform partial constraint validation locally
    q = supabase.table("village_survey") \
        .select("id") \
        .eq("center_id", g.center_id) \
        .eq("survey_year", year)
        
    if month is not None:
        q = q.eq("survey_month", month)
    else:
        q = q.is_("survey_month", "null")
        
    if q.execute().data:
        period_str = f"month {month}" if month else "yearly"
        return err(f"A survey for year {year} ({period_str}) already exists for this center.", 409)

    record = {
        "id": str(uuid.uuid4()),
        "village_name": data["village_name"].strip(),
        "total_population": pop,
        "total_families": families,
        "total_children": kids,
        "pregnant_women": preg,
        "lactating_mothers": lact,
        "survey_year": year,
        "survey_month": month,
        "center_id": g.center_id,
        "created_at": now_iso()
    }
    
    res = supabase.table("village_survey").insert(record).execute()
    if not res.data:
        return err("Failed to insert survey record", 500)
    return ok(res.data[0], "Survey record created successfully", 201)


@app.route("/api/village-surveys/<sid>", methods=["PUT"])
@auth_required
def update_village_survey(sid):
    """Modify details of an existing survey record."""
    # Check existence
    existing = supabase.table("village_survey").select("id").eq("id", sid).eq("center_id", g.center_id).execute().data
    if not existing:
        return err("Survey record not found", 404)
        
    data = request.get_json() or {}
    allowed = ["village_name", "total_population", "total_families", "total_children", "pregnant_women", "lactating_mothers", "survey_year", "survey_month"]
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    
    # Types formatting
    for num_f in ["total_population", "total_families", "total_children", "pregnant_women", "lactating_mothers", "survey_year"]:
        if num_f in updates:
            try:
                updates[num_f] = int(updates[num_f])
                assert updates[num_f] >= 0
            except Exception:
                return err(f"Invalid numeric input for '{num_f}'", 400)
                
    if "survey_month" in updates:
        m = updates["survey_month"]
        if m is not None and str(m).strip() != "":
            try:
                updates["survey_month"] = int(m)
                assert 1 <= updates["survey_month"] <= 12
            except Exception:
                return err("Month must be 1-12", 400)
        else:
            updates["survey_month"] = None

    if not updates:
        return err("No valid fields to update", 400)

    res = supabase.table("village_survey").update(updates).eq("id", sid).execute()
    return ok(res.data[0] if res.data else None, "Survey record updated successfully")


@app.route("/api/village-surveys/<sid>", methods=["DELETE"])
@auth_required
def delete_village_survey(sid):
    """Delete a survey record."""
    existing = supabase.table("village_survey").select("id").eq("id", sid).eq("center_id", g.center_id).execute().data
    if not existing:
        return err("Survey record not found", 404)
        
    supabase.table("village_survey").delete().eq("id", sid).execute()
    return ok(None, "Survey record deleted successfully")


# ================================================================
#  PDF REPORTS ENDPOINTS
# ================================================================

@app.route("/api/reports/history", methods=["GET"])
@auth_required
def get_reports_history():
    """Retrieve history list of previously generated reports for the center."""
    res = supabase.table("reports") \
        .select("*") \
        .eq("center_id", g.center_id) \
        .order("created_at", desc=True) \
        .execute()
    return ok(res.data or [])


@app.route("/api/reports/generate", methods=["POST"])
@auth_required
def generate_report():
    """
    POST /api/reports/generate
    Body: { "report_type": "stock" | "distribution" | "children" | "attendance" | "bmi" | "beneficiary" | "survey" }
    
    Generates a PDF using ReportLab, uploads to Supabase Storage, registers 
    in the database, and returns the file directly as an attachment.
    """
    data = request.get_json() or {}
    report_type = data.get("report_type", "").lower()
    
    VALID_TYPES = ["stock", "distribution", "children", "attendance", "bmi", "beneficiary", "survey", "villagers"]
    if report_type not in VALID_TYPES:
        return err(f"Invalid report type. Allowed: {', '.join(VALID_TYPES)}", 400)
        
    cid = g.center_id
    staff_name = g.user.get("full_name", "Staff Member")
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    
    # Fetch Center Details
    center = supabase.table("centers").select("*").eq("id", cid).execute().data
    center_info = center[0] if center else {}
    
    # Compile metrics and table rows depending on report type
    report_data = {
        "stats": {},
        "columns": [],
        "records": []
    }
    
    if report_type == "stock":
        entries = supabase.table("stock_entries").select("*").eq("center_id", cid).order("item_name").execute().data or []
        report_data["stats"] = {
            "Total Stock Types": len(entries),
            "Low Stock Alerts": sum(1 for s in entries if (s.get("remaining_quantity") or 0) <= (s.get("min_quantity") or 20)),
            "Available Supply": sum(s.get("remaining_quantity") or 0 for s in entries)
        }
        report_data["columns"] = ["Item Name", "Qty Received", "Distributed", "Remaining", "Min Alert Level", "Unit"]
        report_data["records"] = [
            [
                s.get("item_name"), 
                s.get("quantity_received"), 
                s.get("quantity_distributed"), 
                s.get("remaining_quantity"), 
                s.get("min_quantity"), 
                s.get("unit")
            ]
            for s in entries
        ]
        
    elif report_type == "distribution":
        dists = supabase.table("stock_distribution").select("*").eq("center_id", cid).order("distribution_date", desc=True).execute().data or []
        report_data["stats"] = {
            "Distribution Runs": len(dists),
            "Total Quantity Out": sum(d.get("quantity") or 0 for d in dists)
        }
        report_data["columns"] = ["Distribution Date", "Item Name", "Quantity", "Distributed To", "Distributed By"]
        report_data["records"] = [
            [
                d.get("distribution_date"),
                d.get("item_name"),
                d.get("quantity"),
                d.get("distributed_to"),
                d.get("distributed_by")
            ]
            for d in dists
        ]
        
    elif report_type == "children":
        kids = supabase.table("children").select("*").eq("center_id", cid).order("child_name").execute().data or []
        report_data["stats"] = {
            "Total Enrolled Children": len(kids),
            "Boys": sum(1 for k in kids if k.get("gender") == "Male"),
            "Girls": sum(1 for k in kids if k.get("gender") == "Female")
        }
        report_data["columns"] = ["Child Name", "Age (years)", "Gender", "Parent Name", "Parent Mobile"]
        report_data["records"] = [
            [
                k.get("child_name"),
                k.get("age"),
                k.get("gender"),
                k.get("parent_name"),
                k.get("parent_mobile")
            ]
            for k in kids
        ]
        
    elif report_type == "attendance":
        att_logs = supabase.table("attendance").select("*").eq("center_id", cid).execute().data or []
        # Group by date locally
        from collections import defaultdict
        grouped = defaultdict(list)
        for log in att_logs:
            grouped[log.get("attendance_date")].append(log)
            
        records_summary = []
        total_p_rate = 0.0
        
        for date_key, logs in grouped.items():
            tot = len(logs)
            present = sum(1 for l in logs if l.get("status") == "Present")
            absent = tot - present
            pct = round((present / tot) * 100, 1) if tot > 0 else 0
            records_summary.append([date_key, tot, present, absent, f"{pct}%"])
            total_p_rate += pct
            
        records_summary.sort(key=lambda x: x[0], reverse=True)
        avg_pct = round(total_p_rate / len(grouped), 1) if grouped else 0.0
        
        report_data["stats"] = {
            "Total Tracking Days": len(grouped),
            "Average Attendance Rate": f"{avg_pct}%"
        }
        report_data["columns"] = ["Attendance Date", "Total Marked", "Present", "Absent", "Rate %"]
        report_data["records"] = records_summary
        
    elif report_type == "bmi":
        bmis = supabase.table("bmi_records").select("*").eq("center_id", cid).order("measurement_date", desc=True).execute().data or []
        report_data["stats"] = {
            "BMI Records Compiled": len(bmis),
            "Severe Underweight Case Count": sum(1 for b in bmis if b.get("bmi_category") == "Severe Underweight"),
            "Underweight Count": sum(1 for b in bmis if b.get("bmi_category") == "Underweight"),
            "Normal Range Count": sum(1 for b in bmis if b.get("bmi_category") == "Normal")
        }
        report_data["columns"] = ["Child Name", "Age", "Gender", "Height (cm)", "Weight (kg)", "BMI Value", "Category", "Date Measured"]
        report_data["records"] = [
            [
                b.get("child_name"),
                b.get("age_at_measurement"),
                b.get("gender"),
                b.get("height_cm"),
                b.get("weight_kg"),
                b.get("bmi_value"),
                b.get("bmi_category"),
                b.get("measurement_date")
            ]
            for b in bmis
        ]
        
    elif report_type == "beneficiary":
        benefs = supabase.table("beneficiaries").select("*").eq("center_id", cid).order("name").execute().data or []
        report_data["stats"] = {
            "Total Beneficiaries": len(benefs),
            "Pregnant Women": sum(1 for b in benefs if b.get("category") == "Pregnant Woman"),
            "Lactating Mothers": sum(1 for b in benefs if b.get("category") == "Lactating Mother")
        }
        report_data["columns"] = ["Beneficiary Name", "Category", "Mobile Contact", "Address"]
        report_data["records"] = [
            [
                b.get("name"),
                b.get("category"),
                b.get("mobile"),
                b.get("address")
            ]
            for b in benefs
        ]
        
    elif report_type == "survey":
        surveys = supabase.table("village_survey").select("*").eq("center_id", cid).order("survey_year", desc=True).order("survey_month", desc=True).execute().data or []
        latest = surveys[0] if surveys else {}
        report_data["stats"] = {
            "Total Surveys Logged": len(surveys),
            "Latest Village Pop": latest.get("total_population", "—"),
            "Latest Enrolled Families": latest.get("total_families", "—")
        }
        report_data["columns"] = ["Village Name", "Year", "Month", "Population", "Families", "Children", "Pregnant Women", "Lactating Mothers"]
        report_data["records"] = [
            [
                s.get("village_name"),
                s.get("survey_year"),
                s.get("survey_month") or "Yearly",
                s.get("total_population"),
                s.get("total_families"),
                s.get("total_children"),
                s.get("pregnant_women"),
                s.get("lactating_mothers")
            ]
            for s in surveys
        ]

    elif report_type == "villagers":
        villagers = supabase.table("villagers").select("*").eq("center_id", cid).order("name").execute().data or []
        report_data["stats"] = {
            "Total Registered Villagers": len(villagers),
            "Children": sum(1 for v in villagers if v.get("category") == "Child"),
            "Pregnant Women": sum(1 for v in villagers if v.get("category") == "Pregnant Woman"),
            "Lactating Mothers": sum(1 for v in villagers if v.get("category") == "Lactating Mother"),
            "General Residents": sum(1 for v in villagers if v.get("category") == "General Resident")
        }
        report_data["columns"] = ["Name", "Age", "Gender", "Category", "Contact Number", "Address"]
        report_data["records"] = [
            [
                v.get("name"),
                v.get("age"),
                v.get("gender"),
                v.get("category"),
                v.get("contact_number") or "—",
                v.get("address") or "—"
            ]
            for v in villagers
        ]

    try:
        # Generate the ReportLab PDF binary bytes
        pdf_bytes = compile_pdf(report_type, center_info, staff_name, date_str, report_data)
        
        # Unique filename upload
        filename = f"{cid}/{report_type}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
        
        # Verify or create the storage bucket named 'reports' programmatically
        try:
            buckets = supabase.storage.list_buckets()
            names = [b.name for b in buckets] if buckets else []
            if 'reports' not in names:
                supabase.storage.create_bucket('reports', {'public': True})
        except Exception:
            pass # continue and attempt upload
            
        supabase.storage.from_("reports").upload(filename, pdf_bytes, {"content-type": "application/pdf"})
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/reports/{filename}"
        
        # Log to Database table `reports`
        log_record = {
            "id": str(uuid.uuid4()),
            "report_type": report_type.replace('_', ' ').capitalize(),
            "pdf_url": public_url,
            "generated_by": staff_name,
            "center_id": cid,
            "created_at": now_iso()
        }
        supabase.table("reports").insert(log_record).execute()
        
        # Stream the file content directly back to client
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{report_type}_report_{datetime.now(timezone.utc).date().isoformat()}.pdf"
        )
    except Exception as e:
        logger.error(f"Report generation/upload error: {str(e)}")
        return err(f"Could not build report PDF: {str(e)}", 500)


# ================================================================
#  DEV SEED ENDPOINT  (one-shot: call once then remove)
# ================================================================

@app.route("/api/dev/create-buckets", methods=["GET"])
def create_storage_buckets():
    """
    One-shot: creates story-pdfs, story-videos and story-audio buckets in Supabase Storage.
    Visit http://localhost:5000/api/dev/create-buckets once to run.
    """
    results = []
    buckets_to_create = [
        {"id": "story-pdfs",   "name": "story-pdfs",   "public": True},
        {"id": "story-videos", "name": "story-videos", "public": True},
        {"id": "story-audio",  "name": "story-audio",  "public": True},
    ]
    for b in buckets_to_create:
        try:
            supabase.storage.create_bucket(b["id"], options={"public": b["public"]})
            results.append(f"✅ Created bucket: {b['id']} (public={b['public']})")
        except Exception as e:
            err_msg = str(e)
            if "already exists" in err_msg.lower() or "duplicate" in err_msg.lower():
                results.append(f"ℹ️  Bucket '{b['id']}' already exists — skipped")
            else:
                results.append(f"❌ Failed to create '{b['id']}': {err_msg}")
    return ok({"results": results}, "Bucket creation complete")


@app.route("/api/dev/seed-demo", methods=["GET"])
def seed_demo():
    """
    One-shot seeder for Teacher & Staff demo accounts.
    Inserts isolated children / beneficiaries / stock for
    centers 22222222 (Gandhi Nagar) and 33333333 (Nehru Colony).
    """
    import uuid as _uuid
    def uid(): return str(_uuid.uuid4())

    TEACHER = "22222222-2222-2222-2222-222222222222"
    STAFF   = "33333333-3333-3333-3333-333333333333"

    results = []

    # ── Teacher children ────────────────────────────────────────────
    try:
        r = supabase.table("children").insert([
            {"id":uid(),"child_name":"Ramya Reddy",   "age":4,"gender":"Female","parent_name":"Vinod Reddy",  "parent_mobile":"9222111001","center_id":TEACHER},
            {"id":uid(),"child_name":"Suresh Yadav",  "age":5,"gender":"Male",  "parent_name":"Kishore Yadav","parent_mobile":"9222111002","center_id":TEACHER},
            {"id":uid(),"child_name":"Kavitha Nair",  "age":3,"gender":"Female","parent_name":"Arun Nair",    "parent_mobile":"9222111003","center_id":TEACHER},
            {"id":uid(),"child_name":"Nikhil Sharma", "age":6,"gender":"Male",  "parent_name":"Deepak Sharma","parent_mobile":"9222111004","center_id":TEACHER},
            {"id":uid(),"child_name":"Pooja Devi",    "age":4,"gender":"Female","parent_name":"Mahesh Devi",  "parent_mobile":"9222111005","center_id":TEACHER},
            {"id":uid(),"child_name":"Rajan Kumar",   "age":7,"gender":"Male",  "parent_name":"Sanjay Kumar", "parent_mobile":"9222111006","center_id":TEACHER},
        ]).execute()
        results.append(f"Teacher children: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Teacher children ERROR: {e}")

    # ── Teacher beneficiaries ────────────────────────────────────────
    try:
        r = supabase.table("beneficiaries").insert([
            {"id":uid(),"name":"Meena Sharma",  "category":"Pregnant Woman",  "mobile":"9222222001","address":"Colony A, Gandhi Nagar","center_id":TEACHER},
            {"id":uid(),"name":"Rekha Devi",    "category":"Lactating Mother","mobile":"9222222002","address":"Street 3, Gandhi Nagar","center_id":TEACHER},
            {"id":uid(),"name":"Sunita Rao",    "category":"Pregnant Woman",  "mobile":"9222222003","address":"Plot 12, Gandhi Nagar", "center_id":TEACHER},
            {"id":uid(),"name":"Kavitha Pillai","category":"Lactating Mother","mobile":"9222222004","address":"Block B, Gandhi Nagar", "center_id":TEACHER},
        ]).execute()
        results.append(f"Teacher beneficiaries: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Teacher beneficiaries ERROR: {e}")

    # ── Teacher stock ────────────────────────────────────────────────
    try:
        r = supabase.table("stock_entries").insert([
            {"id":uid(),"item_name":"Rice (kg)",    "quantity_received":90, "quantity_distributed":15,"remaining_quantity":75, "min_quantity":30,"unit":"kg",     "received_date":"2024-07-01","supplier":"Government Ration","center_id":TEACHER},
            {"id":uid(),"item_name":"Eggs",         "quantity_received":200,"quantity_distributed":40,"remaining_quantity":160,"min_quantity":40,"unit":"units",  "received_date":"2024-07-01","supplier":"Government Supply","center_id":TEACHER},
            {"id":uid(),"item_name":"Milk (Litres)","quantity_received":30, "quantity_distributed":8, "remaining_quantity":22, "min_quantity":15,"unit":"litres", "received_date":"2024-07-02","supplier":"Local Dairy",      "center_id":TEACHER},
            {"id":uid(),"item_name":"Chikki",       "quantity_received":40, "quantity_distributed":20,"remaining_quantity":20, "min_quantity":20,"unit":"packets","received_date":"2024-07-02","supplier":"Health Department","center_id":TEACHER},
        ]).execute()
        results.append(f"Teacher stock: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Teacher stock ERROR: {e}")

    # ── Staff children ───────────────────────────────────────────────
    try:
        r = supabase.table("children").insert([
            {"id":uid(),"child_name":"Aditya Singh", "age":5,"gender":"Male",  "parent_name":"Rajesh Singh",  "parent_mobile":"9333111001","center_id":STAFF},
            {"id":uid(),"child_name":"Ananya Joshi", "age":4,"gender":"Female","parent_name":"Pradeep Joshi", "parent_mobile":"9333111002","center_id":STAFF},
            {"id":uid(),"child_name":"Bhavesh Patel","age":6,"gender":"Male",  "parent_name":"Amit Patel",    "parent_mobile":"9333111003","center_id":STAFF},
            {"id":uid(),"child_name":"Deepika Rao",  "age":3,"gender":"Female","parent_name":"Venkat Rao",    "parent_mobile":"9333111004","center_id":STAFF},
            {"id":uid(),"child_name":"Ganesh Babu",  "age":5,"gender":"Male",  "parent_name":"Ravi Babu",     "parent_mobile":"9333111005","center_id":STAFF},
        ]).execute()
        results.append(f"Staff children: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Staff children ERROR: {e}")

    # ── Staff beneficiaries ──────────────────────────────────────────
    try:
        r = supabase.table("beneficiaries").insert([
            {"id":uid(),"name":"Saradha Bai","category":"Pregnant Woman",  "mobile":"9333222001","address":"Lane 2, Nehru Colony",   "center_id":STAFF},
            {"id":uid(),"name":"Tulasi Devi","category":"Lactating Mother","mobile":"9333222002","address":"Ward 7, Nehru Colony",   "center_id":STAFF},
            {"id":uid(),"name":"Usha Rani",  "category":"Pregnant Woman",  "mobile":"9333222003","address":"Sector 4, Nehru Colony","center_id":STAFF},
        ]).execute()
        results.append(f"Staff beneficiaries: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Staff beneficiaries ERROR: {e}")

    # ── Staff stock ──────────────────────────────────────────────────
    try:
        r = supabase.table("stock_entries").insert([
            {"id":uid(),"item_name":"Rice (kg)","quantity_received":70, "quantity_distributed":10,"remaining_quantity":60, "min_quantity":25,"unit":"kg",   "received_date":"2024-07-01","supplier":"Government Ration","center_id":STAFF},
            {"id":uid(),"item_name":"Eggs",     "quantity_received":150,"quantity_distributed":30,"remaining_quantity":120,"min_quantity":30,"unit":"units","received_date":"2024-07-01","supplier":"Government Supply","center_id":STAFF},
            {"id":uid(),"item_name":"Dal (kg)", "quantity_received":25, "quantity_distributed":5, "remaining_quantity":20, "min_quantity":10,"unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
            {"id":uid(),"item_name":"Dates",    "quantity_received":20, "quantity_distributed":8, "remaining_quantity":12, "min_quantity":8, "unit":"kg",   "received_date":"2024-07-02","supplier":"Government Supply","center_id":STAFF},
        ]).execute()
        results.append(f"Staff stock: {len(r.data)} inserted")
    except Exception as e:
        results.append(f"Staff stock ERROR: {e}")

    return ok({"seeded": results}, "Demo seeding complete")


@app.route("/api/diagnose", methods=["GET"])
def api_diagnose():
    try:
        import os
        from flask import jsonify
        db_url = os.getenv("SUPABASE_URL")
        db_key_len = len(os.getenv("SUPABASE_KEY") or "")
        
        # Test Supabase connection inside Flask context
        from supabase import create_client
        client = create_client(db_url, os.getenv("SUPABASE_KEY"))
        test_centers = client.table("centers").select("id").limit(1).execute()
        
        # Query users database records
        db_users = client.table("users")\
            .select("email, full_name, center_id, centers(center_name)")\
            .execute()
        
        return jsonify({
            "success": True,
            "supabase_url": db_url,
            "supabase_key_len": db_key_len,
            "centers_data": test_centers.data,
            "users_in_db": db_users.data,
            "message": "Supabase connection verified successfully within Flask context!"
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/dev/test-token", methods=["GET"])
def test_token():
    token = request.args.get("token")
    if not token:
        return jsonify({"success": False, "message": "Token query parameter is required"}), 400
    
    results = {}
    try:
        # 1. Attempt using supabase.auth.get_user(token)
        try:
            res = supabase.auth.get_user(token)
            if res and res.user:
                results["supabase_sdk"] = {
                    "success": True,
                    "user_id": res.user.id,
                    "email": res.user.email,
                    "user_metadata": res.user.user_metadata
                }
            else:
                results["supabase_sdk"] = {
                    "success": False,
                    "message": "Returned empty user"
                }
        except Exception as e:
            import traceback
            results["supabase_sdk"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
        # 2. Attempt using raw urllib to rule out SDK issues
        try:
            import urllib.request
            import urllib.error
            import ssl
            import json
            
            url = f"{SUPABASE_URL}/auth/v1/user"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("apikey", SUPABASE_KEY)
            
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                body = response.read().decode("utf-8")
                results["urllib"] = {
                    "success": True,
                    "status": response.status,
                    "data": json.loads(body)
                }
        except urllib.error.HTTPError as e:
            results["urllib"] = {
                "success": False,
                "status": e.code,
                "error": e.read().decode("utf-8")
            }
        except Exception as e:
            import traceback
            results["urllib"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    if path.startswith("api"):
        return jsonify({"success": False, "message": f"API endpoint not found: /{path}"}), 404
        
    # Standardize path
    safe_path = path.strip("/")
    if not safe_path:
        return send_from_directory(".", "index.html")
        
    if os.path.exists(os.path.join(".", safe_path)):
        return send_from_directory(".", safe_path)
        
    return send_from_directory(".", "index.html")


# ================================================================
#  ENTRYPOINT
# ================================================================

if __name__ == "__main__":
    debug_mode = (FLASK_ENV == "development")
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=debug_mode,
        use_reloader=False,
    )
