# Smart Anganwadi Portal — Stories Upload Guide
## PDF, Video, and YouTube Links Setup

---

## 1. DATABASE SCHEMA (Updated Stories Table)

The stories table already has the necessary columns:

```sql
CREATE TABLE public.stories (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title character varying NOT NULL,
  language character varying NOT NULL,
  category character varying DEFAULT 'Moral Stories',
  emoji character varying DEFAULT '📖',
  preview text,
  has_audio boolean DEFAULT false,
  pdf_url text,              -- ✅ PDF file URL
  audio_url text,            -- ✅ Audio file URL
  video_url text,            -- ✅ Video file URL (NEW)
  youtube_url text,          -- ✅ YouTube embed URL (NEW)
  center_id uuid NOT NULL,
  uploaded_by uuid,
  uploaded_at timestamp with time zone DEFAULT now(),
  CONSTRAINT stories_pkey PRIMARY KEY (id),
  CONSTRAINT stories_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(id),
  CONSTRAINT stories_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id)
);
```

**To add the new columns to existing table:**

```sql
-- Add video_url column if not exists
ALTER TABLE public.stories 
ADD COLUMN IF NOT EXISTS video_url text;

-- Add youtube_url column if not exists
ALTER TABLE public.stories 
ADD COLUMN IF NOT EXISTS youtube_url text;
```

---

## 2. SUPABASE STORAGE SETUP

### Create Storage Buckets:

```sql
-- Run in Supabase SQL Editor to create buckets via REST API
-- Or use Supabase Dashboard → Storage → Create New Bucket

1. **story-pdfs** — For PDF files
2. **story-videos** — For video files
3. **story-audio** — For audio files
```

**Via Supabase Dashboard:**
1. Go to **Storage** (left sidebar)
2. Click **Create New Bucket**
3. Create these buckets:
   - `story-pdfs` (for PDFs)
   - `story-videos` (for videos/MP4)
   - `story-audio` (for audio/MP3)

**Make buckets PUBLIC:**
- Click each bucket → **Settings** → Toggle **Public** ON

---

## 3. BACKEND API (Python - app.py)

Add this endpoint to handle story uploads:

```python
# ================================================================
#  STORIES — UPLOAD
# ================================================================

@app.route("/api/stories/upload", methods=["POST"])
@auth_required
def upload_story():
    """Upload story with PDF, video, or YouTube link."""
    data = request.get_json() or {}
    
    # Required fields
    for f in ["title", "language", "category"]:
        if not data.get(f):
            return err(f"Field '{f}' is required", 400)
    
    # Check language is valid
    valid_languages = ['English', 'Telugu', 'Hindi']
    if data["language"] not in valid_languages:
        return err(f"Language must be one of {valid_languages}", 400)
    
    # Check category is valid
    valid_categories = ['Moral Stories', 'Rhymes & Songs', 'Nature & Animals', 'Telugu Stories']
    if data.get("category") not in valid_categories:
        return err(f"Category must be one of {valid_categories}", 400)
    
    # At least one media file must be provided
    pdf_url = data.get("pdf_url", "").strip()
    video_url = data.get("video_url", "").strip()
    youtube_url = data.get("youtube_url", "").strip()
    audio_url = data.get("audio_url", "").strip()
    
    if not (pdf_url or video_url or youtube_url or audio_url):
        return err("At least one of PDF, video, YouTube link, or audio must be provided", 400)
    
    # Create story record
    story = {
        "id": str(uuid.uuid4()),
        "title": data["title"].strip(),
        "language": data["language"],
        "category": data.get("category", "Moral Stories"),
        "emoji": data.get("emoji", "📖"),
        "preview": data.get("preview", "").strip(),
        "pdf_url": pdf_url,
        "video_url": video_url,
        "youtube_url": youtube_url,
        "audio_url": audio_url,
        "has_audio": bool(audio_url),
        "center_id": g.center_id,
        "uploaded_by": g.user_id,
        "uploaded_at": now_iso(),
    }
    
    res = supabase.table("stories").insert(story).execute()
    if not res.data:
        return err("Failed to create story", 500)
    
    return ok(res.data[0], "Story created successfully", 201)


@app.route("/api/stories/<story_id>", methods=["PUT"])
@auth_required
def update_story(story_id):
    """Update story with new media files."""
    data = request.get_json() or {}
    
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
    
    res = supabase.table("stories").update(update_data).eq("id", story_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("Story not found or unauthorized", 404)
    
    return ok(res.data[0], "Story updated successfully")


@app.route("/api/stories/<story_id>", methods=["DELETE"])
@auth_required
def delete_story(story_id):
    """Delete a story."""
    res = supabase.table("stories").delete().eq("id", story_id).eq("center_id", g.center_id).execute()
    if not res.data:
        return err("Story not found or unauthorized", 404)
    
    return ok(None, "Story deleted successfully")
```

---

## 4. FILE UPLOAD TO SUPABASE STORAGE

### Using Python/Flask Backend:

```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'mp4', 'webm', 'avi', 'mp3', 'wav'}

@app.route("/api/upload/file", methods=["POST"])
@auth_required
def upload_file():
    """Upload PDF, video, or audio file to Supabase Storage."""
    
    if 'file' not in request.files:
        return err("No file provided", 400)
    
    file = request.files['file']
    if file.filename == '':
        return err("No file selected", 400)
    
    # Check file extension
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return err(f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}", 400)
    
    # Determine bucket based on file type
    if ext == 'pdf':
        bucket_name = 'story-pdfs'
    elif ext in ['mp3', 'wav']:
        bucket_name = 'story-audio'
    else:  # mp4, webm, avi
        bucket_name = 'story-videos'
    
    # Create unique filename
    unique_filename = f"{g.center_id}/{int(time.time())}_{filename}"
    
    try:
        # Upload to Supabase Storage
        response = supabase.storage.from_(bucket_name).upload(
            unique_filename,
            file.read(),
            {'content-type': file.content_type}
        )
        
        # Get public URL
        file_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        
        return ok({"file_url": file_url, "filename": unique_filename}, "File uploaded successfully")
    
    except Exception as e:
        return err(f"File upload failed: {str(e)}", 500)
```

---

## 5. FRONTEND — Upload Story Form

Add this HTML form to index.html in the Stories section:

```html
<!-- UPLOAD STORY MODAL -->
<div id="upload-story-modal" class="modal" style="display:none">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5>Upload New Story</h5>
        <button type="button" class="btn-close" onclick="closeUploadModal()"></button>
      </div>
      <div class="modal-body">
        
        <div class="form-group mb-3">
          <label>Story Title *</label>
          <input type="text" class="form-control" id="upload-title" placeholder="Enter story title">
        </div>
        
        <div class="form-group mb-3">
          <label>Language *</label>
          <select class="form-control" id="upload-language">
            <option value="">-- Select Language --</option>
            <option value="English">English</option>
            <option value="Telugu">Telugu</option>
            <option value="Hindi">Hindi</option>
          </select>
        </div>
        
        <div class="form-group mb-3">
          <label>Category *</label>
          <select class="form-control" id="upload-category">
            <option value="">-- Select Category --</option>
            <option value="Moral Stories">Moral Stories</option>
            <option value="Rhymes & Songs">Rhymes & Songs</option>
            <option value="Nature & Animals">Nature & Animals</option>
            <option value="Telugu Stories">Telugu Stories</option>
          </select>
        </div>
        
        <div class="form-group mb-3">
          <label>Emoji</label>
          <input type="text" class="form-control" id="upload-emoji" placeholder="e.g., 📖, 🐦, 🌳" value="📖" maxlength="1">
        </div>
        
        <div class="form-group mb-3">
          <label>Preview/Description</label>
          <textarea class="form-control" id="upload-preview" rows="3" placeholder="Brief description of the story"></textarea>
        </div>
        
        <hr>
        <h6>Upload Media (at least one required)</h6>
        
        <!-- PDF Upload -->
        <div class="form-group mb-3">
          <label>PDF File</label>
          <input type="file" class="form-control" id="upload-pdf" accept=".pdf">
          <small class="text-muted">Max 10MB</small>
        </div>
        
        <!-- Video Upload -->
        <div class="form-group mb-3">
          <label>Video File (MP4, WebM, AVI)</label>
          <input type="file" class="form-control" id="upload-video" accept=".mp4,.webm,.avi">
          <small class="text-muted">Max 50MB</small>
        </div>
        
        <!-- Audio Upload -->
        <div class="form-group mb-3">
          <label>Audio File (MP3, WAV)</label>
          <input type="file" class="form-control" id="upload-audio" accept=".mp3,.wav">
          <small class="text-muted">Max 20MB</small>
        </div>
        
        <!-- YouTube Link -->
        <div class="form-group mb-3">
          <label>YouTube Link</label>
          <input type="url" class="form-control" id="upload-youtube" placeholder="https://www.youtube.com/watch?v=...">
          <small class="text-muted">Full YouTube URL</small>
        </div>
        
        <div id="upload-error" class="alert alert-danger" style="display:none"></div>
      </div>
      
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="closeUploadModal()">Cancel</button>
        <button type="button" class="btn btn-primary" onclick="uploadStory()">
          <i class="bi bi-cloud-upload"></i> Upload Story
        </button>
      </div>
    </div>
  </div>
</div>
```

---

## 6. FRONTEND — JavaScript Upload Logic

Add to script.js:

```javascript
function openUploadModal() {
  document.getElementById('upload-story-modal').style.display = 'block';
}

function closeUploadModal() {
  document.getElementById('upload-story-modal').style.display = 'none';
  document.getElementById('upload-error').style.display = 'none';
}

async function uploadStory() {
  const title = document.getElementById('upload-title').value.trim();
  const language = document.getElementById('upload-language').value;
  const category = document.getElementById('upload-category').value;
  const preview = document.getElementById('upload-preview').value.trim();
  const emoji = document.getElementById('upload-emoji').value.trim();
  
  const pdfFile = document.getElementById('upload-pdf').files[0];
  const videoFile = document.getElementById('upload-video').files[0];
  const audioFile = document.getElementById('upload-audio').files[0];
  const youtubeUrl = document.getElementById('upload-youtube').value.trim();
  
  const errEl = document.getElementById('upload-error');
  
  // Validation
  if (!title) { errEl.textContent = 'Title is required'; errEl.style.display = 'block'; return; }
  if (!language) { errEl.textContent = 'Language is required'; errEl.style.display = 'block'; return; }
  if (!category) { errEl.textContent = 'Category is required'; errEl.style.display = 'block'; return; }
  if (!pdfFile && !videoFile && !audioFile && !youtubeUrl) {
    errEl.textContent = 'At least one media file (PDF, Video, Audio) or YouTube link required';
    errEl.style.display = 'block';
    return;
  }
  
  errEl.style.display = 'none';
  
  // Upload files to storage
  let pdfUrl = '';
  let videoUrl = '';
  let audioUrl = '';
  
  try {
    if (pdfFile) {
      const pdfRes = await uploadFileToStorage(pdfFile, 'story-pdfs');
      pdfUrl = pdfRes.file_url;
    }
    if (videoFile) {
      const videoRes = await uploadFileToStorage(videoFile, 'story-videos');
      videoUrl = videoRes.file_url;
    }
    if (audioFile) {
      const audioRes = await uploadFileToStorage(audioFile, 'story-audio');
      audioUrl = audioRes.file_url;
    }
    
    // Create story in database
    const res = await apiFetch('/stories/upload', {
      method: 'POST',
      body: JSON.stringify({
        title: title,
        language: language,
        category: category,
        emoji: emoji,
        preview: preview,
        pdf_url: pdfUrl,
        video_url: videoUrl,
        audio_url: audioUrl,
        youtube_url: youtubeUrl
      })
    });
    
    if (res.success) {
      toast('✅ Story uploaded successfully!', 'success');
      closeUploadModal();
      document.getElementById('upload-story-modal').style.display = 'none';
      // Refresh stories list
      loadStories();
    } else {
      errEl.textContent = res.message || 'Upload failed';
      errEl.style.display = 'block';
    }
  } catch (error) {
    errEl.textContent = 'Error: ' + error.message;
    errEl.style.display = 'block';
  }
}

async function uploadFileToStorage(file, bucketName) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_URL}/upload/file`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: formData
  });
  
  const json = await response.json();
  if (!json.success) throw new Error(json.message);
  return json.data;
}

async function loadStories() {
  const res = await apiFetch('/stories');
  if (res.success) {
    DB.stories = res.data || [];
    renderStories();
  }
}

function renderStories() {
  const container = document.getElementById('stories-container');
  if (!container) return;
  
  container.innerHTML = DB.stories.map(story => `
    <div class="story-card">
      <div class="story-emoji">${story.emoji}</div>
      <h5>${story.title}</h5>
      <p class="story-lang">${story.language}</p>
      <p class="story-preview">${story.preview}</p>
      
      <div class="story-media">
        ${story.pdf_url ? `<a href="${story.pdf_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-file-pdf"></i> PDF</a>` : ''}
        ${story.video_url ? `<a href="${story.video_url}" target="_blank" class="btn btn-sm btn-outline-danger"><i class="bi bi-play-circle"></i> Video</a>` : ''}
        ${story.youtube_url ? `<a href="${story.youtube_url}" target="_blank" class="btn btn-sm btn-outline-danger"><i class="bi bi-youtube"></i> YouTube</a>` : ''}
        ${story.audio_url ? `<audio controls class="story-audio"><source src="${story.audio_url}"></audio>` : ''}
      </div>
    </div>
  `).join('');
}
```

---

## 7. HOW TO USE

### Option A: Upload Files Manually

1. **Go to Supabase Dashboard** → Storage
2. **Select bucket** (story-pdfs, story-videos, story-audio)
3. **Click Upload** and select your file
4. **Copy public URL** and paste in story upload form

### Option B: Use Upload API

1. Click **Upload Story** button in portal
2. Fill title, language, category
3. Upload PDF, video, or audio file
4. Add YouTube link (optional)
5. Click **Upload Story**

---

## 8. FILE STRUCTURE

```
Supabase Storage:
├── story-pdfs/
│   └── center-uuid/timestamp_filename.pdf
├── story-videos/
│   └── center-uuid/timestamp_filename.mp4
└── story-audio/
    └── center-uuid/timestamp_filename.mp3
```

---

## 9. EXAMPLE YOUTUBE URL FORMAT

```
Direct link: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Embed link: https://www.youtube.com/embed/dQw4w9WgXcQ
```

---

## 10. FILE SIZE LIMITS

| Type | Max Size |
|------|----------|
| PDF | 10 MB |
| Video | 50 MB |
| Audio | 20 MB |

Adjust limits in app.py as needed.

---

## Database Query to View Stories

```sql
SELECT 
  id, title, language, category, emoji,
  pdf_url, video_url, youtube_url, audio_url,
  uploaded_by, uploaded_at
FROM public.stories
WHERE center_id = 'your-center-uuid'
ORDER BY uploaded_at DESC;
```
