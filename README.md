



📂 AI Drive Folder Q&A Agent

AI-powered Streamlit application that connects to a Google Drive folder, reads documents, and answers user questions using semantic search and LLMs.

This project allows users to authenticate with Google Drive, load files from a specific folder, extract text from supported formats (.txt, .pdf, .docx, .md), and perform intelligent question-answering using LangChain, OpenAI embeddings, and FAISS vector database. The system ensures answers are strictly derived from document content and returns “Not found in document” if no relevant information exists.

🚀 Features

Google Drive OAuth authentication • Load and index Drive files • Multi-format support (TXT, PDF, DOCX, MD) • AI-based Q&A • Semantic search with FAISS • Source tracking • Strict answer validation

🛠️ Tech Stack

Streamlit (UI) • OpenAI + LangChain (LLM & embeddings) • FAISS (vector DB) • Google Drive API • PyPDF2 • python-docx

⚙️ Setup (Quick Start)
git clone https://github.com/your-username/ai-drive-agent.git
cd ai-drive-agent
pip install streamlit google-auth google-auth-oauthlib google-api-python-client langchain langchain-community openai faiss-cpu PyPDF2 python-docx

Add your API key in code:

os.environ["OPENAI_API_KEY"] = "your_api_key"

Place credentials.json (Google OAuth) in root folder and update:

FOLDER_ID = "your_folder_id"

Run the app:

streamlit run main.py
🧠 Workflow

Connect Drive → Load files → Extract text → Split into chunks → Create embeddings → Store in FAISS → Ask question → Retrieve relevant data → Generate answer

📌 Notes

• Answers are generated only from document context
• If no match found → ❌ Not found in document
• Uses similarity threshold for accuracy

🔮 Future Scope

File upload UI • Multi-folder support • Chat history • Improved retrieval (RAG optimization)

📜 License

MIT License
