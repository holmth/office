from __future__ import annotations

import argparse
import os
import sys

DEFAULT_PROJECT_ENDPOINT = (
    "https://aoai-test-agent-framework.services.ai.azure.com/"
    "api/projects/aoai-test-agent-framework-project"
)
DEFAULT_AGENT_NAME = "office-skill-tester"
OFFICE_SKILL_TEST_INSTRUCTIONS = """
You are an Azure AI Foundry agent that validates Office document skills.
When asked to run an Office skill test, you must use any available Word and PowerPoint
skills instead of only describing what you would do. Create the requested files, make at
least one edit to each file, and then summarize what worked, what failed, and which
skills were unavailable. Never claim a file was created or edited unless the skill run
actually succeeded.
""".strip()


def resolve_project_endpoint(explicit_endpoint: str | None = None) -> str:
    return explicit_endpoint or os.environ.get("PROJECT_ENDPOINT") or DEFAULT_PROJECT_ENDPOINT


def resolve_model_deployment_name(explicit_model: str | None = None) -> str:
    model = explicit_model or os.environ.get("MODEL_DEPLOYMENT_NAME")
    if model:
        return model
    raise ValueError(
        "MODEL_DEPLOYMENT_NAME must be provided with --model or the MODEL_DEPLOYMENT_NAME environment variable."
    )


def build_office_skill_test_prompt(extra_request: str | None = None) -> str:
    sections = [
        "Run an Office skill smoke test.",
        "1. Create a Word document named office-skill-test.docx with a title, a three-item bullet list, and a 2x2 table.",
        "2. Edit the Word document by adding a short conclusion paragraph.",
        "3. Create a PowerPoint presentation named office-skill-test.pptx with a title slide, an agenda slide, and a summary slide.",
        "4. Edit the PowerPoint deck by changing one slide title and adding a short speaker note or summary update.",
        "5. Return a concise report that lists the skills you used, the files you created or edited, and any failures, permission issues, or missing skills.",
        "If Word or PowerPoint skills are unavailable, say that explicitly.",
    ]
    if extra_request:
        sections.append(f"Additional request: {extra_request}")
    return "\n".join(sections)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and optionally run an Azure AI Foundry Office skill test agent.")
    parser.add_argument("--endpoint", help="Azure AI Foundry project endpoint. Defaults to PROJECT_ENDPOINT or the repo sample endpoint.")
    parser.add_argument("--model", help="Model deployment name. Defaults to MODEL_DEPLOYMENT_NAME.")
    parser.add_argument("--name", default=DEFAULT_AGENT_NAME, help=f"Agent name. Defaults to {DEFAULT_AGENT_NAME!r}.")
    parser.add_argument("--prompt", help="Optional extra request appended to the default Office skill smoke test prompt.")
    parser.add_argument("--skip-run", action="store_true", help="Create the agent without running the Office skill smoke test.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    endpoint = resolve_project_endpoint(args.endpoint)
    model = resolve_model_deployment_name(args.model)

    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.agents.models import MessageRole
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        print(
            "Missing Azure SDK dependencies. Install azure-ai-projects, azure-ai-agents, and azure-identity first.",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 2

    project_client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    with project_client:
        agents_client = project_client.agents
        agent = agents_client.create_agent(
            model=model,
            name=args.name,
            instructions=OFFICE_SKILL_TEST_INSTRUCTIONS,
        )
        print(f"Created agent: {agent.id}")
        print(f"Agent name: {agent.name}")
        print(f"Project endpoint: {endpoint}")

        if args.skip_run:
            return 0

        thread = agents_client.threads.create()
        prompt = build_office_skill_test_prompt(args.prompt)
        agents_client.messages.create(thread_id=thread.id, role=MessageRole.USER, content=prompt)

        run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
        print(f"Run status: {run.status}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}", file=sys.stderr)
            return 1

        response_message = agents_client.messages.get_last_message_by_role(thread_id=thread.id, role=MessageRole.AGENT)
        if response_message:
            for text_message in response_message.text_messages:
                print(text_message.text.value)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
