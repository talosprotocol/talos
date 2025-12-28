
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.client.client import Client, ClientConfig

@pytest.fixture
def mock_wallet():
    wallet = MagicMock()
    wallet.address = "test_address"
    wallet.name = "test_user"
    wallet.to_dict.return_value = {"name": "test_user", "address": "test_address"}
    wallet.signing_keys.public_key = b"pub_key"
    wallet.encryption_keys.public_key = b"enc_key"
    return wallet

@pytest.fixture
def client_config(tmp_path):
    return ClientConfig(data_dir=tmp_path / ".talos_test", p2p_port=9999)

@pytest.fixture
def client(client_config, mock_wallet):
    with patch("src.client.client.Wallet") as MockWallet:
        MockWallet.generate.return_value = mock_wallet
        MockWallet.from_dict.return_value = mock_wallet
        client = Client(config=client_config)
        yield client

class TestClient:
    def test_init_creates_data_dir(self, client_config):
        client = Client(config=client_config)
        assert client_config.data_dir.exists()
        assert client.wallet is None

    def test_init_wallet(self, client, mock_wallet):
        wallet = client.init_wallet("test_user")
        assert wallet == mock_wallet
        assert (client.config.data_dir / "wallet.json").exists()

    def test_init_wallet_exists_error(self, client, mock_wallet):
        client.init_wallet("test_user")
        with pytest.raises(FileExistsError):
            client.init_wallet("test_user")

    def test_load_wallet(self, client, mock_wallet):
        # First save it
        client.init_wallet("test_user")
        # Re-create client to load
        new_client = Client(config=client.config)
        loaded = new_client.load_wallet()

        assert loaded is True
        assert new_client.wallet.name == "test_user"

    def test_load_wallet_missing(self, client):
        assert client.load_wallet() is False

    @patch("src.client.client.Blockchain")
    def test_load_blockchain_default(self, MockBlockchain, client):
        loaded = client.load_blockchain()
        assert loaded is False
        assert client.blockchain is not None
        # Blockchain is now called with persistence_path and auto_save for persistence
        MockBlockchain.assert_called_with(
            difficulty=2,
            persistence_path=str(client.config.data_dir / "blockchain.json"),
            auto_save=True
        )

    @patch("src.client.client.Blockchain")
    def test_load_blockchain_exists(self, MockBlockchain, client):
        # Create dummy file
        (client.config.data_dir / "blockchain.json").write_text("{}")

        loaded = client.load_blockchain()
        assert loaded is True
        MockBlockchain.from_dict.assert_called_once()

    @patch("src.client.client.Blockchain")
    def test_save_blockchain(self, MockBlockchain, client):
        mock_chain = MagicMock()
        mock_chain.to_dict.return_value = {"blocks": []}
        MockBlockchain.from_dict.return_value = mock_chain

        # We need to set the internal blockchain since load_blockchain calls from_dict
        client.load_blockchain()
        # Manually ensure the mock is returned by load_blockchain or set it
        client._blockchain = mock_chain

        client.save_blockchain()
        assert (client.config.data_dir / "blockchain.json").exists()

    @pytest.mark.asyncio
    async def test_register_no_wallet(self, client):
        with pytest.raises(RuntimeError, match="Wallet not initialized"):
            await client.register()

    @pytest.mark.asyncio
    @patch("src.client.client.websockets.connect", new_callable=AsyncMock)
    async def test_register_success(self, mock_connect, client, mock_wallet):
        client.init_wallet("test_user")

        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # Mock protocol flow
        # 1. Receive server handshake
        # 2. Receive ack
        # 3. Receive peer list

        from src.network.protocol import ProtocolFrame, HandshakeMessage, HandshakeAck

        server_hs = HandshakeMessage(
            version=1, peer_id="registry", name="Registry",
            signing_key=b"k", encryption_key=b"k",
            capabilities=["registry"]
        )
        ack = HandshakeAck(accepted=True, peer_id="registry")
        peer_list = {"type": "peer_list", "peers": []}

        mock_ws.recv.side_effect = [
            server_hs.to_frame().to_bytes(),
            ack.to_frame().to_bytes(),
            ProtocolFrame.data(str(peer_list).replace("'", '"').encode()).to_bytes()
        ]

        success = await client.register()
        assert success is True
        mock_ws.send.assert_called()

    @pytest.mark.asyncio
    async def test_start_no_wallet(self, client):
        with pytest.raises(RuntimeError):
            await client.start()

    @pytest.mark.asyncio
    @patch("src.client.client.P2PNode")
    @patch("src.client.client.TransmissionEngine")
    async def test_start_stop(self, MockEngine, MockP2P, client, mock_wallet):
        client.init_wallet("test_user")

        mock_p2p = AsyncMock()
        MockP2P.return_value = mock_p2p

        await client.start()
        assert client.is_running
        mock_p2p.start.assert_called_once()

        await client.stop()
        assert not client.is_running
        mock_p2p.stop.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.client.client.P2PNode")
    @patch("src.client.client.TransmissionEngine")
    async def test_send_message(self, MockEngine, MockP2P, client, mock_wallet):
        client.init_wallet("test_user")

        mock_engine = AsyncMock()
        MockEngine.return_value = mock_engine

        mock_p2p = AsyncMock()
        mock_p2p.get_peer = MagicMock(return_value=MagicMock()) # get_peer is sync
        MockP2P.return_value = mock_p2p

        await client.start()

        success = await client.send_message("recipient", "hello")
        assert success is not None # engine returns something
        mock_engine.send_text.assert_called_with("recipient", "hello")

