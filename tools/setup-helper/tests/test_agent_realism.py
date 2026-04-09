import pytest
from pathlib import Path
from talos_setup_helper.agent import Agent
from talos_setup_helper.executor import RecipeExecutor
from unittest.mock import MagicMock, patch

def test_recipe_executor_sdk_init_python(tmp_path):
    executor = RecipeExecutor(tmp_path)
    args = {"project_name": "test-project", "language": "python"}
    
    executor.execute("talos-sdk-init", args)
    
    assert (tmp_path / "test-project").is_dir()
    assert (tmp_path / "test-project" / "pyproject.toml").exists()
    assert (tmp_path / "test-project" / "test_project" / "__init__.py").exists()

def test_recipe_executor_sdk_init_typescript(tmp_path):
    executor = RecipeExecutor(tmp_path)
    args = {"project_name": "test-ts", "language": "typescript"}
    
    executor.execute("talos-sdk-init", args)
    
    assert (tmp_path / "test-ts").is_dir()
    assert (tmp_path / "test-ts" / "package.json").exists()
    assert (tmp_path / "test-ts" / "src" / "index.ts").exists()

@patch("requests.post")
def test_agent_execute_job_realism(mock_post, tmp_path):
    # Setup mock auth
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    agent = Agent(config_dir)
    agent.auth._identity = {
        "agent_id": "agent-123",
        "agent_secret": "secret-456",
        "dashboard_url": "http://dashboard"
    }
    
    job = {
        "job_id": "job-789",
        "recipe_id": "talos-sdk-init",
        "args": {"project_name": "real-project", "language": "python"}
    }
    
    agent._execute_job(job)
    
    # Verify events were sent
    assert mock_post.call_count >= 2 # started, completed
    
    # Verify workspace effect
    job_dir = config_dir / "workspace" / "job-789"
    assert (job_dir / "real-project").is_dir()

@patch("requests.post")
def test_agent_poll_credential_rotation(mock_post, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    agent = Agent(config_dir)
    agent.auth._save_identity("agent-123", "old-secret", "http://dashboard")
    
    # Mock response with new secret
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "agent_secret": "new-secret",
        "job": None
    }
    
    agent._poll()
    
    # Verify local identity updated
    assert agent.auth._identity["agent_secret"] == "new-secret"
    
    # Verify next call would use new secret
    headers = agent.auth.get_headers()
    assert headers["Authorization"] == "Bearer new-secret"
