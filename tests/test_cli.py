
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from src.client.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_client_cls():
    with patch("src.client.cli.Client") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance
        yield MockClient

class TestCLI:
    def test_cli_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Talos Protocol - Secure P2P MCP Tunneling" in result.output

    @patch("src.client.cli.Client")
    def test_init_command(self, MockClient, runner):
        # Setup mock to simulate non-existent wallet initially
        mock_instance = MockClient.return_value
        mock_instance.wallet_path = MagicMock()
        mock_instance.wallet_path.exists.return_value = False
        
        mock_instance.init_wallet.return_value = MagicMock(address="test_addr", name="test_user")
        
        result = runner.invoke(cli, ["init", "--name", "test_user"])
        assert result.exit_code == 0
        assert "Wallet created successfully" in result.output

    def test_status_command(self, runner, mock_client_cls):
        wallet = MagicMock()
        wallet.name = "test_user"
        wallet.address = "test_addr"
        
        client = mock_client_cls.return_value
        client.load_wallet.return_value = True
        client.wallet = wallet
        
        chain = MagicMock()
        chain.__len__.return_value = 10
        client.blockchain = chain
        
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Name:       test_user" in result.output
        assert "Blockchain: 10 blocks" in result.output

    def test_status_no_wallet(self, runner, mock_client_cls):
        client = mock_client_cls.return_value
        client.load_wallet.return_value = False
        
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Not initialized" in result.output
