# SaaS Research Pipeline Architecture

A production-grade, asynchronous AI research pipeline designed to analyze SaaS applications for developer friendliness, API structures, existing Model Context Protocol (MCP) integrations, and buildability metrics.

This project implements a modular **Clean Architecture** to separate concerns between raw information harvesting, validation verification, storage serialization, and analytics presentation.

---

## Architecture Overview

The system operates as an orchestrator coordinating three specialized AI agents, four structural services, two storage engines, and a visual HTML renderer:

```
                  [ data/apps.csv ] (Input App List)
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│                   main.py                        │
│             (Pipeline Orchestrator)              │
└─────────────────────────┬────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌────────────────┐┌────────────────┐┌───────────────┐
│Researcher Agent││Verifier Agent  ││Analyzer Agent │
└────────┬───────┘└───────┬────────┘└───────┬───────┘
         │                │                 │
         │                ├─────────────────┘
         ▼                ▼
┌──────────────────────────────────────────────────┐
│                   Services                       │
│ (Search, Browser Scraper, LLM Schema Extractor)  │
└─────────────────────────┬────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│               Storage & Delivery                 │
│    (JSON Staging, CSV Exports, Jinja HTML Report)│
└──────────────────────────────────────────────────┘
```

---

## Directory Structure

```
saas-research-pipeline/
├── .env.example              # Template for API keys and limits configuration
├── README.md                 # Project architectural layout and developer guides
├── requirements.txt          # Python packaging and dependency declarations
├── main.py                   # Core orchestrator file to execute pipeline runs
├── data/                     # Data staging directory
│   ├── apps.csv              # Input list of target SaaS applications (CSV format)
│   ├── raw/                  # Output storage for initial raw researcher extracts (JSON)
│   ├── processed/            # Consolidated structured research results
│   └── verified/             # Outputs that passed validation assertions (JSON)
├── core/                     # Core helper modules
│   ├── config.py             # Settings configurations validated via pydantic-settings
│   ├── logger.py             # Rich log handling and file rotation logging setup
│   ├── models.py             # Pydantic schemas: AppResearch, Evidence, VerificationResult
│   ├── prompts.py            # AI prompting systems for extraction and checking
│   └── utils.py              # Common helpers: AsyncRateLimiter, exponential retry decorators
├── services/                 # Infrastructure interface layers
│   ├── base.py               # Abstract base service declarations (ABCs)
│   ├── search_service.py     # Tavily/Serper Search client integrations
│   ├── browser_service.py    # BeautifulSoup & HTTPX web scraper utility
│   ├── llm_service.py        # OpenAI/Gemini client validation and structure parsing
│   └── extractor_service.py  # Coordinates scraping, chunking, and feature extraction
├── agent/                    # Autonomous pipeline nodes
│   ├── base.py               # Abstract Base Agent template
│   ├── researcher/           # Researcher Agent: Generates queries and extracts raw SaaS cards
│   ├── verifier/             # Verifier Agent: Cross-checks statements against official links
│   ├── analyzer/             # Analyzer Agent: Compiles statistical aggregations over batch runs
│   └── html_generator/       # Generator: Compiles results into an interactive web dashboard
├── templates/                # Visual formatting layouts
│   └── report_template.html  # Jinja2 premium styled HTML template (glassmorphism/filters)
├── output/                   # Consolidations directory
│   ├── research.json         # Raw consolidation JSON database
│   ├── research.csv          # Flat tabular database for spreadsheet processing (flattened)
│   └── statistics.json       # Synthesized analytical statistics
├── reports/                  # Pipeline deliverables directory
│   └── case_study.html       # Fully compiled HTML report dashboard
├── logs/                     # Log diagnostics
│   └── pipeline.log          # File rotated log dump
└── tests/                    # Project test suite
    ├── conftest.py           # Shared fixtures
    ├── test_agents.py        # Verifies agent interactions
    ├── test_services.py      # Verifies HTTPX and BS4 extractor utilities
    └── test_storage.py       # Verifies JSON staging and flat CSV transformations
```

---

## Core Data Models (`core/models.py`)

1. **`Evidence`**: Captures documentation references (`url`, `title`, `snippet`, `extracted_at`).
2. **`VerificationResult`**: Formulates verifier analysis (`is_verified`, `verified_fields`, `mismatches`, `notes`, `verified_at`).
3. **`AppResearch`**: The primary SaaS profile database schema. Optimized for flat mapping to support CSV compatibility:
   - Lists of `auth_methods` and `api_types` are flattened into comma-separated text strings for spreadsheet engines.
   - Enums validate `self_serve_status`, `buildability_verdict`, and `verification_status` parameters.
4. **`ResearchStatistics`**: Represents the final batch research analytics aggregates.

---

## Design Choices & Production Features

- **SOLID Principles**: Clean interfaces (`services/base.py`, `agent/base.py`) isolate third-party integrations (e.g. search engine changes, provider changes) from agent logic.
- **Asynchronous Execution**: Pipeline coordinates tasks concurrently using `asyncio.gather` while maintaining thread-safety.
- **Throttling & Concurrency Limits**: Outbound crawlers and search actions are bounded by an asynchronous semaphore (`settings.MAX_CONCURRENT_RESEARCHERS`) and `AsyncRateLimiter` to avoid rate limits or ip blocking.
- **Exponential Backoff**: Transient connection errors are intercepted by `retry_async` decorator, applying variable backoff delays and random jitter.
- **Mock / Dry Run Mode**: Run `python main.py --dry-run` to trace the entire pipeline loop using structural mockup data without consuming LLM tokens or calling web crawler requests.

---

## Setup & Running

### 1. Installation
Ensure Python 3.12 is installed, then install package requirements:
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Configure your API keys and concurrency limits:
```bash
cp .env.example .env
# Edit .env file with your GEMINI_API_KEY, TAVILY_API_KEY, etc.
```

### 3. Execution

To run the pipeline using mock responses (dry-run mode) to verify the layout:
```bash
python main.py --dry-run
```

To run the pipeline on the input CSV targeting live endpoints:
```bash
python main.py --input data/apps.csv
```

### 4. Running Tests
Run the project test suite using `pytest`:
```bash
pytest tests/
```
