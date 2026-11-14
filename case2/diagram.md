flowchart TD
    PDF[PDF input] --> SAFE[safe_open_pdf<br>size & magic check]
    SAFE --> EXT[extract_text_and_tables<br>pdfplumber]
    EXT --> PARSE[parse<br>regex‑based field extraction]
    PARSE --> VAL[validate<br>missing fields, reconciliation]
    VAL --> CONF[confidence scoring<br>weighted field confidences]
    CONF --> ROUTE{overall confidence<br>≥ 0.70?}
    ROUTE -- yes --> JSON[JSON output<br>no review needed]
    ROUTE -- no --> REVIEW[JSON output<br>needs_review = true<br>review_reasons]
    EXT -.-> MASK[masking.mask_id<br>optional LLM path]
    MASK -.-> LLM[llm_extractor.extract_with_llm<br>DISABLED by default]
    LLM -.-> AUDIT[audit/llm_payload.jsonl]