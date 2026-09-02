# office

Test office agent skills.

## Included skills

- `office-documents`: lets the agent process `.docx` and `.pptx` files by
  extracting their content to Markdown first and then following the user's
  instruction for the document.

## Create an Office skill test agent

The repository includes `/home/runner/work/office/office/office_skill_test_agent.py`, a small sample that:

- creates an Azure AI Foundry agent against the provided project endpoint
- gives the agent instructions to use available Word and PowerPoint skills
- optionally runs a smoke test that asks the agent to create and edit both document types

### Prerequisites

Install the Azure SDK packages used by the sample:

```bash
pip install azure-ai-projects azure-ai-agents azure-identity
```

Set the model deployment to use:

```bash
export MODEL_DEPLOYMENT_NAME=<your-model-deployment-name>
```

The sample already defaults `PROJECT_ENDPOINT` to:

```text
https://aoai-test-agent-framework.services.ai.azure.com/api/projects/aoai-test-agent-framework-project
```

Override it only if you want to point at a different Foundry project:

```bash
export PROJECT_ENDPOINT=<another-project-endpoint>
```

### Usage

Create the agent and immediately run the Office skill smoke test:

```bash
python office_skill_test_agent.py
```

Create the agent without running the smoke test:

```bash
python office_skill_test_agent.py --skip-run
```

If the configured agent does not have Word or PowerPoint skills available, the run should report that clearly instead of pretending the actions succeeded.

