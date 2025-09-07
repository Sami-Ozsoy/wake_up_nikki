# 🤖 Niki - FMB130 Command Assistant

A Retrieval-Augmented Generation (RAG) powered assistant that helps you work with Teltonika FMB130 device commands and parameters.

## 📋 Features

- **RAG-based answers**: Extracts reliable information from your local FMB docs (PDF/TXT)
- **Agentic routing (LangGraph)**: Classifies intent and routes to FMB specialist or a general assistant
- **Modern web UI (Flask)**: ChatGPT-like interface with Markdown rendering and copy buttons
- **Streamlit alternative UI**: Simple, fast to run, sidebar with sample prompts
- **Session memory**: Per-session conversation history
- **FAISS vector index**: Fast similarity search over documents

## 🏗️ Project Structure

```
wake_up_nikki/
├── flask_app.py               # Flask web app (recommended UI)
├── main.py                    # Streamlit app (alternative UI)
├── config.py                  # Environment configuration
├── agents/
│   └── graph.py              # LangGraph-based routing + tools
├── utils/
│   ├── helpers.py            # LLM factory (OpenAI by default)
│   ├── loaders.py            # Prompt loader
│   └── formatter.py          # Output formatting helpers
├── vector/
│   ├── vector_store.py       # FAISS-backed vector store
│   └── index/                # Saved FAISS index (faiss + pkl)
├── templates/
│   └── chat.html             # Flask chat UI
├── assets/                   # Static assets
│   └── niki.png              # Logo
├── prompts/
│   └── main_prompt.txt       # System prompt template
├── data/                     # Your source docs (PDF/TXT)
├── rebuild_index.py          # Script to (re)build vector index
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Getting Started

### 1) Prerequisites

- Python 3.9+ (Dockerfile uses 3.9-slim)
- An OpenAI API key
- FMB130 reference documents (PDF/TXT) to place under `data/`

### 2) Installation

```bash
# Clone the repo
git clone <repository-url>
cd wake_up_nikki

# Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create a .env file)
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 3) Prepare Data and Build the Index

Put your FMB130 docs into the `data/` folder, for example:

- `N430 Komut Listesi.pdf`
- `N430 Parametre Listesi.pdf`
- `Directories.txt`

Then build the FAISS index:

```bash
python rebuild_index.py
```

You should see logs indicating documents were loaded and an index was saved under `vector/index/`.

## 🎯 Usage

### Flask App (recommended)

```bash
python flask_app.py
```

Open `http://localhost:5000` in your browser.

Highlights:
- ChatGPT-like modern UI
- Markdown rendering with code copy buttons
- Session-based history

### Streamlit App (alternative)

```bash
streamlit run main.py
```

Open `http://localhost:8501` in your browser.

Sidebar includes sample questions, temperature, and model selectors.

## 🔧 Configuration

### Environment Variables (.env)

```bash
OPENAI_API_KEY=your_openai_api_key_here

# Optional (not required by default flow)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Optional: if you plan to enable/replace web search logic
# GOOGLE_SEARCH_API_KEY=...
# GOOGLE_SEARCH_ENGINE_ID=...
```

### Customizing the Prompt

Edit `prompts/main_prompt.txt` to tune the assistant’s behavior and response style.

## 💡 Example Questions

1) Battery status
```
"How can I check the battery status?"
```

2) GPRS settings
```
"How do I configure GPRS parameters?"
```

3) SMS notifications
```
"How can I set up SMS/call notifications?"
```

4) Remote control
```
"How can I reboot the device remotely?"
```

### Expected Answer Format

The assistant typically returns structured Markdown like:

```markdown
## 📋 Command Info

### 🔍 Command Name: [Name]
Description: [Short description]

### 📱 SMS Format
```
[SMS command]
```

### 💡 Usage Notes
[Explanation]

### ⚙️ Parameter Details
- Parameter ID: [ID]
- Type: [Type]
- Default: [Value]

### 📝 Example
```
[Example SMS]
```
```

## 🐳 Run with Docker (Streamlit)

```bash
# Build image
docker build -t niki-fmb130 .

# Run container (exposes Streamlit at 8501)
docker run -e OPENAI_API_KEY=your_openai_api_key_here -p 8501:8501 niki-fmb130
```

## 🔍 Troubleshooting

1) “OPENAI_API_KEY not set”
- Ensure `.env` exists and contains a valid key, or export it in your shell

2) “Index not found”
- Confirm your docs are under `data/`
- Rebuild the index: `python rebuild_index.py`

3) Import or dependency errors
- Verify your virtual environment is active
- Reinstall deps: `pip install -r requirements.txt`

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add amazing feature"`)
4. Push the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License

## 📞 Contact

- **Owner**: Sami Özsoy
- **Email**: [your.email@example.com]
- **Repo**: [`https://github.com/username/wake_up_nikki`](https://github.com/username/wake_up_nikki)

---

Note: This project focuses on Teltonika FMB130 commands with a local RAG index. Validate responses and test carefully before production use.