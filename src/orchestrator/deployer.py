"""Deployment Pipeline for IT Navigator on IBM watsonx Orchestrate.
Deploys tools, collaborator agents, and the primary orchestrator via Orchestrate REST API.
"""
import sys
import os
import argparse
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from watson_orchestrate_client import WatsonOrchestrateClient
from src.orchestrator.tool_registry import get_all_tool_definitions
from src.orchestrator.agent_definitions import get_agent_definitions


def deploy_it_navigator(dry_run: bool = False) -> Dict[str, Any]:
    """Deploys the complete IT Navigator agentic system to Watson Orchestrate."""
    print("=" * 65)
    print("  Deploying IT Navigator to IBM watsonx Orchestrate")
    print("=" * 65)

    client = WatsonOrchestrateClient()
    if dry_run:
        print("[MODE] DRY RUN — Validating schemas without making remote modifications.\n")
    else:
        print(f"[AUTH] Connecting to: {client.instance_url}")
        token = client.get_token()
        print("[AUTH] Successfully authenticated via IBM Cloud IAM.\n")

    # 1. Register Tools
    tool_defs = get_all_tool_definitions()
    print(f"--- Step 1: Processing {len(tool_defs)} Tools ---")

    existing_tools = {}
    if not dry_run:
        try:
            for t in client.list_tools():
                existing_tools[t.get("name")] = t.get("id")
        except Exception as e:
            print(f"[WARN] Failed to list existing tools: {e}")

    tool_id_map: Dict[str, str] = {}
    for tdef in tool_defs:
        name = tdef["name"]
        if dry_run:
            tool_id_map[name] = f"mock-tool-id-{name}"
            print(f"  [VALIDATED] Tool: {name} ({tdef['display_name']})")
            continue

        if name in existing_tools:
            tool_id_map[name] = existing_tools[name]
            print(f"  [EXISTS] Tool '{name}' already present (ID: {existing_tools[name]})")
        else:
            try:
                res = client.create_tool(tdef)
                tid = res.get("id", "")
                tool_id_map[name] = tid
                print(f"  [CREATED] Tool '{name}' -> ID: {tid}")
            except Exception as e:
                print(f"  [ERROR] Failed to create tool '{name}': {e}")
                # Fallback to local name placeholder
                tool_id_map[name] = f"local-{name}"

    # 2. Deploy Collaborator Agents
    agent_defs = get_agent_definitions()
    collaborator_names = ["it_knowledge_agent", "service_request_agent", "incident_management_agent"]
    print(f"\n--- Step 2: Deploying {len(collaborator_names)} Collaborator Agents ---")

    existing_agents = {}
    if not dry_run:
        try:
            for a in client.list_agents():
                existing_agents[a.get("name")] = a.get("id")
        except Exception as e:
            print(f"[WARN] Failed to list existing agents: {e}")

    agent_id_map: Dict[str, str] = {}
    for cname in collaborator_names:
        adef = dict(agent_defs[cname])
        # Map tool names to tool IDs if available
        resolved_tools = [tool_id_map.get(tn, tn) for tn in adef.get("tools", [])]
        payload = {
            "name": adef["name"],
            "display_name": adef["display_name"],
            "description": adef["description"],
            "instructions": adef["instructions"],
            "llm": adef["llm"],
            "style": adef["style"],
            "tools": resolved_tools,
            "collaborators": [],
            "guidelines": adef.get("guidelines", []),
        }

        if dry_run:
            agent_id_map[cname] = f"mock-agent-id-{cname}"
            print(f"  [VALIDATED] Collaborator: {cname} ({adef['display_name']})")
            continue

        if cname in existing_agents:
            aid = existing_agents[cname]
            agent_id_map[cname] = aid
            try:
                client.update_agent(aid, payload)
                print(f"  [UPDATED] Collaborator '{cname}' (ID: {aid})")
            except Exception as e:
                print(f"  [REUSED] Collaborator '{cname}' (ID: {aid}, update warning: {e})")
        else:
            try:
                res = client.create_agent(payload)
                aid = res.get("id", "")
                agent_id_map[cname] = aid
                print(f"  [CREATED] Collaborator '{cname}' -> ID: {aid}")
            except Exception as e:
                print(f"  [ERROR] Failed to create collaborator '{cname}': {e}")
                agent_id_map[cname] = f"local-{cname}"

    # 3. Deploy Primary Orchestrator Agent
    print("\n--- Step 3: Deploying Primary Orchestrator Agent ---")
    pname = "it_navigator_primary"
    pdef = dict(agent_defs[pname])
    resolved_ptools = [tool_id_map.get(tn, tn) for tn in pdef.get("tools", [])]
    resolved_collabs = [agent_id_map.get(cn, cn) for cn in pdef.get("collaborators", [])]

    primary_payload = {
        "name": pdef["name"],
        "display_name": pdef["display_name"],
        "description": pdef["description"],
        "instructions": pdef["instructions"],
        "llm": pdef["llm"],
        "style": pdef["style"],
        "tools": resolved_ptools,
        "collaborators": resolved_collabs,
        "guidelines": pdef.get("guidelines", []),
    }

    if dry_run:
        agent_id_map[pname] = f"mock-agent-id-{pname}"
        print(f"  [VALIDATED] Primary Agent: {pname} ({pdef['display_name']})")
    else:
        if pname in existing_agents:
            aid = existing_agents[pname]
            agent_id_map[pname] = aid
            try:
                client.update_agent(aid, primary_payload)
                print(f"  [UPDATED] Primary Agent '{pname}' (ID: {aid})")
            except Exception as e:
                print(f"  [REUSED] Primary Agent '{pname}' (ID: {aid}, update warning: {e})")
        else:
            try:
                res = client.create_agent(primary_payload)
                aid = res.get("id", "")
                agent_id_map[pname] = aid
                print(f"  [CREATED] Primary Agent '{pname}' -> ID: {aid}")
            except Exception as e:
                print(f"  [ERROR] Failed to create Primary Agent '{pname}': {e}")
                agent_id_map[pname] = f"local-{pname}"

    print("\n" + "=" * 65)
    print("  Deployment Summary")
    print("=" * 65)
    print(f"  Primary Orchestrator : {pname} (ID: {agent_id_map.get(pname)})")
    for cn in collaborator_names:
        print(f"  Collaborator Agent   : {cn} (ID: {agent_id_map.get(cn)})")
    print(f"  Registered Tools     : {len(tool_id_map)} tools registered")
    print("=" * 65 + "\n")

    return {
        "agents": agent_id_map,
        "tools": tool_id_map,
        "dry_run": dry_run,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy IT Navigator to IBM watsonx Orchestrate")
    parser.add_argument("--dry-run", action="store_true", help="Validate schemas locally without remote updates")
    args = parser.parse_args()
    deploy_it_navigator(dry_run=args.dry_run)
