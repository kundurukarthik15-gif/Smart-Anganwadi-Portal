#!/usr/bin/env python3
"""
Smart Anganwadi Portal — Resources CSV Generator & Seeder
Generates a structured CSV file for educational stories, PDFs, and video links,
and optionally imports them directly into the Supabase database.
"""

import os
import csv
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# We try to import Supabase client in case they want to seed directly
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Default Fallbacks
DEFAULT_CENTER_ID = "11111111-1111-1111-1111-111111111111"  # Rajiv Nagar Center
DEFAULT_USER_ID = None  # Uploaded by can be NULL (safer for foreign keys)

def get_active_center_id():
    """Queries Supabase to get the first active center_id, or defaults to the seeded Rajiv Nagar Center."""
    if not SUPABASE_AVAILABLE:
        print("ℹ️ Supabase library not found. Using default center_id.")
        return DEFAULT_CENTER_ID

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("ℹ️ Supabase environment variables not set in .env. Using default center_id.")
        return DEFAULT_CENTER_ID

    try:
        supabase = create_client(supabase_url, supabase_key)
        # Fetch the first center from DB
        res = supabase.table("centers").select("id").limit(1).execute()
        if res.data and len(res.data) > 0:
            active_id = res.data[0]["id"]
            print(f"✅ Found active center in database: {active_id}")
            return active_id
        else:
            print(f"⚠️ No centers found in database. Using default center_id: {DEFAULT_CENTER_ID}")
            return DEFAULT_CENTER_ID
    except Exception as e:
        print(f"⚠️ Could not connect to Supabase: {e}. Using default center_id: {DEFAULT_CENTER_ID}")
        return DEFAULT_CENTER_ID

def generate_resources(center_id):
    """Compiles a list of high-quality early educational books (PDFs) and video resources."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Structure match exactly the Supabase "stories" table columns
    resources = [
        # ==========================================
        # 1. ENGLISH RESOURCES
        # ==========================================
        {
            "id": str(uuid.uuid4()),
            "title": "NCERT Preschool Activity Book (Volume 1)",
            "language": "English",
            "category": "Moral Stories",
            "emoji": "📚",
            "preview": "Official NCERT activity book designed for early childhood learning, featuring drawing, coloring, and tracing tasks.",
            "has_audio": False,
            "pdf_url": "https://ncert.nic.in/pdf/publication/preschool/preschool_activity_book.pdf",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "pdf",
            "is_global": True,
            "url_link": ""
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Nursery Rhymes & Kids Songs Compilation",
            "language": "English",
            "category": "Rhymes & Songs",
            "emoji": "🎵",
            "preview": "A collection of preschool-friendly classic rhymes including Johny Johny, Baa Baa Black Sheep, and Jack & Jill.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=F4tHL8reQDQ",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=F4tHL8reQDQ"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "UNICEF Early Childhood Education Curriculum Guide",
            "language": "English",
            "category": "Nature & Animals",
            "emoji": "🧩",
            "preview": "Educational guidelines and cognitive development activities designed by UNICEF experts for young children.",
            "has_audio": False,
            "pdf_url": "https://www.unicef.org/india/media/3401/file/Early-Childhood-Education-Curriculum.pdf",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "pdf",
            "is_global": True,
            "url_link": ""
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Interactive Shapes & Colors Learning Video",
            "language": "English",
            "category": "Rhymes & Songs",
            "emoji": "🎨",
            "preview": "A colorful animated educational video helping children identify basic geometric shapes and primary colors.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=w7w06M4Lz14",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=w7w06M4Lz14"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Wild & Domestic Animal Sounds for Toddlers",
            "language": "English",
            "category": "Nature & Animals",
            "emoji": "🦁",
            "preview": "Fun interactive nature lesson introducing preschool children to common animal names, visual pictures, and sound effects.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=t99ULJjCsaM",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=t99ULJjCsaM"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "The Thirsty Crow Moral Story Book",
            "language": "English",
            "category": "Moral Stories",
            "emoji": "🐦",
            "preview": "Animated storybook showing the thirsty crow who uses clever thinking to drink water from a pitcher. Teaches resourcefulness.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=2u7l64t5r5k",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=2u7l64t5r5k"
        },

        # ==========================================
        # 2. TELUGU RESOURCES
        # ==========================================
        {
            "id": str(uuid.uuid4()),
            "title": "చందమామ రావే (Chandamama Raave Rhymes)",
            "language": "Telugu",
            "category": "Rhymes & Songs",
            "emoji": "🌙",
            "preview": "Traditional Telugu nursery rhymes including Chandamama Raave, Bulbul Pitta, and other popular lullabies.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=sU1H6Cj4r5w",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=sU1H6Cj4r5w"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "బుద్ధిమంతుడైన కాకి (The Clever Thirsty Crow)",
            "language": "Telugu",
            "category": "Telugu Stories",
            "emoji": "🏺",
            "preview": "A beautifully animated Telugu story of the thirsty crow, teaching young children the values of perseverance and intellect.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=YfM_n3C6vX4",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=YfM_n3C6vX4"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "చిట్టి చిలకమ్మ తెలుగు పద్యాలు (Chitti Chilakamma)",
            "language": "Telugu",
            "category": "Rhymes & Songs",
            "emoji": "🦜",
            "preview": "Classic Telugu kindergarten nursery rhyme compilation of Chitti Chilakamma, Koti Bava, and other preschool hits.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=XzGv6mU_4jQ",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=XzGv6mU_4jQ"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "కుందేలు - తాబేలు కథ (The Rabbit & Tortoise)",
            "language": "Telugu",
            "category": "Telugu Stories",
            "emoji": "🐢",
            "preview": "Famous Panchatantra moral story of the slow-and-steady tortoise beating the speedy rabbit in a race, narrated in Telugu.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=hBwz6G0G1w0",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=hBwz6G0G1w0"
        },

        # ==========================================
        # 3. HINDI RESOURCES
        # ==========================================
        {
            "id": str(uuid.uuid4()),
            "title": "चंदा मामा दूर के (Chanda Mama Door Ke Rhymes)",
            "language": "Hindi",
            "category": "Rhymes & Songs",
            "emoji": "🌕",
            "preview": "Watch the classic animated Hindi nursery rhyme 'Chanda Mama Door Ke' with fun characters and kids singing along.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=53u7f6i6lJw",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=53u7f6i6lJw"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "चालाक खरगोश और मूर्ख शेर (The Lion & Rabbit)",
            "language": "Hindi",
            "category": "Moral Stories",
            "emoji": "🦁",
            "preview": "Popular Panchatantra tale of the clever rabbit who tricks the greedy forest lion. Hindi audio with moral message.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=Jm-Obe8p68g",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=Jm-Obe8p68g"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "एक बंदर ने खोली दुकान (Monkey's Shop Hindi Rhyme)",
            "language": "Hindi",
            "category": "Rhymes & Songs",
            "emoji": "🐒",
            "preview": "Cute and humorous Hindi moral poem about a monkey trying to run a grocery shop, tailored for toddler enjoyment.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=z2-yB1y_zL8",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=z2-yB1y_zL8"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "लालची कुत्ता (The Greedy Dog Hindi Story)",
            "language": "Hindi",
            "category": "Moral Stories",
            "emoji": "🐕",
            "preview": "Story of the dog who saw his own reflection in the water and dropped his bone out of greed. Hindi voiceover and animations.",
            "has_audio": False,
            "pdf_url": "",
            "audio_url": "",
            "video_url": "",
            "youtube_url": "https://www.youtube.com/watch?v=fVb2i2c0c7E",
            "center_id": center_id,
            "uploaded_by": DEFAULT_USER_ID,
            "uploaded_at": now_iso,
            "content_type": "url",
            "is_global": True,
            "url_link": "https://www.youtube.com/watch?v=fVb2i2c0c7E"
        }
    ]
    return resources

def write_to_csv(filename, resources):
    """Writes the resources list into a CSV format."""
    headers = [
        "id", "title", "language", "category", "emoji", "preview", "has_audio",
        "pdf_url", "audio_url", "video_url", "youtube_url", "center_id",
        "uploaded_by", "uploaded_at", "content_type", "is_global", "url_link"
    ]

    try:
        with open(filename, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for r in resources:
                writer.writerow(r)
        print(f"✨ Successfully generated CSV file: {filename} ({len(resources)} resources)")
        return True
    except Exception as e:
        print(f"❌ Error writing CSV file: {e}")
        return False

def seed_to_supabase(resources):
    """Directly uploads the generated resources into the Supabase database."""
    if not SUPABASE_AVAILABLE:
        print("❌ Cannot seed directly. The 'supabase' library is not available in Python.")
        return False

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Cannot seed. Supabase credentials are missing in the .env file.")
        return False

    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Connecting to Supabase and uploading resources...")
        
        # Prepare list (change uploaded_by to None for insert stability)
        insert_list = []
        for r in resources:
            r_copy = r.copy()
            # If uploaded_by is empty, remove key or set to None
            if not r_copy["uploaded_by"]:
                r_copy["uploaded_by"] = None
            insert_list.append(r_copy)

        res = supabase.table("stories").upsert(insert_list, on_conflict="id").execute()
        print(f"🚀 Success! Upserted {len(res.data)} learning resources directly into the Supabase database.")
        return True
    except Exception as e:
        print(f"❌ Error seeding to Supabase: {e}")
        return False

def main():
    import sys
    print("=== Smart Anganwadi Portal — Educational Resources Generator ===")
    
    # Check flags
    seed_now = False
    if "--seed" in sys.argv:
        seed_now = True
    
    # 1. Get correct center ID from Supabase
    center_id = get_active_center_id()
    
    # 2. Compile resources
    resources = generate_resources(center_id)
    
    # 3. Write CSV file
    csv_filename = "smart_anganwadi_resources.csv"
    write_to_csv(csv_filename, resources)
    
    # 4. Prompt / offer seeding directly
    print("\n--- Next Steps ---")
    print(f"1. You can now import the generated file '{csv_filename}' manually via your Supabase dashboard into the 'stories' table.")
    print("2. Alternatively, you can seed these items directly into the Supabase database right now!")
    
    if seed_now:
        seed_to_supabase(resources)
    else:
        print("\nℹ️ Run with 'python generate_resources_csv.py --seed' to automatically seed these records directly into your Supabase database.")

if __name__ == "__main__":
    main()
