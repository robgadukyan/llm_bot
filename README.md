# Agentic Telegram Teaching Assistant

Individual homework solution for **AUA NLP: Build an Agentic Telegram Teaching Assistant**.

The bot accepts lecture slides, parses slide text, calls a **local OpenAI-compatible LLM server** through `vLLM` or `llama.cpp`, searches for supporting web resources, generates a teaching package, previews it in Telegram, and sends the package by email only after explicit `/send` confirmation.

## 1. Features matched to the assignment

- `/start` introduces the bot and gives a usage example.
- `/help` lists commands and limitations.
- `/plan` runs the full slide-based lesson-planning workflow.
- `/research` returns supporting web resources.
- `/status` shows uploaded file, current state, and errors.
- `/send` sends the latest generated preview by email after confirmation.
- PDF slide parsing is supported; PPTX parsing is included as a bonus.
- Local LLM backend is isolated in `llm_backend.py`.
- Secrets are read from `.env`; `.env.example` is safe to commit.
- Bad files, missing email, failed web search, and email errors are handled without crashing.

## 2. Repository structure

```text
agentic-teaching-bot/
  README.md
  .env.example
  requirements.txt
  pyproject.toml
  bot.py
  llm_backend.py
  agents/
    orchestrator.py
    prompts.py
  tools/
    slides.py
    web_search.py
    email.py
    logger.py
  examples/
    sample_slides.pdf
    sample_output.md
  report/
    design_report.md
  tests/
    test_slides.py
    test_email.py
  data/
    uploads/.gitkeep
    logs/.gitkeep
```

## 3. Setup

```bash
git clone <your-repo-url>
cd agentic-teaching-bot
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add:

```text
TELEGRAM_BOT_TOKEN=...
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:1.5b
LLM_MAX_TOKENS_CAP=900
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=...
```

For Gmail, use an app password, not your normal password.

## 4. Run a local LLM server

### Option A: Ollama (recommended for low-resource computers)

Example:

```bash
ollama pull qwen2.5:1.5b
ollama serve
```

Then set:

```text
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:1.5b
LLM_API_KEY=EMPTY
LLM_MAX_TOKENS_CAP=900
```

### Option B: vLLM

Example:

```bash
pip install vllm
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --served-model-name local-qwen \
  --host 127.0.0.1 \
  --port 8000
```

Then set:

```text
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_MODEL=local-qwen
LLM_API_KEY=EMPTY
```

### Option B: llama.cpp

Example using the llama.cpp server binary:

```bash
./llama-server -m ./models/your-model.gguf -c 4096 --host 127.0.0.1 --port 8000
```

Then set:

```text
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_MODEL=local-gguf
LLM_API_KEY=EMPTY
```

## 5. Run the bot

```bash
python bot.py
```

In Telegram:

1. Open the bot.
2. Send `/start`.
3. Upload `examples/sample_slides.pdf` or your own lecture PDF.
4. Run:

```text
/plan duration=90 audience="BA NLP students" language=English email=recipient@example.com
```

5. Review the preview.
6. Send only after approval:

```text
/send
```

## 6. Testing

```bash
pytest
```

The included tests check slide parsing and email-body construction. Full Telegram and SMTP tests require real credentials, so they are demonstrated in the demo video/live demo instead of automated unit tests.

## 7. Demo video script

Use `examples/sample_slides.pdf` and record these actions:

1. Start bot: `/start`.
2. Upload sample PDF.
3. Show `/status`.
4. Run `/research`.
5. Run `/plan duration=60 audience="BA NLP students" language=English email=your_email@example.com`.
6. Show preview.
7. Confirm with `/send`.
8. Show received email.

## 8. Limitations

- OCR is not included. Scanned image-only PDFs will fail with a clear error.
- Web search depends on availability of the DuckDuckGo search package and network access.
- The bot uses in-memory session state. For production, replace it with SQLite or Redis.
- The local LLM must be running before `/plan` unless `ALLOW_LLM_FALLBACK=true` is set for emergency demo mode.

## 9. Academic integrity note

This code is a complete starter implementation. Before submitting, run it locally, record your own demo, and make sure you understand every file and configuration choice.
