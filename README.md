# 🚀 AI SaaS Research Pipeline

An asynchronous multi-agent AI pipeline that researches SaaS applications, extracts developer-focused capabilities, verifies information against official documentation, and generates an interactive HTML dashboard.

## Dashboard Preview

<img src="assets/<img width="639" height="805" alt="image" src="https://github.com/user-attachments/assets/ad850025-f235-4550-84d4-01db8c738511" />
" alt="![Uploading image.png…]()
" width="500">


---
---

## ✨ Features

- 🤖 Multi-agent architecture (Researcher, Verifier, Analyzer)
- ⚡ Asynchronous pipeline using `asyncio`
- 🔍 Automated web search and documentation crawling
- 🧠 Structured extraction using Google Gemini
- ✅ Verification against official documentation
- 📊 Interactive HTML dashboard generation
- 📁 JSON and CSV exports
- 🔄 Checkpoint recovery for interrupted runs
- 📈 Analytics and summary statistics

---

## 🏗️ Architecture

```
Input CSV
    │
    ▼
Researcher Agent
    │
    ▼
Verifier Agent
    │
    ▼
Analyzer Agent
    │
    ▼
JSON / CSV
    │
    ▼
Interactive HTML Dashboard
```

---

## 🛠️ Tech Stack

- **Language:** Python
- **LLM:** Google Gemini
- **Search:** Tavily API
- **Web Scraping:** HTTPX, BeautifulSoup
- **Validation:** Pydantic
- **Templates:** Jinja2
- **Data Processing:** Pandas
- **Async:** asyncio

---

## 📂 Project Structure

```
.
├── agent/
├── core/
├── services/
├── storage/
├── templates/
├── data/
├── output/
├── reports/
├── tests/
├── main.py
└── README.md
```

---

## 🚀 Setup

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment

Create a `.env` file using `.env.example` and add:

```text
GOOGLE_API_KEY=your_api_key
TAVILY_API_KEY=your_api_key
MAX_CONCURRENT_RESEARCHERS=5
```

---

## ▶️ Run

Run the full pipeline:

```bash
python main.py --input data/apps.csv
```

Dry run:

```bash
python main.py --dry-run
```

Ignore checkpoints:

```bash
python main.py --input data/apps.csv --force
```

---

## 📊 Output

The pipeline generates:

```
output/
├── research.json
├── research.csv
└── statistics.json

reports/
└── case_study.html
```

The HTML dashboard includes:

- Summary statistics
- Search & filters
- Confidence scores
- Verification status
- Evidence links
- Light/Dark mode

---

## 💡 Design Highlights

- Clean Architecture
- Modular service layer
- Dependency injection
- Async execution
- Automatic retry with exponential backoff
- Checkpoint recovery for long-running jobs
- Structured Pydantic models

---

## 🚧 Future Improvements

- PostgreSQL storage
- Docker support
- Additional LLM providers
- Scheduled incremental research
- Distributed execution
