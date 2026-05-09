# Design Report: Agentic Telegram Teaching Assistant

## 1. Purpose

This project implements a small but complete LLM application for an NLP homework assignment. The system is a Telegram bot that receives lecture slides, extracts slide content, uses a local LLM to generate a teaching package, searches the web for supporting resources, previews the result, and sends it by email only after the user confirms. The focus is not on using the largest model, but on a reliable workflow with clear tools, state, grounding, and failure handling.

## 2. Architecture

The architecture follows a simple custom state-machine and tool-based agent design:

```text
Telegram Bot API -> Session State -> TeachingAssistantAgent
                                  |
                                  +-> Slide Parser / Retriever
                                  +-> Local LLM Backend
                                  +-> Web Search Tool
                                  +-> Email Sender
                                  +-> JSONL Logger / Status
```

The Telegram layer is implemented in `bot.py` using async handlers. Each chat has a `SessionState` object that stores the uploaded file path, latest generated package, recipient email, errors, and whether email confirmation is pending. The agent workflow is implemented in `agents/orchestrator.py`. Prompts are separated into `agents/prompts.py`, and practical tools are placed in the `tools/` directory.

The design intentionally avoids a heavy framework. A simple finite-state flow is easier to debug for homework and satisfies the required agentic behavior: the system calls multiple tools, maintains state, revises output, and logs steps.

## 3. Model Choice and Local LLM Backend

The LLM backend is isolated in `llm_backend.py`. The function `generate(messages, temperature, max_tokens)` calls a local OpenAI-compatible `/v1/chat/completions` endpoint. This allows the same bot code to work with either vLLM or llama.cpp.

Recommended GPU option:

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct --served-model-name local-qwen --host 127.0.0.1 --port 8000
```

Recommended CPU/smaller GPU option:

```bash
./llama-server -m ./models/your-model.gguf -c 4096 --host 127.0.0.1 --port 8000
```

The submitted configuration should document the exact model name, quantization, context length, and command used. For example, a CPU demo can use a 4-bit GGUF instruct model with a 4096-token context. The code also includes an emergency `ALLOW_LLM_FALLBACK=true` mode for debugging, but the main submitted demonstration should use the local LLM server.

## 4. Slide Understanding and RAG

The slide parser supports PDF through `pypdf` and PPTX through `python-pptx`. The parser extracts text by slide/page and stores slide references as `[Slide X]`. The extracted text is converted into a context block with slide references. A simple lexical retriever is included for lightweight RAG-style selection, although the main workflow currently sends a trimmed slide context to the local model.

The agent asks the model for:

1. A slide-grounded summary.
2. A concept map with prerequisites and misconceptions.
3. A full timed teaching plan.
4. A revision checklist.

The prompts instruct the model not to invent slide numbers or URLs and to mark slide-grounded claims using `[Slide X]`.

## 5. Web Research Tool

The web-search tool is implemented in `tools/web_search.py`. It uses DuckDuckGo search through a Python package and returns structured resources: title, URL, snippet, and justification. If search fails, the tool returns an error message instead of inventing fake references. The package includes web resources in the lesson plan only when actual URLs are returned.

## 6. Email Tool and Security

The email tool is implemented in `tools/email.py` with SMTP and TLS. Credentials are read from environment variables. The repository includes `.env.example`, but never commits `.env`. The Telegram bot never sends an email immediately after generation. It first shows a preview and sets `awaiting_send_confirmation=True`; only `/send` triggers SMTP delivery.

## 7. Prompting Strategy

The system prompt defines the assistant as a teaching-planning agent for an NLP course. It requires grounding markers and prohibits invented citations. Separate prompt templates are used for each step:

- `slide_summary_prompt`: lecture title, summary, and keywords.
- `concept_map_prompt`: concepts, relationships, prerequisites, and misconceptions.
- `teaching_plan_prompt`: complete teaching package with objectives, timing, exercise, links, and email body.
- `revision_prompt`: timing, clarity, and grounding check.

This separation improves reliability because each step has a specific task and output expectation.

## 8. Evaluation

| Test case | Input | Expected behavior | Result to show in demo/report |
|---|---|---|---|
| Functional test | Upload `examples/sample_slides.pdf`, run `/plan duration=60 audience="BA NLP students" language=English email=...` | Bot parses slides, calls local LLM, searches web, previews package, waits for `/send` | Screenshot or demo video showing preview and received email |
| Grounding test | Inspect generated package | Several claims include `[Slide X]`; resources include URLs from web search marked `[Web]` | Mark 3-5 claims and their sources |
| Failure test: bad file | Upload `.jpg` or image-only scanned PDF | Bot rejects unsupported file or reports no readable text without crashing | Screenshot of clear error message |
| Failure test: missing email | Run `/plan duration=60 audience="students"` | Bot asks for recipient email and does not generate/send | Screenshot of validation message |
| Web failure test | Disconnect network and run `/plan` | Bot continues with a web-search warning and does not invent links | Log entry and preview warning |

## 9. Latency Note

Latency depends on hardware and model size. On a CPU with a small quantized GGUF model, generation can take several minutes. On a GPU with vLLM and a 7B instruct model, the full workflow is expected to be faster. The demo report should record the actual hardware, model, backend, and approximate times for slide parsing, LLM generation, web search, and email sending.

## 10. Limitations and Future Improvements

The current implementation is intentionally lightweight. It does not include OCR for scanned PDFs, persistent database storage, a web dashboard, or vector embeddings. Future improvements could include OCR, SQLite/Redis persistence, PDF/Markdown attachments, bilingual Armenian-English output, richer trace inspection, and a direct latency comparison between vLLM and llama.cpp.

## 11. Conclusion

The project satisfies the assignment requirements by integrating Telegram UX, a local LLM backend, slide understanding, web research, revision, logging, and email delivery after confirmation. The design is modular enough to demonstrate agentic behavior while remaining simple and debuggable.
