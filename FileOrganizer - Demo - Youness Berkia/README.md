# File Organizer Demo (Youness Berkia)

This folder contains a ready-to-run demo dataset for the `file-organizer` project.

## What’s inside
- `incoming/` has 10 `.docx` files
  - 5 files have deliberately ambiguous names (routing relies on AI)
  - 5 files have keyword-based names (routing uses deterministic `filename_contains` rules)
- 10 destination folders: `School/`, `Tax Returns/`, `Work/`, `Invoices/`, `Contracts/`, `Medical/`, `Banking/`, `Insurance/`, `Travel/`, `Personal/`

## Run the demo
1. Copy the profile YAML into your local profiles directory:
   - `cp "demo-youness.yaml" ~/.config/file-organizer/profiles/demo-youness.yaml`

2. (Optional) Validate the profile:
   - `file-organizer validate demo-youness`

3. Dry-run first (recommended):
   - `file-organizer run --profile demo-youness --dry-run --limit 10`
   - If your terminal is hard to read, try:
     - `file-organizer run --profile demo-youness --dry-run --limit 10 --theme dark`
     - `file-organizer run --profile demo-youness --dry-run --limit 10 --theme light`

4. Execute when you’re happy:
   - `file-organizer run --profile demo-youness --limit 10`

## Note about AI
The ambiguous files require Ollama to be installed and running locally. If Ollama isn’t available, those ambiguous files won’t be matched.

