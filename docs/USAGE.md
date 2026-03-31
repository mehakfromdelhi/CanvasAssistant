# Usage Guide

## What you need

- Canvas base URL
- Canvas personal access token
- Canvas course ID
- Gemini API key
- Local academic folder path

## Running the agent

```powershell
python run_agent.py
```

## Where outputs go

Outputs are written under:

```text
ACADEMICS_ROOT/Course Name/Session N/
```

Each session contains:

- `pages/`
- `files/`
- `links/`
- `summaries/`

## Summary provider order

1. Gemini
2. OpenAI
3. Local fallback summary

