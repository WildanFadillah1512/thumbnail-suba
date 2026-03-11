import streamlit as st
import os
import sys
import tempfile
import re
import zipfile
import shutil
import time
import random
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance

st.set_page_config(page_title="Thumbnail Generator", layout="wide")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

def get_random_ua():
    return random.choice(USER_AGENTS)

# ============================================================
# DEPENDENCY CHECK
# ============================================================

def check_dependencies():
    missing = []
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python-headless")
    try:
        from google import genai
    except ImportError:
        missing.append("google-genai")
    try:
        from groq import Groq
    except ImportError:
        missing.append("groq")
    return missing

missing_deps = check_dependencies()
if missing_deps:
    st.error("❌ **Dependency belum ter-install untuk Python yang dipakai Streamlit ini.**")
    st.code(f"{sys.executable} -m pip install {' '.join(missing_deps)}", language="bash")
    st.info("Jalankan perintah di atas di terminal, lalu restart Streamlit.")
    st.stop()


# ============================================================
# TEXT FORMATTING HELPERS
# ============================================================

def format_text_top(text: str) -> str:
    """Teks atas: Huruf awal kapital (Title Case)."""
    return text.title()

def format_text_bottom(text: str) -> str:
    """Teks bawah: Title Case."""
    return text.title()


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def center_crop_and_resize(img, target_width, target_height):
    width, height = img.size
    aspect_ratio_img = width / height
    aspect_ratio_target = target_width / target_height

    if aspect_ratio_img > aspect_ratio_target:
        new_width = int(aspect_ratio_target * height)
        offset = (width - new_width) / 2
        img = img.crop((offset, 0, width - offset, height))
    else:
        new_height = int(width / aspect_ratio_target)
        offset = (height - new_height) / 2
        img = img.crop((0, offset, width, height - offset))

    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def get_font_for_target_width(draw, text, font_path, target_width, max_size=200, min_size=20):
    """
    Cari ukuran font agar lebar teks sedekat mungkin (<=) dengan target_width.
    Ini membuat efek teks blok justified (rata tanpa lekukan).
    """
    size = max_size
    while size >= min_size:
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            font = ImageFont.load_default(size=size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= target_width:
            return font, size, text_width
        size -= 1

    # Fallback
    try:
        font = ImageFont.truetype(font_path, min_size)
    except:
        font = ImageFont.load_default(size=min_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    return font, min_size, bbox[2] - bbox[0]


def generate_thumbnail(image_input, text_top, text_bottom):
    """Generate thumbnail from image file or PIL Image."""
    # Format teks
    text_top = format_text_top(text_top)
    text_bottom = format_text_bottom(text_bottom)

    if isinstance(image_input, Image.Image):
        img = image_input.convert("RGBA")
    else:
        img = Image.open(image_input).convert("RGBA")

    # 1. Resize and Crop to 1080 x 1920 (9:16)
    img = center_crop_and_resize(img, 1080, 1920)
    img = img.convert("RGB")

    # 2. Blurred dark background
    bg_img = img.copy()
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=15))
    enhancer = ImageEnhance.Brightness(bg_img)
    bg_img = enhancer.enhance(0.3)

    final_img = bg_img.convert("RGBA")

    # 3. Add Logo
    logo_path = "logo/suba-arch by suba.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_width = 300
        aspect_ratio = logo.size[1] / logo.size[0]
        logo_height = int(logo_width * aspect_ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        logo_x = (1080 - logo_width) // 2
        logo_y = 1920 - logo_height - 100
        final_img.alpha_composite(logo, (logo_x, logo_y))

    # 4. Text Overlay
    draw = ImageDraw.Draw(final_img)

    font_top_path = "poppins/Poppins-Bold.ttf"
    font_bottom_path = "poppins/Poppins-Bold.ttf"

    FONT_TOP_DEFAULT = 77
    FONT_BOTTOM_DEFAULT = 64

    start_y = 900
    words = text_top.split()

    if words:
        first_word = words[0]
        rest_text = " " + " ".join(words[1:]) if len(words) > 1 else ""
        full_top_text = text_top

        # Hitung lebar natural masing-masing teks pada ukuran default
        try:
            default_font_top = ImageFont.truetype(font_top_path, FONT_TOP_DEFAULT)
        except:
            default_font_top = ImageFont.load_default(size=FONT_TOP_DEFAULT)
        try:
            default_font_bottom = ImageFont.truetype(font_bottom_path, FONT_BOTTOM_DEFAULT)
        except:
            default_font_bottom = ImageFont.load_default(size=FONT_BOTTOM_DEFAULT)
            
        bbox_top = draw.textbbox((0, 0), full_top_text, font=default_font_top)
        w_top = bbox_top[2] - bbox_top[0]
        
        bbox_bottom = draw.textbbox((0, 0), text_bottom, font=default_font_bottom)
        w_bottom = bbox_bottom[2] - bbox_bottom[0]
        
        # Target width mengikuti lebar natural yang paling panjang (agar font tetap proporsional),
        # kecilkan lagi dari 770px ke 700px
        TARGET_WIDTH = max(w_top, w_bottom)
        
        # Beri batas minimum agar ukurannya tidak terlalu kecil, tapi tidak melebihi lebar frame (1080)
        # 700px memberikan padding yang sangat lapang
        if TARGET_WIDTH > 700:
            TARGET_WIDTH = 700
        elif TARGET_WIDTH < 600:  # Batas bawah diturunkan juga agar lebih pas
            TARGET_WIDTH = 600

        # --- Font teks atas (rata penuh target_width) ---
        font_top, size_top, _ = get_font_for_target_width(
            draw, full_top_text, font_top_path, target_width=TARGET_WIDTH, max_size=160
        )

        # Hitung posisi teks atas (2 warna)
        first_word_bbox = draw.textbbox((0, 0), first_word, font=font_top)
        first_word_width = first_word_bbox[2] - first_word_bbox[0]

        rest_width = 0
        if rest_text.strip():
            rest_bbox = draw.textbbox((0, 0), rest_text, font=font_top)
            rest_width = rest_bbox[2] - rest_bbox[0]

        total_top_width = first_word_width + rest_width
        start_x = (1080 - total_top_width) // 2

        draw.text((start_x, start_y), first_word, font=font_top, fill="#FFD700")
        if rest_text:
            draw.text((start_x + first_word_width, start_y), rest_text, font=font_top, fill="white")

        # --- Font teks bawah (rata penuh target_width) ---
        font_bottom, size_bottom, bottom_width = get_font_for_target_width(
            draw, text_bottom, font_bottom_path, target_width=TARGET_WIDTH, max_size=180
        )

        bottom_x = (1080 - bottom_width) // 2

        # Jarak antar baris: padatkan sedikit jaraknya
        top_bbox = draw.textbbox((0, 0), full_top_text, font=font_top)
        top_height = top_bbox[3] - top_bbox[1]
        
        # Tambahkan jarak (padding) antara teks atas dan bawah
        bottom_y = start_y + top_height + 40

        draw.text((bottom_x, bottom_y), text_bottom, font=font_bottom, fill="white")

    return final_img.convert("RGB")


# ============================================================
# URL VALIDATION
# ============================================================

def validate_social_url(url):
    if not url:
        return False, ""

    tiktok_patterns = [r'(tiktok\.com)', r'(vm\.tiktok\.com)', r'(vt\.tiktok\.com)']
    ig_patterns = [r'(instagram\.com/reel)', r'(instagram\.com/p/)', r'(instagram\.com/tv/)']

    for p in tiktok_patterns:
        if re.search(p, url, re.IGNORECASE):
            return True, "tiktok"
    for p in ig_patterns:
        if re.search(p, url, re.IGNORECASE):
            return True, "instagram"

    return False, ""


# ============================================================
# VIDEO DOWNLOAD & FRAME EXTRACTION
# ============================================================

def _download_instagram_image_fallback(url, temp_dir):
    import requests
    import os
    base_url = url.split('?')[0]
    img_url = base_url if base_url.endswith('/') else base_url + '/'
    img_url += 'media/?size=l'
    headers = {
        'User-Agent': get_random_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        res = requests.get(img_url, headers=headers, timeout=15)
        if res.status_code == 200:
            if 'image' in res.headers.get('content-type', '').lower():
                img_path = os.path.join(temp_dir, "image.jpg")
                with open(img_path, 'wb') as f:
                    f.write(res.content)
                return img_path
            else:
                return f"ERROR: Dapat respons HTTP 200 tapi bukan format gambar. (Content-Type: {res.headers.get('content-type')})"
        else:
            return f"ERROR: Instagram menolak akses foto. (HTTP Status: {res.status_code})"
    except Exception as e:
        return f"ERROR: Gagal saat mencoba download fallback: {str(e)}"
    return None

def download_video(url, st_status=None):
    import yt_dlp
    import requests

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "video.%(ext)s")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'socket_timeout': 30,
        'retries': 3,
        'http_headers': {
            'User-Agent': get_random_ua(),
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', '') or ''
            description = info.get('description', '') or ''

        downloaded_file = None
        for f in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, f)
            if os.path.isfile(filepath):
                downloaded_file = filepath
                break

        if not downloaded_file:
            if "instagram" in url.lower():
                if st_status: st_status.update(label="⚠️ Menggunakan fallback metode 2 (Photo Link)...")
                fallback_res = _download_instagram_image_fallback(url, temp_dir)
                if fallback_res and not fallback_res.startswith("ERROR"):
                    return fallback_res, title or "Instagram Photo", description
                elif st_status and fallback_res:
                    st.warning(f"Fallback Debug: {fallback_res}")
            raise FileNotFoundError(f"Video/Foto tidak ditemukan di {temp_dir} setelah download")

        return downloaded_file, title, description

    except yt_dlp.utils.DownloadError as e:
        # Fallback for Instagram image posts or rate-limit blocks
        if "instagram" in url.lower():
            if st_status: st_status.update(label="⚠️ Error yt-dlp. Mencoba fallback ke foto...")
            fallback_res = _download_instagram_image_fallback(url, temp_dir)
            if fallback_res and not fallback_res.startswith("ERROR"):
                return fallback_res, "Instagram Photo", ""
            elif st_status and fallback_res:
                st.warning(f"Fallback Debug: {fallback_res}")
        raise e


def extract_best_frame(video_path):
    import cv2
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return None
    target_frame = int(total_frames * 0.3)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return None


def extract_multiple_frames(video_path, num_frames=3):
    import cv2
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return []

    positions = [0.2, 0.4, 0.6]
    if num_frames == 5:
        positions = [0.1, 0.25, 0.4, 0.6, 0.8]

    frames = []
    for pos in positions[:num_frames]:
        target_frame = int(total_frames * pos)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        if ret:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    cap.release()
    return frames


# ============================================================
# TEXT GENERATION (Gemini + Groq fallback)
# ============================================================

AUDIENCE_CONTEXT = """
Target audience: middle-upper class Indonesia yang memahami pentingnya jasa arsitek profesional, 
memiliki buying power untuk membangun rumah dengan budget 1,5 miliar ke atas. 
Mereka menghargai kualitas, estetika, dan profesionalisme. 
Pastikan teks thumbnail terasa premium, aspiratif, dan relevan untuk segmen ini.
"""

def pil_image_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def generate_text_gemini(image, title, description, api_key):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""Kamu adalah copywriter thumbnail YouTube/TikTok/Instagram untuk brand arsitektur premium bernama Suba Arch.

{AUDIENCE_CONTEXT}

Berdasarkan gambar ini dan informasi video berikut:
Judul: {title}
Deskripsi: {description[:500] if description else 'Tidak ada deskripsi'}

Buatkan 2 baris teks untuk thumbnail yang MENARIK PERHATIAN:
- BARIS1: Teks utama highlight (TEPAT 2 kata, provokatif/clickbait, sesuai audience premium)
- BARIS2: Sub-teks penjelasan (TEPAT 2 kata, sesuai audience premium)

ATURAN:
- Total PAS 4 kata (2 kata atas, 2 kata bawah)
- Bahasa Indonesia
- Singkat, padat, provokatif
- Jangan gunakan emoji
- Tone: premium, aspiratif, profesional — cocok untuk orang yang mempertimbangkan membangun rumah mewah

Format output HANYA seperti ini (tanpa tambahan apapun):
BARIS1: [teks]
BARIS2: [teks]"""

    image_bytes = pil_image_to_bytes(image)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=prompt),
        ],
    )

    text = response.text.strip()
    lines = text.strip().split('\n')
    text_top = "TEKS ATAS"
    text_bottom = "TEKS BAWAH"

    for line in lines:
        line = line.strip()
        if line.upper().startswith('BARIS1:'):
            text_top = line.split(':', 1)[1].strip()
        elif line.upper().startswith('BARIS2:'):
            text_bottom = line.split(':', 1)[1].strip()

    return text_top, text_bottom


def generate_text_groq(title, description, groq_api_key):
    from groq import Groq

    client = Groq(api_key=groq_api_key)

    prompt = f"""Kamu adalah copywriter thumbnail YouTube/TikTok/Instagram untuk brand arsitektur premium bernama Suba Arch.

{AUDIENCE_CONTEXT}

Berdasarkan informasi video berikut:
Judul: {title}
Deskripsi: {description[:500] if description else 'Tidak ada deskripsi'}

Buatkan 2 baris teks untuk thumbnail yang MENARIK PERHATIAN:
- BARIS1: Teks utama highlight (TEPAT 2 kata, provokatif/clickbait, sesuai audience premium)
- BARIS2: Sub-teks penjelasan (TEPAT 2 kata, sesuai audience premium)

ATURAN:
- Total PAS 4 kata (2 kata atas, 2 kata bawah)
- Bahasa Indonesia
- Singkat, padat, provokatif
- Jangan gunakan emoji
- Tone: premium, aspiratif, profesional — cocok untuk orang yang mempertimbangkan membangun rumah mewah

Format output HANYA seperti ini (tanpa tambahan apapun):
BARIS1: [teks]
BARIS2: [teks]"""

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=100,
    )

    text = chat_completion.choices[0].message.content.strip()
    lines = text.strip().split('\n')
    text_top = "TEKS ATAS"
    text_bottom = "TEKS BAWAH"

    for line in lines:
        line = line.strip()
        if line.upper().startswith('BARIS1:'):
            text_top = line.split(':', 1)[1].strip()
        elif line.upper().startswith('BARIS2:'):
            text_bottom = line.split(':', 1)[1].strip()

    return text_top, text_bottom


def generate_text_with_fallback(image, title, description, gemini_key, groq_key):
    if gemini_key:
        try:
            return generate_text_gemini(image, title, description, gemini_key)
        except Exception as e:
            st.warning(f"⚠️ Gemini gagal: {str(e)[:150]}. Mencoba Groq...")

    if groq_key:
        try:
            return generate_text_groq(title, description, groq_key)
        except Exception as e:
            st.error(f"❌ Groq juga gagal: {str(e)[:150]}")

    return "TEKS ATAS", "TEKS BAWAH"


# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🎨 Thumbnail Generator — Suba Arch")

tab1, tab2 = st.tabs(["📸 Upload Foto", "🔗 Generate dari Link"])

# ──────────────────────────────────────────────────────────────
# TAB 1: Upload Foto
# ──────────────────────────────────────────────────────────────
with tab1:
    st.markdown("Upload foto mentah, sistem akan membuat thumbnail otomatis sesuai template.")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Upload Foto Mentah", type=["jpg", "png", "jpeg"])

        text_top_raw = st.text_input("Teks Atas", value="Value Niat", key="tab1_text_top")
        st.caption("Kata pertama otomatis kuning · Teks atas → Huruf Awal Kapital · Teks bawah → Title Case · Layar teks rata kiri-kanan otomatis")
        text_bottom_raw = st.text_input("Teks Bawah", value="Lebih Kuat", key="tab1_text_bottom")

        st.caption(f"Preview: **{format_text_top(text_top_raw)}** ({len(text_top_raw)} karakter) / {format_text_bottom(text_bottom_raw)} ({len(text_bottom_raw)} karakter)")

    with col2:
        if uploaded_file is not None:
            st.subheader("Preview Hasil:")
            with st.spinner("Generating thumbnail..."):
                try:
                    result_img = generate_thumbnail(uploaded_file, text_top_raw, text_bottom_raw)
                    st.image(result_img, caption="Thumbnail Generated", use_container_width=True)
                    buf = io.BytesIO()
                    result_img.save(buf, format="PNG")
                    st.download_button(
                        label="Download Thumbnail",
                        data=buf.getvalue(),
                        file_name="thumbnail_generated.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("Silakan upload foto mentah terlebih dahulu.")


# ──────────────────────────────────────────────────────────────
# TAB 2: Generate dari Link
# ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    **Masukkan link TikTok / Instagram** (maks 10 link).  
    Sistem akan otomatis download video → ambil frame terbaik → generate teks thumbnail.
    """)

    with st.expander("🛠️ Debug Info", expanded=False):
        st.code(f"Python: {sys.executable}", language="text")

    with st.expander("⚙️ Pengaturan API", expanded=False):
        col_api1, col_api2 = st.columns(2)
        with col_api1:
            gemini_api_key = st.text_input(
                "Gemini API Key (Utama)",
                type="password",
                value="",
                help="API Key dari Google AI Studio",
                key="gemini_api_key"
            )
        with col_api2:
            groq_api_key = st.text_input(
                "Groq API Key (Fallback)",
                type="password",
                value="",
                help="API Key dari Groq sebagai fallback",
                key="groq_api_key"
            )
        st.caption("💡 Gemini digunakan utama (mendukung gambar). Groq otomatis dipakai jika Gemini gagal.")
        frame_count = st.select_slider("Jumlah Frame yang Diekstrak", options=[1, 3, 5], value=3, key="frame_count")

    st.divider()

    num_links = st.number_input("Jumlah Link", min_value=1, max_value=10, value=1, step=1, key="num_links")
    all_auto = st.checkbox("🤖 Generate Semua Teks Otomatis (AI)", value=True, key="all_auto")

    st.divider()

    if "link_results" not in st.session_state:
        st.session_state.link_results = {}

    link_data = []
    for i in range(int(num_links)):
        st.markdown(f"### Link #{i+1}")

        col_link, col_mode = st.columns([3, 1])

        with col_link:
            url = st.text_input(
                "URL TikTok/Instagram",
                placeholder="https://vt.tiktok.com/... atau https://www.instagram.com/reel/...",
                key=f"link_url_{i}"
            )
            if url:
                is_valid, platform = validate_social_url(url)
                if is_valid:
                    st.caption(f"{'🎵' if platform == 'tiktok' else '📷'} {platform.title()} link terdeteksi")
                else:
                    st.warning("⚠️ URL tidak terdeteksi sebagai TikTok/Instagram. Tetap akan dicoba.")

        with col_mode:
            if all_auto:
                mode = "Auto (AI)"
                st.info("🤖 Auto")
            else:
                mode = st.radio("Mode Teks", ["Auto (AI)", "Manual"], key=f"link_mode_{i}", horizontal=True)

        manual_top = ""
        manual_bottom = ""
        if mode == "Manual":
            col_t, col_b = st.columns(2)
            with col_t:
                manual_top = st.text_input("Teks Atas (tepat 2 kata)", key=f"manual_top_{i}", max_chars=50)
            with col_b:
                manual_bottom = st.text_input("Teks Bawah (tepat 2 kata)", key=f"manual_bottom_{i}", max_chars=50)
            if manual_top or manual_bottom:
                st.caption(f"Preview: **{format_text_top(manual_top)}** ({len(manual_top)} kar) / {format_text_bottom(manual_bottom)} ({len(manual_bottom)} kar)")

        link_data.append({
            "index": i,
            "url": url.strip() if url else "",
            "mode": mode,
            "manual_top": manual_top,
            "manual_bottom": manual_bottom,
        })

        if i in st.session_state.link_results:
            result = st.session_state.link_results[i]

            st.markdown("---")
            st.markdown("**📝 Hasil Generate:**")

            col_edit_top, col_edit_bottom = st.columns(2)
            with col_edit_top:
                edited_top = st.text_input(
                    "✏️ Edit Teks Atas",
                    value=result.get('text_top', 'TEKS ATAS'),
                    key=f"edit_top_{i}",
                    max_chars=50
                )
            with col_edit_bottom:
                edited_bottom = st.text_input(
                    "✏️ Edit Teks Bawah",
                    value=result.get('text_bottom', 'TEKS BAWAH'),
                    key=f"edit_bottom_{i}",
                    max_chars=50
                )

            edited_top_fmt = format_text_top(edited_top)
            edited_bottom_fmt = format_text_bottom(edited_bottom)

            text_changed = (
                edited_top_fmt != result.get('text_top', '') or
                edited_bottom_fmt != result.get('text_bottom', '')
            )
            if text_changed:
                result['text_top'] = edited_top_fmt
                result['text_bottom'] = edited_bottom_fmt
                result['thumbnail'] = generate_thumbnail(result['frame'], edited_top_fmt, edited_bottom_fmt)

            frames = result.get("all_frames", [])
            if len(frames) > 1:
                st.markdown("**🖼️ Pilih Frame:**")
                frame_cols = st.columns(len(frames))
                for fi, frame_img in enumerate(frames):
                    with frame_cols[fi]:
                        st.image(frame_img, caption=f"Frame {fi+1}", use_container_width=True)
                        if st.button(f"Pilih Frame {fi+1}", key=f"select_frame_{i}_{fi}"):
                            st.session_state.link_results[i]['frame'] = frame_img
                            st.session_state.link_results[i]['thumbnail'] = generate_thumbnail(
                                frame_img, edited_top_fmt, edited_bottom_fmt
                            )
                            st.rerun()

            col_prev, col_thumb = st.columns(2)
            with col_prev:
                st.image(result["frame"], caption="Frame Terpilih", use_container_width=True)
                st.caption(f"🎯 **{result['text_top']}** / {result['text_bottom']}")
            with col_thumb:
                st.image(result["thumbnail"], caption="Thumbnail Generated", use_container_width=True)
                buf = io.BytesIO()
                result["thumbnail"].save(buf, format="PNG")
                st.download_button(
                    label=f"📥 Download #{i+1}",
                    data=buf.getvalue(),
                    file_name=f"thumbnail_{i+1}.png",
                    mime="image/png",
                    key=f"download_{i}"
                )

            if st.button(f"🔄 Regenerate Teks #{i+1}", key=f"regen_text_{i}"):
                with st.spinner("Generating new text..."):
                    try:
                        new_top, new_bottom = generate_text_with_fallback(
                            result['frame'],
                            result.get('title', ''),
                            result.get('description', ''),
                            gemini_api_key,
                            groq_api_key
                        )
                        new_top = format_text_top(new_top)
                        new_bottom = format_text_bottom(new_bottom)
                        st.session_state.link_results[i]['text_top'] = new_top
                        st.session_state.link_results[i]['text_bottom'] = new_bottom
                        st.session_state.link_results[i]['thumbnail'] = generate_thumbnail(
                            result['frame'], new_top, new_bottom
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal regenerate teks: {str(e)}")

        st.divider()

    col_gen, _ = st.columns([2, 1])
    with col_gen:
        generate_btn = st.button(
            "🚀 Generate Semua Thumbnails",
            type="primary",
            use_container_width=True,
            key="generate_all_btn"
        )

    if generate_btn:
        valid_links = [d for d in link_data if d["url"]]

        if not valid_links:
            st.error("❌ Masukkan minimal 1 link!")
        else:
            auto_links = [d for d in valid_links if d["mode"] == "Auto (AI)"]
            if auto_links and not gemini_api_key and not groq_api_key:
                st.error("❌ Minimal satu API Key diperlukan untuk mode Auto!")
            else:
                st.session_state.link_results = {}
                temp_dirs = []

                for idx, data in enumerate(valid_links):
                    link_num = data["index"]
                    url = data["url"]

                    with st.status(f"🔄 Memproses Link #{link_num+1}...", expanded=True) as status:
                        try:
                            if idx > 0:
                                delay = random.randint(3, 7)
                                st.write(f"⏳ Jeda {delay} detik untuk menghindari blokir anti-robot Instagram...")
                                time.sleep(delay)

                            st.write(f"⬇️ Downloading konten dari: `{url[:60]}...`")
                            video_path, title, description = download_video(url, st_status=status)
                            temp_dirs.append(os.path.dirname(video_path))
                            st.write(f"✅ Video/Foto berhasil didownload! Judul: **{title[:50]}**")

                            st.write("🖼️ Menyiapkan frame...")
                            if video_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                                all_frames = [Image.open(video_path).convert("RGB")]
                            else:
                                if frame_count > 1:
                                    all_frames = extract_multiple_frames(video_path, num_frames=frame_count)
                                else:
                                    single_frame = extract_best_frame(video_path)
                                    all_frames = [single_frame] if single_frame else []


                            if not all_frames:
                                status.update(label=f"❌ Link #{link_num+1}: Gagal extract frame", state="error")
                                st.error("Gagal extract frame dari video")
                                continue

                            st.write(f"✅ Berhasil mengambil {len(all_frames)} frame")
                            frame = all_frames[len(all_frames) // 2]

                            if data["mode"] == "Auto (AI)":
                                st.write("🤖 Generating teks otomatis via AI...")
                                text_top, text_bottom = generate_text_with_fallback(
                                    frame, title, description, gemini_api_key, groq_api_key
                                )
                            else:
                                text_top = data["manual_top"] or "TEKS ATAS"
                                text_bottom = data["manual_bottom"] or "TEKS BAWAH"

                            text_top = format_text_top(text_top)
                            text_bottom = format_text_bottom(text_bottom)

                            st.write(f"✅ Teks: **{text_top}** / {text_bottom}")

                            st.write("🎨 Generating thumbnail...")
                            thumbnail = generate_thumbnail(frame, text_top, text_bottom)

                            st.session_state.link_results[link_num] = {
                                "frame": frame,
                                "all_frames": all_frames,
                                "thumbnail": thumbnail,
                                "text_top": text_top,
                                "text_bottom": text_bottom,
                                "title": title,
                                "description": description,
                            }

                            status.update(label=f"✅ Link #{link_num+1} berhasil!", state="complete")

                        except Exception as e:
                            status.update(label=f"❌ Link #{link_num+1}: Error", state="error")
                            st.error(f"Error: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc(), language="text")

                for td in temp_dirs:
                    try:
                        shutil.rmtree(td, ignore_errors=True)
                    except:
                        pass

                results = st.session_state.link_results
                if results:
                    st.success(f"🎉 Selesai! {len(results)} thumbnail berhasil di-generate.")

                    if len(results) > 1:
                        zip_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                            for idx, result in results.items():
                                img_buf = io.BytesIO()
                                result["thumbnail"].save(img_buf, format="PNG")
                                zf.writestr(f"thumbnail_{idx+1}.png", img_buf.getvalue())

                        st.download_button(
                            label="📦 Download Semua Thumbnails (ZIP)",
                            data=zip_buf.getvalue(),
                            file_name="thumbnails_all.zip",
                            mime="application/zip",
                            key="download_all_zip"
                        )

                st.rerun()