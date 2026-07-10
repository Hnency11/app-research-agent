"""
Main Pipeline Orchestrator.

Orchestrates the asynchronous pipeline execution:
1. Loads SaaS app inputs from CSV.
2. Instantiates database storage, helper services, and AI agents.
3. Conducts initial search, scraping, and LLM-based parsing (Researcher Agent).
4. Validates statements against official documentation evidence URLs (Verifier Agent).
5. Aggregates data matrices and computes research metrics (Analyzer Agent).
6. Generates visual case study web dashboards (HTML Generator Agent).
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd
from core.config import settings
from core.logger import logger
from core.models import AppResearch, ResearchStatistics
from agent.researcher.researcher_agent import ResearcherAgent
from agent.verifier.verifier_agent import VerifierAgent
from agent.analyzer.analyzer_agent import AnalyzerAgent
from agent.html_generator.generator import HTMLReportGenerator
from services.search_service import SearchService
from services.browser_service import BrowserService
from services.llm_service import LLMService
from services.extractor_service import ExtractorService
from storage.json_storage import JSONStorage
from storage.csv_storage import CSVStorage


def load_apps_list(file_path: Path) -> List[dict]:
    """Loads SaaS applications list from CSV or markdown table formats."""
    is_markdown = False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for _ in range(15):
                line = f.readline()
                if not line:
                    break
                if "|" in line or line.startswith("###"):
                    is_markdown = True
                    break
    except Exception:
        pass

    if is_markdown:
        logger.info("Markdown table format detected in apps list. Parsing rows...")
        apps = []
        current_category = "General"
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("###"):
                    current_category = line.replace("###", "").strip()
                    if "." in current_category:
                        parts = current_category.split(".", 1)
                        if parts[0].strip().isdigit():
                            current_category = parts[1].strip()
                    continue
                if line.startswith("|") and "---" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        num_part = parts[0]
                        app_name = parts[1]
                        hint = parts[2]
                        if app_name.lower() in ("app", "#", "website / hint") or not num_part.isdigit():
                            continue
                        
                        # Clean hint (remove comments inside parentheses)
                        url = hint.split()[0] if hint else ""
                        if url and not url.startswith("http"):
                            url = "https://" + url
                        
                        apps.append({
                            "app_name": app_name,
                            "homepage_url": url,
                            "category": current_category
                        })
        return apps
    else:
        logger.info("Standard CSV format assumed for apps list.")
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")

async def process_single_app(
    app_row: dict,
    researcher_agent: ResearcherAgent,
    verifier_agent: VerifierAgent,
    json_storage: JSONStorage,
    semaphore: asyncio.Semaphore,
    dry_run: bool,
    force: bool = False
) -> AppResearch:
    """Orchestrates the research and verification steps for a single application.

    Respects checkpoints: if data/raw/{safe_name}.json already exists and --force
    is not set, loads the cached result and skips search, crawling and LLM extraction.
    """
    app_name = app_row.get("app_name", "Unknown App")
    homepage_url = app_row.get("website") or app_row.get("homepage_url", "")
    if homepage_url and not homepage_url.startswith("http"):
        homepage_url = "https://" + homepage_url

    async with semaphore:
        # --- Checkpoint check ---
        if not force:
            cached = await json_storage.load_app_research(app_name, stage="raw")
            if cached is not None:
                logger.info(f"[CHECKPOINT] Skipping {app_name} (checkpoint found).")
                return cached

        logger.info(f"[PIPELINE-FLOW] Commencing research execution for app: {app_name}")
        
        try:
            # Stage 1: Researcher Agent
            raw_research = await researcher_agent.run(app_name, homepage_url)
            
            # Preserve the category from data/apps.csv
            csv_category = app_row.get("category")
            if csv_category:
                raw_research.category = csv_category

            # Always stamp last_updated with the authoritative Python UTC time
            raw_research.last_updated = datetime.now(timezone.utc)

            await json_storage.save_app_research(raw_research, stage="raw")

            # Stage 2: Verifier Agent
            verified_research = await verifier_agent.run(raw_research)

            logger.info(f"[PIPELINE-FLOW] Finished research execution successfully for app: {app_name}")
            return verified_research

        except Exception as e:
            logger.error(f"[PIPELINE-FLOW] Critical failure processing app '{app_name}': {str(e)}")
            from core.models import VerificationStatus
            return AppResearch(
                app_name=app_name,
                category=app_row.get("category") or "Failed Extraction",
                description="Extraction failure encountered during execution.",
                auth_methods=[],
                self_serve_status="unknown",
                api_surface="N/A",
                api_types=[],
                sdk_available=False,
                webhook_support=False,
                mcp_support=False,
                buildability_verdict="unknown",
                main_blocker=str(e),
                evidence=[],
                confidence_score=0.0,
                verification_status=VerificationStatus.FAILED,
                verification_notes=f"Error log: {str(e)}",
                last_updated=datetime.now(timezone.utc)
            )


async def run_pipeline(input_csv: Path, dry_run: bool = False, force: bool = False) -> None:
    """Executes the complete end-to-end SaaS research pipeline.

    Args:
        input_csv: Path to input CSV file containing app list.
        dry_run: Flag to simulate service responses instead of calling actual APIs.
        force: If True, bypass checkpoints and reprocess all apps.
    """
    start_time = time.monotonic()
    logger.info("==================================================")
    logger.info(f"Starting SaaS Research Pipeline (Dry Run: {dry_run}, Force: {force})")
    logger.info("==================================================")

    # 1. Verify and load application list from input path
    if not input_csv.exists():
        logger.error(f"Input SaaS list CSV not found at: {input_csv}")
        sys.exit(1)
        
    try:
        input_apps = load_apps_list(input_csv)
        logger.info(f"Loaded {len(input_apps)} apps from input list.")
    except Exception as e:
        logger.critical(f"Failed parsing input list file: {str(e)}")
        sys.exit(1)

    # 2. Instantiate storage components
    json_storage = JSONStorage()
    csv_storage = CSVStorage()

    # 3. Instantiate base services
    search_service = SearchService(api_key=settings.TAVILY_API_KEY)
    browser_service = BrowserService(timeout=settings.REQUEST_TIMEOUT_SECONDS)
    llm_service = LLMService(api_key=settings.GEMINI_API_KEY, provider="gemini")
    extractor_service = ExtractorService(browser_service=browser_service, llm_service=llm_service)

    # 4. Instantiate pipeline agents
    researcher_agent = ResearcherAgent(
        search_service=search_service,
        browser_service=browser_service,
        extractor_service=extractor_service
    )
    verifier_agent = VerifierAgent(browser_service=browser_service, llm_service=llm_service)
    analyzer_agent = AnalyzerAgent()
    html_generator = HTMLReportGenerator()

    # 5. Execute research + verification concurrently with semaphore limit
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_RESEARCHERS)
    
    tasks = [
        process_single_app(app, researcher_agent, verifier_agent, json_storage, semaphore, dry_run, force)
        for app in input_apps
    ]
    
    logger.info(f"Dispatched async task execution pool. Max concurrency limit: {settings.MAX_CONCURRENT_RESEARCHERS}")
    results: List[AppResearch] = await asyncio.gather(*tasks)
    # Filter out None results defensively
    results = [r for r in results if r is not None]

    # 6. Write consolidated output deliverables to output directory
    logger.info("Writing consolidated output deliverables to output/ directory...")
    await json_storage.save_bulk_research(results, "research.json")
    await csv_storage.save_bulk_research(results, "research.csv")

    elapsed_time = time.monotonic() - start_time

    # 7. Run Analyzer Agent to compile statistics
    stats: ResearchStatistics = await analyzer_agent.run(
        research_list=results,
        total_inputs=len(input_apps),
        elapsed_time=elapsed_time
    )

    # 8. Generate HTML case study report
    report_path = await html_generator.run(research_list=results, stats=stats)
    logger.info(f"HTML report written to: {report_path}")

    logger.info("==================================================")
    logger.info(f"SaaS Pipeline run completed in {elapsed_time:.2f} seconds.")
    logger.info(f"Consolidated results saved to output/research.json and output/research.csv")
    logger.info("==================================================")


def main() -> None:
    """CLI script parser and execution starter."""
    parser = argparse.ArgumentParser(description="SaaS App Research AI Pipeline")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/apps.csv",
        help="Path to input SaaS application list CSV (default: data/apps.csv)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Run pipeline using mockup values without making search or LLM API calls"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess all apps, ignoring existing raw checkpoints"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    
    # Run pipeline loop asynchronously
    asyncio.run(run_pipeline(input_path, dry_run=args.dry_run, force=args.force))


if __name__ == "__main__":
    main()
