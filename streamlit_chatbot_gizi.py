import streamlit as st
import google.generativeai as genai
import io
import base64
import uuid

# --- CSS Styling ---
st.markdown("""
    <style>
    /* Ubah warna background keseluruhan aplikasi */
    [data-testid="stAppViewContainer"] > .main {
        background-color: #212121;  /* Abu-abu gelap */
    }

    /* Ubah warna teks utama */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown p, .stMarkdown li, .stMarkdown ol, .stMarkdown ul {
        color: #e0e0e0; /* Abu-abu terang */
    }
    .stCaption {
        color: #9e9e9e; /* Abu-abu medium untuk caption */
    }
    .st-emotion-cache-1cypcdb { /* Untuk info box */
        background-color: #313131;
        border-color: #424242;
        color: #e0e0e0;
    }
    .st-emotion-cache-13ln4j {
        background-color: #313131;
    }
    
    .stChatMessage {
        border-radius: 16px;
        padding: 14px;
        margin: 6px 0;
        font-size: 15px;
    }
    
    /* Pesan User */
    .user-msg {
        background-color: #424242;  /* Abu-abu tua */
        color: #e0e0e0;           /* Abu-abu terang untuk teks */
    }
    
    /* Pesan Assistant */
    .assistant-msg {
        background-color: #313131;  /* Abu-abu sedang */
        color: #e0e0e0;           /* Abu-abu terang untuk teks */
    }

    /* Menghilangkan ikon share di judul aplikasi */
    h1 .st-emotion-cache-121d1d8 {
        display: none;
    }

    /* **PENTING**: Perubahan untuk membuat judul sidebar rata tengah */
    h2 {
        text-align: center;
    }

    /* Menyesuaikan ukuran dan padding tombol ikon agar terlihat baik */
    .stButton > button {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0.75rem 1rem;
        font-size: 1.5rem;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- Judul Halaman ---
st.title("🥗 NutriScan Chatbot")
st.caption("Upload foto makananmu, biar chatbot analisis gizinya!")

# --- Inisialisasi Client pakai Secrets ---
if "genai_client" not in st.session_state:
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        st.session_state.genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        st.error(f"API Key tidak valid: {e}")
        st.stop()

# --- Inisialisasi State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "last_file_name" not in st.session_state:
    st.session_state.last_file_name = None
if "session_key" not in st.session_state:
    st.session_state.session_key = str(uuid.uuid4())

# --- Sidebar ---
with st.sidebar:
    # Menggunakan ## akan menghasilkan tag <h2> di HTML
    st.markdown("## 📂 Riwayat Chat")
    st.markdown("---")

    if st.session_state.sessions:
        for sid, sess in st.session_state.sessions.items():
            preview = next((m["content"] for m in sess if m["role"] == "assistant" and "Terjadi error" not in m["content"]), "Chat Kosong")
            if st.button(f"📜 {sid}: {preview[:30]}...", key=f"sess_btn_{sid}"):
                st.session_state.messages = sess.copy()
                st.session_state.last_file_name = None
                st.rerun()
    else:
        st.markdown("<p style='text-align: center; color: #9e9e9e;'>Belum ada riwayat chat.</p>", unsafe_allow_html=True)
    
    st.markdown("---")

    if st.button("➕ Mulai Chat Baru", use_container_width=True):
        st.session_state.sessions = {}
        st.session_state.messages = []
        st.session_state.last_file_name = None
        st.session_state.session_key = str(uuid.uuid4()) # Menambahkan ini
        st.rerun()

# --- Fungsi untuk menampilkan chat bubble ---
def display_chat_messages():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='stChatMessage user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f"<div class='stChatMessage assistant-msg'>{msg['content']}</div>", unsafe_allow_html=True)

# --- Upload Foto ---
uploaded_file = st.file_uploader("Upload foto makanan", type=["jpg", "jpeg", "png"], key=st.session_state.session_key)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Foto makanan yang diunggah", use_container_width=True)

    if st.session_state.last_file_name != uploaded_file.name:
        st.session_state.last_file_name = uploaded_file.name
        
        display_chat_messages()
        st.session_state.last_file_data = uploaded_file.getvalue()

        try:
            with st.spinner("🤖 Chatbot sedang menganalisis gambar..."):
                response = st.session_state.genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{
                        "role": "user",
                        "parts": [
                            {"text": "Analisis makanan dalam foto ini. Sebutkan estimasi kandungan gizi (kalori, protein, karbo, lemak) dan beri tips pola makan sehat."},
                            {"inline_data": {"mime_type": uploaded_file.type, "data": st.session_state.last_file_data}}
                        ]
                    }]
                )
                answer = response.text
        except Exception as e:
            answer = f"⚠️ Terjadi error saat analisis gambar: {e}"

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
else:
    st.info("Silakan unggah foto makanan untuk memulai analisis.")

# --- Tampilkan Riwayat Chat ---

display_chat_messages()
