# Canvas Academic Assistant

A local Python agent that pulls course materials from Canvas, organizes them into session folders, and generates reading summaries with Gemini or OpenAI.

This project is designed for students who want to keep their own academic materials on their own machine while using their own API keys.

## What It Does

- Connects to Canvas with a personal access token
- Reads module items for a selected course
- Pulls Canvas pages, linked files, and many external reading links
- Organizes outputs by course and session
- Generates summaries with Gemini first, then OpenAI as fallback
- Stores raw text, downloaded files, link captures, and summaries locally

## Current Form

This is currently a local command-line Python application.

- It is not a hosted web app
- It is not a packaged desktop installer
- Each user runs it locally on their own machine
- Each user supplies their own Canvas token and AI API key

## Output Structure

The agent writes materials into this structure:

```text
ACADEMICS_ROOT/
  Course Name/
    Session 1/
      files/
      links/
      pages/
      summaries/
    Session 2/
      ...
```

Typical files inside a session:

- `pages/session-page.txt`
- `summaries/session-summary.md`
- `files/resource-01-<name>.pdf`
- `files/resource-01-<name>.txt`
- `links/resource-02-<name>.txt`
- `summaries/resource-02-<name>.summary.md`

## How It Works

1. Load local config from `.env`
2. Authenticate to Canvas with a personal access token
3. List module items for the configured course
4. Pull page content, file metadata, and external links
5. Extract readable text from HTML and PDFs
6. Generate summaries with Gemini
7. Fall back to OpenAI if Gemini is unavailable
8. Fall back to a lightweight local summary if both providers fail
9. Save everything into session-based folders

## Requirements

- Windows PowerShell was the original build environment
- Python 3.12+
- Canvas personal access token
- Gemini API key
- Optional OpenAI API key as a fallback provider

## Installation

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies.
4. Create a local `.env` file from `.env.example`.
5. Run the agent.

Example PowerShell commands:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_agent.py
```

If you want Playwright/browser tooling available locally as well:

```powershell
playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and fill in your own values.

Required values:

```env
CANVAS_BASE_URL=https://your-school.instructure.com
CANVAS_API_TOKEN=your_canvas_token
CANVAS_COURSE_ID=123456
ACADEMICS_ROOT=C:\Path\To\Your\Academics\Q4
COURSE_NAME=Your Course Name
GEMINI_API_KEY=your_gemini_key
```

Optional values:

```env
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini
```

## Quick Start

1. Create a Canvas token in your Canvas account settings.
2. Create a Gemini API key in Google AI Studio.
3. Fill in `.env`.
4. Run:

```powershell
python run_agent.py
```

5. Open the course folder under your configured `ACADEMICS_ROOT`.

## Example Use Case

For a course named `Venture Capital Leadership`, the agent may create:

```text
SY/Q4/Venture Capital Leadership/
  Session 5/
    files/
      resource-01-case-hardina-smythe-.pdf
      resource-01-case-hardina-smythe-.txt
    pages/
      session-page.txt
    summaries/
      session-summary.md
      resource-01-case-hardina-smythe-.summary.md
```

## Security

- Do not commit `.env`
- Do not share your Canvas token
- Do not share your Gemini or OpenAI keys
- Every user should use their own credentials
- Review the repo before pushing to GitHub to make sure no secret-bearing files are present

## Limitations

- Some PDFs extract messy text, especially scan-heavy case packets
- Some external sites block automated retrieval
- Canvas structure differs slightly by school and course design
- The agent currently runs one configured course at a time
- This is a local tool, not yet a polished GUI application

## Roadmap

- Multi-course runs from discovered Canvas course lists
- Student-friendly setup wizard instead of manual `.env` editing
- Cleaner naming across all historical outputs
- OCR support for scan-heavy PDFs
- Better external-link handling
- Desktop packaging

## Project Structure

```text
run_agent.py
requirements.txt
src/canvas_agent/
  canvas_api.py
  config.py
  extractors.py
  main.py
  pipeline.py
  scaffold.py
  summarizer.py
  utils.py
```

## Sharing With Classmates

The recommended sharing model is:

- publish the source code
- do not publish your personal `.env`
- let each classmate clone the repo
- let each classmate add their own Canvas token and Gemini key
- let each classmate choose their own save path

## Contributing

If you extend this project, keep it safe for local users:

- never hardcode credentials
- prefer local-first workflows
- document any new environment variables
- keep outputs predictable and easy to inspect

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
