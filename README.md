# Repository Documenter (Google ADK)

A local repository documentation workflow built with Google ADK, Python AST,
and Tree-sitter. It scans Python, Java and JavaScript repositories and writes
a `README.md` into the scanned repository root.

## Pipeline

1. **Repository scanner** — inventories source files and project manifests.
2. **Language detector and parser** — identifies language counts and extracts
   classes, methods, functions and imports.
3. **Documentation generator** — uses a Gemini agent to write a factual README.
4. **README writer** — writes the generated Markdown to the repository root.

The first two stages are deterministic Python workflow nodes. The final
documentation stage is an LLM agent. This keeps filesystem access and parsing
predictable while using the model for explanation and synthesis.

## Supported source files

- Python: `.py` (Python standard-library `ast`)
- Java: `.java` (Tree-sitter)
- JavaScript: `.js`, `.jsx`, `.mjs`, `.cjs` (Tree-sitter)

Mixed-language repositories are supported. The primary language is the language
with the largest number of supported source files.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env` to `.env` inside the `repo_documenter/` directory and set
`GOOGLE_API_KEY`. The ADK loader reads the `.env` beside `agent.py`.

For Google AI Studio:

```dotenv
GOOGLE_GENAI_USE_ENTERPRISE=FALSE
GOOGLE_API_KEY=your-key
DOC_AGENT_MODEL=gemini-3.5-flash
```

## Run with ADK Web

From the directory containing `repo_documenter/`:

```bash
adk web
```

Open the local ADK Web page, select `repo_documenter`, and enter the absolute
path to a local repository, for example:

```text
/Users/your-user/Projects/payment-service
```

The generated file will be:

```text
/Users/your-user/Projects/payment-service/README.md
```

## Run from the terminal

```bash
adk run repo_documenter
```

Enter the repository path when prompted.

## Safety and limitations

- Repository code is parsed but never executed.
- Symlinks and common generated/vendor directories are skipped.
- Binary, oversized and unreadable files are skipped.
- The scanner inventories up to 5,000 supported source files.
- Individual source files larger than 500 KB are skipped.
- Existing `README.md` is backed up to `README.md.bak` before replacement.
- Java and JavaScript parsing is structural; this starter does not perform
  full type resolution, dependency graph construction, or semantic execution.
- Framework indicators come from dependency manifests and are not proof that
  a framework is active in runtime code.
- The generated README is based on static analysis. Review commands and
  architecture descriptions before using them as operational documentation.

## Extending

Add another parser in `tools/code_analyzer.py`, register its extension and
language in `SUPPORTED_EXTENSIONS`, and add parser-specific extraction logic.
