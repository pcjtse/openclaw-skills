---
name: Financial Research Expert
description: A multi-tiered workflow for gathering and analyzing professional financial data using custom scripts.
---

# Financial Research Skill

This skill outlines a professional workflow for financial research. Follow this structured approach when a user asks you to research a specific company, ticker, or macroeconomic trend. The design mimics the tiered research workflow used by professionals (e.g., Bloomberg -> FactSet -> Refinitiv -> Open APIs) adapted to work with our free custom tools.

## Prerequisites
Before beginning any research, ensure the required dependencies are installed:
```bash
pip install -r financial-services-skills/scripts/requirements.txt
```

## The Research Workflow
Always proceed through these three tiers of research systematically. Do not skip tiers unless explicitly requested by the user.

### Tier 1: Core Financial & Market Data (The "Bloomberg" Equivalent)
Start your research by getting the real-time or recent baseline for the target company/stock.
*   **Tool:** `financial-services-skills/scripts/stock_data.py`
*   **Purpose:** Gather immediate quantitative context, pricing metrics, analyst sentiment, and breaking news.
*   **Command:** `python scripts/stock_data.py <TICKER>`
*   **Actionable Output:** Use this data to summarize the company's current market position (Market Cap, P/E ratios), what analysts are saying (upgrades/downgrades), and the immediate news cycle.

### Tier 2: Primary Source & Regulatory Filings (The "FactSet / Refinitiv" Equivalent)
After grasping the high-level market perspective, dive deep into the fundamental financial reporting directly from the source.
*   **Tool:** `financial-services-skills/scripts/sec_edgar.py`
*   **Purpose:** Download the SEC 10-K (Annual) and 10-Q (Quarterly) filings for rigorous fundamental analysis.
*   **Command:** `python scripts/sec_edgar.py <TICKER> --email <your-email> --company-name <your-identifier> --limit 1`
*   **Actionable Output:** Read through the downloaded documents located in the target output directory (default: `./sec_filings`). Analyze the Management's Discussion and Analysis (MD&A), Risk Factors, and detailed financial statements to understand the core drivers of the business and potential headwinds.

### Tier 3: Open Market Intelligence & Sentiment (The "Open API" Equivalent)
Once the company-specific fundamentals and baseline market views are understood, broaden the scope.
*   **Tool:** `financial-services-skills/scripts/web_search.py`
*   **Purpose:** Gather macroeconomic context, competitor actions, regulatory news, or sentiment not yet captured in structural reporting.
*   **Command:** `python scripts/web_search.py <your targeted research query>`
*   **Actionable Output:** Synthesize these real-world context clues with the financial and regulatory data gathered in Tiers 1 and 2 to form a holistic, professional research summary for the user. 

## Final Output Structure
When presenting your research back to the user, combine the findings from all three tiers into a cohesive report:
1.  **Executive Summary:** A high-level overview.
2.  **Market & Analyst View (Tier 1):** Current metrics and sentiment.
3.  **Fundamental Analysis (Tier 2):** Insights drawn directly from SEC filings.
4.  **Broader Context & Risks (Tier 3):** External factors, competitors, and macroeconomic climate.
5.  **Final Recommendation Score:** A definitive score out of 10 indicating the overall conviction/attractiveness of the investment, supported by a brief justification based on the prior analysis.
