import streamlit as st
import io
import os

# 🔐 Replace in production
os.environ["OPENAI_API_KEY"] = ""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

from PyPDF2 import PdfReader
from docx import Document as DocxDocument

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Drive Agent", layout="wide")

# 🎨 LIGHT UI
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f8fafc, #e0f2fe);
}
h1 { text-align: center; color: #1e3a8a; }
section[data-testid="stSidebar"] { background: #f1f5f9; }

.stButton>button {
    background: #3b82f6;
    color: white;
    border-radius: 10px;
}

.stTextInput>div>div>input {
    background: white;
    border-radius: 10px;
}

.result-box {
    background: white;
    padding: 15px;
    border-radius: 12px;
    margin-top: 10px;
    border-left: 4px solid #3b82f6;
}
</style>
""", unsafe_allow_html=True)

st.title("📂 AI Drive Folder Q&A Agent")

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = "1SYm9Or5taIHW6aGx9vzfsNoTKrL67Fsf"

# ---------------- AUTH ----------------
def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('drive', 'v3', credentials=creds)

# ---------------- DOWNLOAD ----------------
def download_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return fh.getvalue()

# ---------------- EXTRACT ----------------
def extract_text(file_name, file_bytes):
    try:
        if file_name.endswith((".txt", ".md")):
            return file_bytes.decode("utf-8", errors="ignore")
        elif file_name.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_bytes))
            return " ".join([p.extract_text() or "" for p in reader.pages])
        elif file_name.endswith(".docx"):
            doc = DocxDocument(io.BytesIO(file_bytes))
            return " ".join([p.text for p in doc.paragraphs])
        return None
    except:
        return None

# ---------------- VECTOR DB ----------------
def create_vector_db(all_docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    texts, metadatas = [], []

    for doc in all_docs:
        chunks = splitter.split_text(doc["text"])
        texts.extend(chunks)
        metadatas.extend([{"source": doc["name"]}] * len(chunks))

    return FAISS.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)

# ---------------- CONNECT ----------------
if st.button("🔐 Connect Google Drive"):
    st.session_state.service = authenticate()
    st.success("Connected!")

# ---------------- LOAD ----------------
if "service" in st.session_state:
    service = st.session_state.service

    if st.button("📥 Load & Index Folder"):

        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])

        valid_files = [
            f for f in files if f["name"].endswith((".txt", ".pdf", ".docx", ".md"))
        ]

        all_docs = []

        for file in valid_files:
            file_bytes = download_file(service, file["id"])
            text = extract_text(file["name"], file_bytes)

            if text:
                all_docs.append({"name": file["name"], "text": text})

        st.session_state.db = create_vector_db(all_docs)
        st.success("Indexed!")

# ---------------- ASK ----------------
st.subheader("💬 Ask Question")
query = st.text_input("Enter your question")

if query and "db" in st.session_state:

    docs_with_scores = st.session_state.db.similarity_search_with_score(query, k=5)

    # ✅ STRICT FILTER (IMPORTANT FIX)
    threshold = 0.6   # lower = stricter
    filtered = [(doc, score) for doc, score in docs_with_scores if score < threshold]

    # 🚫 IF NO GOOD MATCH → STOP HERE
    if not filtered:
        st.markdown('<div class="result-box">❌ Not found in document</div>', unsafe_allow_html=True)

    else:
        context = "\n\n".join([doc.page_content for doc, _ in filtered])

        prompt = f"""
Answer ONLY from context.
If answer not present, say "Not found in document".

Context:
{context}

Question:
{query}
"""

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm.invoke(prompt)

        answer = response.content.strip().lower()

        # 🚫 SECOND CHECK
        if "not found" in answer:
            st.markdown('<div class="result-box">❌ Not found in document</div>', unsafe_allow_html=True)

        else:
            st.markdown(f'<div class="result-box">✅ {response.content}</div>', unsafe_allow_html=True)

            st.markdown("### 📄 Sources")
            sources = set([doc.metadata["source"] for doc, _ in filtered])
            for s in sources:
                st.markdown(f'<div class="result-box">📂 {s}</div>', unsafe_allow_html=True)