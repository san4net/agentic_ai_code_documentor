import os
from pydantic import BaseModel, Field

from google.adk import Agent, Workflow

from .tools.repository_scanner import scan_repository
from .tools.code_analyzer import analyze_repository
from .tools.readme_writer import write_readme


class ReadmeDraft(BaseModel):
    """Structured output expected from the documentation-writing agent. """

    repository_path: str = Field(
        description="Absolute repository root path copied exactly from the analysis input."
    )
    markdown: str = Field(
        description="Complete README.md content in Markdown."
    )


MODEL = os.getenv("DOC_AGENT_MODEL", "gemini-3.5-flash")

documentation_generator_agent = Agent(
    name="documentation_generator_agent",
    model=MODEL,
    description="Creates a factual README.md from structured repository analysis.",
    instruction="""
You are a senior software architect and technical documentation writer.

The input is a JSON object containing repository inventory and static code analysis.
Create a clear, useful README.md for the repository.

Rules:
- Use repository_name as the top-level Markdown title.
- Copy root_path exactly into repository_path.
- Use only facts supported by the supplied analysis.
- Do not invent runtime behavior, endpoints, architecture, deployment steps,
  configuration keys, or commands that are not supported by the input.
- If information is unavailable, say "Not identified from static analysis".
- Explain the primary language and any additional languages detected.
- Include the directory layout, important modules, classes/functions,
  dependencies/framework indicators, and entry points where available.
- Explain how to build/run/test only when reliable commands can be inferred
  from project manifests or conventional project metadata. Label inferred
  commands as suggestions.
- Keep the document concise enough to be useful, but cover the major components.
- Do not include secrets, environment variable values, or source-code dumps.
- Output must satisfy the ReadmeDraft schema.
""",
    output_schema=ReadmeDraft,
    include_contents="none",
)

# Current ADK graph-based workflow: each node receives the previous node's output.
# START receives the user's repository path as a string.
root_agent = Workflow(
    name="repository_documentation_workflow",
    input_schema=str,
    edges=[
        (
            "START",
            scan_repository,
            analyze_repository,
            documentation_generator_agent,
            write_readme,
        )
    ],
)
