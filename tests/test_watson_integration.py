"""Integration tests for Watson Orchestrate API client and deployment.
Verifies live connectivity, IAM token acquisition, and schema validity.
"""
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from watson_orchestrate_client import WatsonOrchestrateClient
from src.orchestrator.deployer import deploy_it_navigator
from src.orchestrator.tool_registry import get_all_tool_definitions
from src.orchestrator.agent_definitions import get_agent_definitions


def test_watson_iam_authentication():
    """Verify live IAM token exchange with IBM Cloud."""
    client = WatsonOrchestrateClient()
    token = client.get_token()
    assert token is not None
    assert len(token) > 50
    assert token.startswith("ey") or len(token) > 100


def test_watson_instance_connectivity():
    """Verify listing agents on the live Orchestrate instance."""
    client = WatsonOrchestrateClient()
    agents = client.list_agents()
    assert isinstance(agents, list)
    assert len(agents) >= 1


def test_tool_registry_schemas():
    """Verify that all 12 tools conform to required Orchestrate schema structure."""
    tools = get_all_tool_definitions()
    assert len(tools) == 12
    for t in tools:
        assert "name" in t
        assert "display_name" in t
        assert "description" in t
        assert "input_schema" in t
        assert "output_schema" in t
        assert "binding" in t


def test_agent_definitions_schemas():
    """Verify that all 4 agents have valid schemas, models, and guidelines."""
    agents = get_agent_definitions()
    assert len(agents) == 4
    expected_agents = ["it_knowledge_agent", "service_request_agent", "incident_management_agent", "it_navigator_primary"]
    for ea in expected_agents:
        assert ea in agents
        adef = agents[ea]
        assert "name" in adef
        assert "llm" in adef
        assert "instructions" in adef
        assert len(adef["instructions"]) > 50


def test_deployment_dry_run():
    """Verify deployer dry-run execution without errors."""
    summary = deploy_it_navigator(dry_run=True)
    assert summary["dry_run"] is True
    assert len(summary["agents"]) == 4
    assert len(summary["tools"]) == 12
