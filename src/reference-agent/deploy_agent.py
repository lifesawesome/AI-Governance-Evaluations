"""
Deploy the Contoso Support Agent to Azure AI Foundry.

Usage:
    python deploy_agent.py

Requires:
    - AI_FOUNDRY_PROJECT_ENDPOINT in .env
    - TENANT_ID in .env
    - AZURE_AI_MODEL_DEPLOYMENT_NAME in .env
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import PromptAgentDefinition, FunctionTool, FunctionToolDefinition


def load_agent_config(config_path: str = None) -> dict:
    """Load agent configuration from YAML."""
    if config_path is None:
        config_path = Path(__file__).parent / "agent-config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_tool_definitions(tools: list) -> list:
    """Convert YAML tool definitions to SDK format."""
    function_defs = []
    for tool in tools:
        params = {}
        if tool.get("parameters"):
            properties = {}
            for param_name, param_def in tool["parameters"].items():
                prop = {"type": param_def.get("type", "string")}
                if "description" in param_def:
                    prop["description"] = param_def["description"]
                if "enum" in param_def:
                    prop["enum"] = param_def["enum"]
                properties[param_name] = prop
            params = {
                "type": "object",
                "properties": properties,
                "required": list(tool["parameters"].keys()),
            }

        function_defs.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": params if params else {"type": "object", "properties": {}},
            },
        })
    return function_defs


def deploy_agent():
    """Deploy or update the Contoso Support Agent."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    project_endpoint = os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]
    tenant_id = os.environ["TENANT_ID"]
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    credential = AzureCliCredential(tenant_id=tenant_id)
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)

    config = load_agent_config()
    tools = build_tool_definitions(config.get("tools", []))

    print(f"Deploying agent: {config['agent_name']}")
    print(f"Model: {model_deployment}")
    print(f"Tools: {len(tools)}")

    agent = project_client.agents.create_version(
        agent_name=config["agent_name"],
        definition=PromptAgentDefinition(
            model=model_deployment,
            instructions=config["instructions"],
            tools=tools,
        ),
    )

    print(f"\n✅ Agent deployed successfully")
    print(f"   Name: {config['agent_name']}")
    print(f"   Version: {agent.version if hasattr(agent, 'version') else 'latest'}")

    return agent


if __name__ == "__main__":
    deploy_agent()
