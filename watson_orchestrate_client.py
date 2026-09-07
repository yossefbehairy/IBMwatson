"""IBM watsonx Orchestrate API Client
Handles authentication via IBM Cloud IAM and exposes methods to interact with
Watson Orchestrate agents, tools, skills, flows, and runs.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional

# Path to config.json if present in the same directory
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config() -> Dict[str, str]:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


_cfg = load_config()

DEFAULT_API_KEY = os.getenv(
    "WATSON_ORCHESTRATE_API_KEY",
    _cfg.get("api_key", ""),
)
DEFAULT_INSTANCE_URL = os.getenv(
    "WATSON_ORCHESTRATE_URL",
    _cfg.get(
        "instance_url",
        "https://api.eu-gb.watson-orchestrate.cloud.ibm.com/instances/44e00af6-23d2-4ec1-b06f-506d97dd2083",
    ),
)
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class WatsonOrchestrateClient:
    def __init__(
        self,
        api_key: str = DEFAULT_API_KEY,
        instance_url: str = DEFAULT_INSTANCE_URL,
    ):
        self.api_key = api_key
        self.instance_url = instance_url.rstrip("/")
        self._token: Optional[str] = None

    def get_token(self, force_refresh: bool = False) -> str:
        """Exchange IBM Cloud API key for an IAM Bearer token."""
        if self._token and not force_refresh:
            return self._token

        data = urllib.parse.urlencode(
            {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            IAM_TOKEN_URL,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            self._token = body["access_token"]
            return self._token

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        import requests

        token = self.get_token()
        url = f"{self.instance_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data is not None else None,
                timeout=30,
            )
            if resp.status_code == 204 or not resp.content:
                return {}
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code} on {method} {url}: {resp.text}")
            return resp.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed on {method} {url}: {e}")

    # ==================== Agents ====================

    def list_agents(self) -> List[Dict[str, Any]]:
        """List configured agents in the instance."""
        res = self._request("/v1/orchestrate/agents")
        return res if isinstance(res, list) else res.get("data", [])

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get details for a specific agent."""
        return self._request(f"/v1/orchestrate/agents/{agent_id}")

    def create_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent in the instance."""
        return self._request("/v1/orchestrate/agents", method="POST", data=payload)

    def update_agent(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        return self._request(
            f"/v1/orchestrate/agents/{agent_id}", method="PUT", data=payload
        )

    def patch_agent(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Patch an existing agent (partial update)."""
        return self._request(
            f"/v1/orchestrate/agents/{agent_id}", method="PATCH", data=payload
        )

    def delete_agent(self, agent_id: str) -> Any:
        """Delete an agent by ID."""
        return self._request(f"/v1/orchestrate/agents/{agent_id}", method="DELETE")

    # ==================== Tools ====================

    def list_tools(self) -> List[Dict[str, Any]]:
        """List configured tools."""
        res = self._request("/v1/orchestrate/tools")
        return res if isinstance(res, list) else res.get("data", [])

    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """Get tool specification by ID."""
        return self._request(f"/v1/orchestrate/tools/{tool_id}")

    def create_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new tool."""
        return self._request("/v1/orchestrate/tools", method="POST", data=payload)

    def delete_tool(self, tool_id: str) -> Any:
        """Delete a tool by ID."""
        return self._request(f"/v1/orchestrate/tools/{tool_id}", method="DELETE")

    # ==================== Skills & Flows ====================

    def list_skills(self) -> List[Dict[str, Any]]:
        """List configured skills."""
        res = self._request("/v1/orchestrate/skills")
        return res if isinstance(res, list) else res.get("data", [])

    def list_flows(self) -> List[Dict[str, Any]]:
        """List configured flows."""
        res = self._request("/v1/orchestrate/flows")
        return res if isinstance(res, list) else res.get("data", [])

    # ==================== Runs & Execution ====================

    def list_runs(self) -> Dict[str, Any]:
        """List orchestrate execution runs."""
        return self._request("/v1/orchestrate/runs")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get status of an execution run."""
        return self._request(f"/v1/orchestrate/runs/{run_id}")

    def create_run(
        self,
        agent_id: str,
        message_content: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate or continue a conversation with an agent."""
        payload: Dict[str, Any] = {
            "agent_id": agent_id,
            "message": {
                "role": "user",
                "content": message_content,
            },
        }
        if thread_id:
            payload["thread_id"] = thread_id
        return self._request("/v1/orchestrate/runs", method="POST", data=payload)


if __name__ == "__main__":
    client = WatsonOrchestrateClient()
    print("Connecting to IBM Watson Orchestrate...")
    try:
        agents = client.list_agents()
        print(f"Success! Found {len(agents)} agents:")
        for a in agents:
            name = a.get("name", "Unnamed")
            aid = a.get("id", "")
            desc = (a.get("description") or "")[:70]
            print(f" - [{aid}] {name}: {desc}...")
    except Exception as e:
        print(f"Connection failed: {e}")
