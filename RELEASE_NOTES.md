# Release Notes

## v0.1.0

Initial public release of CanvasAssistant.

### Highlights

- Connects to Canvas with a personal access token
- Pulls course module items for a configured Canvas course
- Captures Canvas pages, linked files, and many external reading links
- Organizes outputs by course and session
- Generates summaries with Gemini first
- Falls back to OpenAI and then a local backup summarizer
- Saves all outputs locally for each user

### Intended Use

This release is designed for individual students running the tool locally on
their own machines with their own credentials.

### Known Limitations

- Some PDFs may extract poorly without OCR
- Some external sites may block automated retrieval
- The app currently runs one configured course at a time
- Setup is still environment-variable driven rather than wizard-based

