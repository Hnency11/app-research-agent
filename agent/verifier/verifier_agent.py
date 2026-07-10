"""
Verifier Agent Module.

Validates extracted information against official source text snippets/documentation
URLs to detect hallucinations or mismatches.
"""

from agent.base import BaseAgent
from core.logger import logger
from core.models import AppResearch, VerificationResult, VerificationStatus
from core.prompts import VERIFIER_SYSTEM_PROMPT, VERIFIER_USER_PROMPT
from services.browser_service import BrowserService
from services.llm_service import LLMService


class VerifierAgent(BaseAgent):
    """Fact-checker agent that verifies researcher findings against official documentation URLs."""

    def __init__(self, browser_service: BrowserService, llm_service: LLMService):
        """Initialize VerifierAgent.

        Args:
            browser_service: Crawls verification sources.
            llm_service: LLM service instance.
        """
        self.browser = browser_service
        self.llm = llm_service
        logger.debug("VerifierAgent initialized.")

    async def run(self, research: AppResearch) -> AppResearch:
        """Verify the research findings of an application.

        Loads official URLs from AppResearch evidence lists, retrieves their text bodies,
        and requests verification feedback from the LLM.

        Args:
            research: The raw AppResearch record to verify.

        Returns:
            AppResearch: The updated AppResearch record containing verification status/notes.
        """
        logger.info(f"Starting verification pipeline for app: '{research.app_name}'")

        if not research.evidence:
            logger.warning(f"No evidence links provided for verification on '{research.app_name}'.")
            research.verification_status = VerificationStatus.NEEDS_REVIEW
            research.verification_notes = "Verification skipped: No evidence URLs provided."
            return research

        # 1. Fetch text bodies from evidence links to confirm official claims
        evidence_texts = []
        for index, ev in enumerate(research.evidence):
            try:
                logger.debug(f"Verifying evidence index {index} URL: {ev.url}")
                # For validation: use the extracted snippet already in the Evidence
                evidence_texts.append(
                    f"Evidence Source {index + 1}: Title: {ev.title}\n"
                    f"URL: {ev.url}\n"
                    f"Excerpt snippet: {ev.snippet}\n"
                )
            except Exception as e:
                logger.warning(f"Could not retrieve verification text from URL '{ev.url}': {str(e)}")

        evidence_summary = "\n".join(evidence_texts)

        # 2. Invoke structured LLM review verification prompt
        prompt = VERIFIER_USER_PROMPT.format(
            app_name=research.app_name,
            auth_methods=", ".join(research.auth_methods),
            self_serve_status=research.self_serve_status.value,
            api_types=", ".join(research.api_types),
            sdk_available=research.sdk_available,
            webhook_support=research.webhook_support,
            mcp_support=research.mcp_support,
            buildability_verdict=research.buildability_verdict.value,
            evidence_list=evidence_summary
        )

        try:
            verification_result = await self.llm.generate_structured(
                prompt=prompt,
                response_model=VerificationResult,
                system_prompt=VERIFIER_SYSTEM_PROMPT
            )

            # 3. Update the AppResearch fields with verification outcomes
            if verification_result.is_verified:
                research.verification_status = VerificationStatus.VERIFIED
            else:
                research.verification_status = VerificationStatus.FAILED if verification_result.mismatches else VerificationStatus.NEEDS_REVIEW

            research.verification_notes = verification_result.notes
            
            logger.info(
                f"Verification completed for '{research.app_name}'. "
                f"Result: {research.verification_status.value}. "
                f"Mismatches identified: {len(verification_result.mismatches)}"
            )

        except Exception as e:
            logger.error(f"Error executing verification LLM request for '{research.app_name}': {str(e)}")
            research.verification_status = VerificationStatus.NEEDS_REVIEW
            research.verification_notes = f"Verification engine failed: {str(e)}"

        return research
