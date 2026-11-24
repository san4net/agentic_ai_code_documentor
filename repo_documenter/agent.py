import os
import json
from pydantic import BaseModel, Field

from google.adk import Agent, Workflow
from google.adk.workflow import START

from .tools.repository_scanner import scan_repository
from .tools.code_analyzer import analyze_repository
from .tools.readme_writer import prepare_readme_review, commit_readme


class ReadmeDraft(BaseModel):
    """Structured output expected from the documentation-writing agent."""

    repository_path: str = Field(
        description="Absolute repository root path copied exactly from the analysis input."
    )
    markdown: str = Field(description="Complete proposed README.md content in Markdown.")


MODEL = os.getenv("DOC_AGENT_MODEL", "gemini-3.5-flash-lite")


documentation_generator_agent = Agent(
    name="documentation_generator_agent",
    model=MODEL,
    description="Creates a factual proposed README.md from structured repository analysis.",
    instruction="""
You are a senior software architect and technical documentation writer.

The input is a JSON object containing repository inventory and static code analysis.
Create a clear, useful proposed README.md for the repository.

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
- Explain build/run/test only when reliable commands can be inferred from manifests.
- Do not include secrets, environment variable values, or source-code dumps.
- Output must satisfy the ReadmeDraft schema.
- Do not read, modify, or overwrite README.md. The next workflow stage handles review.
""",
    output_schema=ReadmeDraft,
    include_contents="none",
)

# Stage 1 ends with a review bundle. It does not write to the repository.
review_workflow = Workflow(
    name="repository_readme_review_workflow",
    input_schema=str,
    edges=[
        (START,
         scan_repository,
         analyze_repository,
         documentation_generator_agent,
         prepare_readme_review),
    ],
)

# Stage 2 is a separate ADK workflow. Its commit node checks the explicit
# approval flag supplied by the trusted review server before touching disk.
commit_workflow = Workflow(
    name="repository_readme_commit_workflow",
    input_schema=str,
    edges=[(START, commit_readme)],
)

# Keep this export for ADK CLI discovery. The custom review server invokes the
# two workflows separately so it can show the diff before calling commit_workflow.
root_agent = review_workflow
