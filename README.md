# 🎨 Thumbnail Generator — Suba Arch

Sebuah aplikasi berbasis web interaktif yang dikembangkan menggunakan **Streamlit** untuk menghasilkan *custom thumbnail* premium bagi platform video pendek seperti YouTube Shorts, TikTok, dan Instagram Reels. Didesain secara spesifik untuk brand arsitektur kelas atas, aplikasi ini menyertakan integrasi AI (Gemini & Groq) untuk menciptakan teks *copywriting* yang provokatif, memikat, dan sangat relevan untuk *audience* kelas menengah ke atas.

---

## ✨ Fitur Utama

1. **Upload Visual Manual** 📸  
   Pengguna dapat mengunggah gambar mentah langsung dari perangkat. Sistem akan memotong (crop 9:16), menyesuaikan ukuran, dan menambahkan efek *blur/brightness* sesuai *style* premium *brand* Suba Arch.  

2. **Generate Otomatis dari Link Sosial Media** 🔗  
   Cukup masukkan link video dari TikTok atau Instagram Reels (mendukung hingga 10 link sekaligus), dan aplikasi akan:
   - Mengunduh video *(menggunakan yt-dlp)*.
   - Mengekstrak _frame_ terbaik dari video tersebut *(menggunakan OpenCV)*.
   - Pilihan untuk mengekstrak beberapa _frame_ (1, 3, atau 5) agar pengguna bisa memilih.

3. **AI Copywriting Super Cepat** 🤖  
   Ditenagai oleh **Google Gemini** sebagai generator utama dan **Groq** sebagai *fallback* cadangan. AI akan otomatis mendeteksi gambar/video dan merumuskan 2 baris teks (masing-masing maksimal 3 kata) yang bernada premium, profesional, dan memukau bagi audiens.

4. **Kustomisasi Teks & Branding Otomatis** ✏️  
   - Format font spesifik (Uppercase untuk baris atas, warna kontras; Title Case untuk teks bawah).
   - Penyesuaian ukuran font otomatis jika karakter teks terlalu panjang (dinamis).
   - Penempatan LOGO "Suba Arch" secata presisi di lokasi ideal (tengah bawah) memastikan *brand awareness* tetap menyala.

5. **Download Tunggal & Batch (ZIP)** 📦  
   Setelah *generate*, Anda bisa mendownload satu per satu hasil thumbnail atau mengunduh semuanya sekaligus dalam format ZIP.

---

## 🛠️ Persyaratan Sistem & Instalasi

Untuk menjalankan aplikasi ini secara lokal, pastikan Anda telah memiliki Python 3.9+ yang ter-instal.

1. **Clone repository ini**
   ```bash
   git clone https://github.com/USERNAME/thumbnail-suba.git
   cd thumbnail-suba
   ```

2. **Buat dan Aktifkan Virtual Environment (Rekomendasi)**
   ```bash
   python -m venv venv
   # Di Windows
   venv\Scripts\activate
   # Di macOS/Linux
   source venv/bin/activate
   ```

3. **Instal Dependensi**
   Aplikasi ini memerlukan modul-modul yang tercantum di `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```
   *Catatan:* Jika Anda menemui isu terkait ekstraksi video, pastikan Anda juga memiliki **FFmpeg** yang terinstal di sistem Anda.

---

## 🚀 Cara Menjalankan Aplikasi Lokal

Setelah semua pustaka Python terinstal, Anda dapat langsung menjalankan server **Streamlit**.

```bash
streamlit run app.py
```

Aplikasi akan segera terbuka di browser Anda (biasanya di `http://localhost:8501`).

---

## 🌐 Deploy ke Streamlit Community Cloud

Aplikasi ini sudah dipersiapkan sepenuhnya untuk dijalankan pada **Streamlit Community Cloud** (termasuk ketersediaan file `packages.txt` untuk memastikan `ffmpeg` terinstal otomatis di OS server Streamlit).

### Langkah-langkah Deploy:
1. **Push ke GitHub**:
   - Pastikan Anda sudah login ke GitHub lalu buat *Repository* baru.
   - Lakukan perintah berikut di terminal komputer Anda:
     ```bash
     git init
     git add .
     git commit -m "First commit: Thumbnail Generator App"
     git branch -M main
     git remote add origin https://github.com/USERNAME/NAMA-REPO-ANDA.git
     git push -u origin main
     ```
2. **Setup di Streamlit Cloud**:
   - Kunjungi [share.streamlit.io](https://share.streamlit.io) lalu login menggunakan akun GitHub Anda.
   - Klik tombol **"New app"**.
   - Pilih *repository* GitHub tempat Anda mem-*push* kode tadi.
   - Pastikan *Main file path* diisi dengan `app.py`.
   - Klik **"Deploy!"**
   - Streamlit Cloud akan mendeteksi `requirements.txt` untuk menginstal Python package dan `packages.txt` untuk menginstal FFmpeg secara otomatis.

---

## 🔑 Konfigurasi Environment (API Keys)

Aplikasi ini memerlukan API Key untuk fitur teks AI otomatis. API key ini dimasukkan langsung pada *UI Dashboard* di tab "Generate dari Link" ("Pengaturan API").
- **Gemini API Key**: Dapatkan gratis melalui [Google AI Studio](https://aistudio.google.com/).
- **Groq API Key**: Dapatkan sekadar untuk *fallback* gratis melalui [Groq Console](https://console.groq.com/).

---

## 📂 Struktur File Utama

```text
thumbnail-suba/
├── app.py                # Source code utama Streamlit
├── requirements.txt      # List modul Python
├── packages.txt          # List paket OS (seperti ffmpeg) yang dibutuhkan untuk deployment
├── .gitignore            # Filter folder/file yang tidak dipush ke repositori
├── README.md             # File dokumentasi proyek (halaman ini)
├── logo/                 # Direktori tempat diletakkannya logo (suba-arch by suba.png)
├── poppins/              # Direktori font (Poppins-Bold)
└── helvetica-bold/       # Direktori font (Helvetica Bold)
```

**Dibuat dengan ❤️ untuk Suba Arch**
