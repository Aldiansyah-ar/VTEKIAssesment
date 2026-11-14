flowchart TD
    subgraph Corpus[Policy corpus]
        PUB[luggage_policy.txt<br>visibility=public]
        STF[internal_baggage_ops.txt<br>visibility=staff]
    end

    PUB & STF --> CHUNK[chunk_policy<br>section‑level chunks]
    CHUNK --> RET[build_retriever<br>TF‑IDF default<br>Sentence‑Transformers optional]

    Q[User query<br>CLI --role passenger/staff] --> VAL[validate_input<br>length & emptiness]
    VAL --> INJ[detect_injection<br>prompt‑injection patterns]
    INJ --> RBAC{RBAC check<br>role vs. staff‑only signals}
    RBAC -- blocked --> BLOCK[blocked response]
    RBAC -- allowed --> SEARCH[retriever.search<br>role‑filtered top‑k=4]
    SEARCH --> CTX{retrieved<br>chunks?}
    CTX -- none --> REF[refusal message]
    CTX -- yes --> PROMPT[build prompt]
    PROMPT --> LLM{OPENAI_API_KEY?}
    LLM -- yes --> GPT[OpenAI chat completion<br>gpt‑4o‑mini etc.]
    LLM -- no --> EXT[extractive answer<br>best sentence + citation]
    GPT & EXT --> ANS[answer + citations]
    ANS --> OUT[results.json]