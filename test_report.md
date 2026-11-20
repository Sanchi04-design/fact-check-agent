# Truth Layer Evaluation Report: Live Trap Document Audit
**Run Date:** 2026-11-20 17:10:32  
**Model Used:** `gemini-3.5-flash`  
**Document Audited:** `sample_trap.pdf` (10 embedded trap claims)  

## Executive Summary
- **Total Claims Extracted:** 10
- **🟢 Verified:** 0
- **🟡 Inaccurate:** 0
- **🔴 False:** 0
- **⚪ Unverifiable:** 10

> [!WARNING]
> **Grounding Quota Notice (Step 2 - Live Verification):**
> During Step 2 (Google Search Grounding verification), Gemini API returned `429 RESOURCE_EXHAUSTED`:
> ```
> 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
> ```
> **Root Cause:** Grounding with Google Search requires billing enabled on the Google AI Studio project (Free tier accounts receive 429 quota exhaustion on search grounding tool calls).
> **Pipeline Behavior:** Per specifications, the application handled the 429 error gracefully without crashing, preserved all extracted claims, did NOT convert API failures to False, and correctly marked them as `Unverifiable`.
> **User Action Required:** To unlock live search grounding, enable pay-as-you-go billing on your Google AI Studio project at [aistudio.google.com/docs/rate-limits](https://aistudio.google.com/docs/rate-limits).

## Claim-by-Claim Benchmark: Expected vs. Observed

| # | Claim | Page | Expected Verdict | Observed Verdict | Expected Real Fact | Observed Real Fact | Sources |
|---|---|---|---|---|---|---|---|
| 1 | Microsoft completed its acquisition of Activision Blizzard for approximately $69 billion in October 2023. | 1 | **Verified** | **Unverifiable** | Closed transaction for $68.7B on Oct 13, 2023 | N/A | 0 source(s) |
| 2 | Python 3.0 was officially released in December 2008. | 1 | **Verified** | **Unverifiable** | Released on Dec 3, 2008 | N/A | 0 source(s) |
| 3 | Anthropic was founded in 1998 by Steve Jobs and Bill Gates. | 1 | **False** | **Unverifiable** | Founded in 2021 by Dario Amodei, Daniela Amodei & team (not 1998 by Jobs & Gates) | N/A | 0 source(s) |
| 4 | The global human population stands at approximately 7.2 billion people as of 2026. | 1 | **Inaccurate** | **Unverifiable** | Surpassed 8.0B in Nov 2022; ~8.1-8.2B in 2024-2026 (7.2B was ~2013) | N/A | 0 source(s) |
| 5 | Apple reported total net sales of $94.9 billion for its fourth fiscal quarter ended September 28, 2024. | 1 | **Verified** | **Unverifiable** | $94.93B net sales in Q4 FY24 (ended Sep 28, 2024) | N/A | 0 source(s) |
| 6 | Tesla recorded global vehicle deliveries of 499,550 in 2024. | 2 | **Inaccurate** | **Unverifiable** | 499,550 was FY2020 deliveries; FY2024 was ~1.79M deliveries | N/A | 0 source(s) |
| 7 | Shopify reported total revenue of $4.8 billion for the third quarter of 2024. | 2 | **Inaccurate** | **Unverifiable** | $2.16B in Q3 2024 (not $4.8B) | N/A | 0 source(s) |
| 8 | Stripe acquired Spotify in March 2024 for $45 billion. | 2 | **False** | **Unverifiable** | Never acquired; Spotify is an independent public company (SPOT) | N/A | 0 source(s) |
| 9 | The Eiffel Tower in Paris stands at an official architectural height of 150 meters. | 2 | **Inaccurate** | **Unverifiable** | Total architectural height is 330 meters (not 150m) | N/A | 0 source(s) |
| 10 | Alphabet (Google) generated $10 billion in total revenue in full year 2024. | 2 | **False** | **Unverifiable** | Full-year 2024 revenue exceeded $350B (not $10B) | N/A | 0 source(s) |

## Detailed Claim Explanations & Citations

### Claim 1 (Page 1): UNVERIFIABLE
- **Extracted Claim:** "Microsoft completed its acquisition of Activision Blizzard for approximately $69 billion in October 2023."
- **Supporting Quote:** "Microsoft completed its acquisition of Activision Blizzard for approximately $69 billion in October 2023"
- **Expected Verdict:** `Verified`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Closed transaction for $68.7B on Oct 13, 2023 *(Authoritative Source: SEC Form 8-K / Microsoft PR)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 2 (Page 1): UNVERIFIABLE
- **Extracted Claim:** "Python 3.0 was officially released in December 2008."
- **Supporting Quote:** "Python 3.0 was officially released in December 2008"
- **Expected Verdict:** `Verified`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Released on Dec 3, 2008 *(Authoritative Source: Python Software Foundation (python.org))*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 3 (Page 1): UNVERIFIABLE
- **Extracted Claim:** "Anthropic was founded in 1998 by Steve Jobs and Bill Gates."
- **Supporting Quote:** "Anthropic was founded in 1998 by Steve Jobs and Bill Gates"
- **Expected Verdict:** `False`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Founded in 2021 by Dario Amodei, Daniela Amodei & team (not 1998 by Jobs & Gates) *(Authoritative Source: Anthropic official about page / Crunchbase)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 4 (Page 1): UNVERIFIABLE
- **Extracted Claim:** "The global human population stands at approximately 7.2 billion people as of 2026."
- **Supporting Quote:** "As of 2026, the global human population stands at approximately 7.2 billion people across all continents."
- **Expected Verdict:** `Inaccurate`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Surpassed 8.0B in Nov 2022; ~8.1-8.2B in 2024-2026 (7.2B was ~2013) *(Authoritative Source: UN Population Division / US Census Bureau)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 5 (Page 1): UNVERIFIABLE
- **Extracted Claim:** "Apple reported total net sales of $94.9 billion for its fourth fiscal quarter ended September 28, 2024."
- **Supporting Quote:** "Apple reported total net sales of $94.9 billion for its fourth fiscal quarter ended September 28, 2024."
- **Expected Verdict:** `Verified`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** $94.93B net sales in Q4 FY24 (ended Sep 28, 2024) *(Authoritative Source: Apple Form 10-Q / Q4 Earnings Release)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 6 (Page 2): UNVERIFIABLE
- **Extracted Claim:** "Tesla recorded global vehicle deliveries of 499,550 in 2024."
- **Supporting Quote:** "Tesla's global vehicle deliveries were 499,550 in 2024"
- **Expected Verdict:** `Inaccurate`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** 499,550 was FY2020 deliveries; FY2024 was ~1.79M deliveries *(Authoritative Source: Tesla IR / SEC 10-K)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 7 (Page 2): UNVERIFIABLE
- **Extracted Claim:** "Shopify reported total revenue of $4.8 billion for the third quarter of 2024."
- **Supporting Quote:** "Shopify reported total revenue of $4.8 billion for the third quarter of 2024."
- **Expected Verdict:** `Inaccurate`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** $2.16B in Q3 2024 (not $4.8B) *(Authoritative Source: Shopify Q3 2024 Earnings Release)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 8 (Page 2): UNVERIFIABLE
- **Extracted Claim:** "Stripe acquired Spotify in March 2024 for $45 billion."
- **Supporting Quote:** "Stripe acquired music streaming service Spotify in March 2024 for $45 billion"
- **Expected Verdict:** `False`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Never acquired; Spotify is an independent public company (SPOT) *(Authoritative Source: Spotify IR / SEC EDGAR)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 9 (Page 2): UNVERIFIABLE
- **Extracted Claim:** "The Eiffel Tower in Paris stands at an official architectural height of 150 meters."
- **Supporting Quote:** "The Eiffel Tower in Paris stands at an official architectural height of 150 meters."
- **Expected Verdict:** `Inaccurate`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Total architectural height is 330 meters (not 150m) *(Authoritative Source: SETE (Société d'Exploitation de la Tour Eiffel))*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`

### Claim 10 (Page 2): UNVERIFIABLE
- **Extracted Claim:** "Alphabet (Google) generated $10 billion in total revenue in full year 2024."
- **Supporting Quote:** "Alphabet (Google) generated $10 billion in total revenue in full year 2024."
- **Expected Verdict:** `False`
- **Observed Verdict:** `Unverifiable` (Confidence: 0%)
- **Benchmark Ground-Truth Fact:** Full-year 2024 revenue exceeded $350B (not $10B) *(Authoritative Source: Alphabet SEC 10-K / Investor Relations)*
- **Explanation:** Verification failed due to an API error after 3 attempts: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}
- **Grounded Sources:** None
- **API Error Captured:** `429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. ', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://aistudio.google.com/docs/rate-limits'}]}]}}`
