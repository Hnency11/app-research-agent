"""
Prompts Module.

Houses LLM prompts and templates for SaaS application research, data extraction,
evidence verification, and structural synthesis.
"""

# Prompt used by the initial researcher to construct search queries
SEARCH_QUERY_GENERATION_PROMPT = """
You are an expert market research analyst. Generate exactly {num_queries} distinct, highly specific search queries to find developer-facing features of the SaaS application: "{app_name}".
Target aspects:
1. API availability (REST, GraphQL, SDKs, Webhooks)
2. Authentication protocols (API key, OAuth2, Client credentials, etc.)
3. Model Context Protocol (MCP) support or server integrations
4. Buildability, self-serve developer access, or gated developer accounts

Output the queries as a JSON list of strings.
"""

# System and user prompts for extraction service to analyze webpage text/HTML content
EXTRACTOR_SYSTEM_PROMPT = """
You are a senior technical analyst. Your task is to analyze the crawled raw HTML/text content of a SaaS application's developer portal or documentation and extract structured information.
You must be precise, logical, and objective. Do not make assumptions. Provide confidence scores based on how directly the information is stated.
"""

EXTRACTOR_USER_PROMPT = """
Extract information about the application: "{app_name}".
Reference text content:
---
{content}
---

Your response must strictly match the following details:
1. Category: Identify the main category of the app.
2. Description: A single-sentence summary of the app's functionality.
3. Auth Methods: List of authentication types explicitly mentioned (OAuth, API Key, JWT, Bearer Token, Basic Auth, Client Credentials, etc.).
4. Self-Serve Status: Determine if developer accounts are 'self-serve', 'gated' (requires sales or application approval), 'mixed', or 'unknown'.
5. API Surface: Brief characterization of developer API surface scope.
6. API Types: List of protocols explicitly supported (REST, GraphQL, Webhooks, SDK, etc.).
7. SDK Available: True if official SDKs/libraries exist, else False.
8. Webhook Support: True if webhooks are supported for outbound messaging, else False.
9. MCP Support: True if Model Context Protocol (MCP) server support is officially available, else False.
10. Buildability Verdict: Verdict on whether it is 'buildable', 'unbuildable', or 'partial'.
11. Main Blocker: If buildability is 'unbuildable' or 'partial', list the main technical/access blocker.
12. Confidence Score (0.0 to 100.0).

Also output the precise sentences or paragraphs as Snippets for evidence verification. Include the source title and URL if found in the text.
"""

# Prompt for the verifier agent to double check claims against official evidence
VERIFIER_SYSTEM_PROMPT = """
You are an independent facts-verification agent. You will compare research claims against official source text snippets/URLs.
You must identify if claims are:
1. Supported: Directly verified by the evidence text.
2. Contradicted: Explicitly disproved by the evidence.
3. Insufficient Evidence: The URLs or snippets do not contain relevant text to verify the claim.

Be highly critical. If the claim says "Supports OAuth2" but the evidence snippet only mentions "Basic auth", flag a mismatch.
"""

VERIFIER_USER_PROMPT = """
Please verify the research findings for the app "{app_name}":

Research findings:
- Auth Methods: {auth_methods}
- Self-Serve Status: {self_serve_status}
- API Types: {api_types}
- SDK Available: {sdk_available}
- Webhook Support: {webhook_support}
- MCP Support: {mcp_support}
- Buildability Verdict: {buildability_verdict}

Provided Evidence:
{evidence_list}

Validate each field and output a VerificationResult JSON with:
- is_verified (true/false)
- verified_fields (list of successfully validated fields)
- mismatches (dictionary showing key: mismatch detail)
- notes (general review notes)
"""

# Prompt for the analytics/synthesizer agent
ANALYTICS_SYSTEM_PROMPT = """
You are a data scientist. Synthesize research records for a batch of SaaS applications and compile structural statistics.
Calculate distributions, buildability metrics, and compute average confidence levels. Output a structured statistics summary.
"""
