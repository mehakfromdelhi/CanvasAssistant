# Architecture

## Core flow

1. `config.py` loads environment variables
2. `canvas_api.py` talks to the Canvas API
3. `pipeline.py` orchestrates retrieval and storage
4. `extractors.py` extracts readable text from HTML and PDFs
5. `summarizer.py` generates summaries
6. `scaffold.py` creates course/session folders

## Main modules

- `run_agent.py`: entrypoint
- `main.py`: app bootstrap and run output
- `pipeline.py`: main processing loop
- `canvas_api.py`: Canvas access
- `summarizer.py`: Gemini/OpenAI/local fallback summarization

## Storage model

The app is local-first.

- No database
- No hosted backend
- No server-side credential storage
- Files are saved directly into the user's academic folder tree

