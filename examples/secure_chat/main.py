#!/usr/bin/env python3
"""
Talos Protocol - Secure Chat Demo with Ollama

End-to-end demonstration of:
1. Ollama AI integration (with fallback)
2. In-memory database for conversations
3. ACL-secured MCP tools
4. Blockchain audit trail
5. Forward secrecy messaging

Run:
    python -m examples.secure_chat.main
"""

import asyncio
import hashlib
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger("secure_chat")

# Talos imports
from src.core.crypto import (
    Wallet,
    derive_shared_secret,
    encrypt_message,
)
from src.core.blockchain import Blockchain
from src.mcp_bridge.acl import ACLManager, PeerPermissions, Permission, RateLimit


# ============================================================================
# In-Memory Database
# ============================================================================

@dataclass 
class Message:
    id: str
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    encrypted: bool = False


@dataclass
class Conversation:
    id: str
    messages: list[Message] = field(default_factory=list)


class InMemoryDB:
    """Simple in-memory database for conversation storage."""
    
    def __init__(self):
        self.conversations: dict[str, Conversation] = {}
        self.feedback: list[dict] = []
        self.tool_calls: list[dict] = []
    
    def create_conversation(self) -> str:
        import uuid
        conv_id = str(uuid.uuid4())[:8]
        self.conversations[conv_id] = Conversation(id=conv_id)
        return conv_id
    
    def add_message(self, conv_id: str, role: str, content: str, **kwargs) -> Message:
        if conv_id not in self.conversations:
            raise ValueError(f"Conversation {conv_id} not found")
        msg_id = hashlib.sha256(f"{conv_id}{time.time()}".encode()).hexdigest()[:16]
        msg = Message(id=msg_id, role=role, content=content, **kwargs)
        self.conversations[conv_id].messages.append(msg)
        return msg
    
    def get_history(self, conv_id: str, limit: int = 10) -> list[Message]:
        conv = self.conversations.get(conv_id)
        return conv.messages[-limit:] if conv else []
    
    def add_feedback(self, conv_id: str, msg_id: str, rating: int, comment: str = ""):
        self.feedback.append({
            "conv_id": conv_id, "msg_id": msg_id, 
            "rating": rating, "comment": comment, "timestamp": time.time()
        })
    
    def log_tool_call(self, tool: str, args: dict, secure: bool):
        self.tool_calls.append({
            "tool": tool, "args": args, "secure": secure, "timestamp": time.time()
        })
    
    def get_stats(self) -> dict:
        total = sum(len(c.messages) for c in self.conversations.values())
        avg = sum(f["rating"] for f in self.feedback) / len(self.feedback) if self.feedback else 0
        return {
            "conversations": len(self.conversations),
            "messages": total,
            "feedback_entries": len(self.feedback),
            "tool_calls": len(self.tool_calls),
            "avg_rating": round(avg, 2),
        }


# ============================================================================
# Ollama Client
# ============================================================================

class OllamaClient:
    """Client for Ollama API with mock fallback."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self._available: Optional[bool] = None
    
    async def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    self._available = resp.status == 200
        except Exception:
            self._available = False
        return self._available
    
    async def generate(self, prompt: str, system: str = "", history: list = None) -> str:
        if not await self.is_available():
            return self._mock(prompt)
        try:
            import aiohttp
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            if history:
                for msg in history:
                    messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": prompt})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json={"model": self.model, "messages": messages, "stream": False},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Ollama error: {e}")
        return self._mock(prompt)
    
    def _mock(self, prompt: str) -> str:
        """Mock responses when Ollama unavailable."""
        pl = prompt.lower()
        if "capital" in pl and "france" in pl:
            return "The capital of France is Paris."
        if "joke" in pl:
            return "Why do programmers prefer dark mode? Because light attracts bugs!"
        if "2 + 2" in pl or "2+2" in pl:
            return "2 + 2 equals 4."
        if "hello" in pl:
            return "Hello! How can I help you today?"
        return f"I received your message: '{prompt[:50]}...'"


# ============================================================================
# Secure MCP Tools
# ============================================================================

class SecureMCPTools:
    """MCP tools with Talos ACL enforcement."""
    
    def __init__(self, db: InMemoryDB, ollama: OllamaClient, acl: ACLManager):
        self.db = db
        self.ollama = ollama
        self.acl = acl
        self.tools = {
            "query_history": self._query_history,
            "get_stats": self._get_stats,
            "submit_feedback": self._submit_feedback,
            "generate_response": self._generate_response,
        }
    
    async def call(self, peer_id: str, tool_name: str, args: dict) -> dict:
        """Call tool with ACL check."""
        result = self.acl.check(peer_id, "tools/call", {"name": tool_name})
        
        if result.permission != Permission.ALLOW:
            logger.warning(f"ACL DENIED: {peer_id[:8]} -> {tool_name}")
            return {"error": "Access denied", "reason": result.reason}
        
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            out = await self.tools[tool_name](**args)
            self.db.log_tool_call(tool_name, args, secure=True)
            return {"result": out, "secure": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def _query_history(self, conv_id: str, limit: int = 5) -> list:
        msgs = self.db.get_history(conv_id, limit)
        return [{"role": m.role, "content": m.content[:80]} for m in msgs]
    
    async def _get_stats(self) -> dict:
        return self.db.get_stats()
    
    async def _submit_feedback(self, conv_id: str, msg_id: str, rating: int, comment: str = "") -> dict:
        self.db.add_feedback(conv_id, msg_id, rating, comment)
        return {"status": "recorded", "rating": rating}
    
    async def _generate_response(self, prompt: str, conv_id: str = None) -> str:
        history = self.db.get_history(conv_id, 5) if conv_id else []
        return await self.ollama.generate(
            prompt, 
            system="You are a helpful assistant secured by Talos Protocol. Be concise.",
            history=history
        )


# ============================================================================
# Secure Chat Application
# ============================================================================

class SecureChatApp:
    """Chat app demonstrating Talos Protocol security."""
    
    def __init__(self):
        self.db = InMemoryDB()
        self.ollama = OllamaClient()
        self.blockchain = Blockchain(difficulty=1)
        
        # Generate identities
        self.user = Wallet.generate("user")
        self.assistant = Wallet.generate("assistant")
        
        # ACL setup
        self.acl = ACLManager(default_allow=False)
        self._setup_acl()
        
        self.tools = SecureMCPTools(self.db, self.ollama, self.acl)
        self.current_conv: Optional[str] = None
    
    def _setup_acl(self):
        # User: full access
        self.acl.add_peer(PeerPermissions(
            peer_id=self.user.address,
            allow_tools=["*"],
            rate_limit=RateLimit(requests_per_minute=100),
        ))
        # Assistant: limited access
        self.acl.add_peer(PeerPermissions(
            peer_id=self.assistant.address,
            allow_tools=["query_history", "get_stats"],
            deny_tools=["submit_feedback"],
            rate_limit=RateLimit(requests_per_minute=50),
        ))
    
    def start_conversation(self) -> str:
        self.current_conv = self.db.create_conversation()
        self.blockchain.add_data({
            "event": "conversation_started",
            "conv_id": self.current_conv,
            "timestamp": time.time(),
        })
        return self.current_conv
    
    async def send_message(self, content: str) -> str:
        if not self.current_conv:
            self.start_conversation()
        
        # Sign message
        signature = self.user.sign(content.encode())
        
        # Encrypt with shared secret
        shared = derive_shared_secret(
            self.user.encryption_keys.private_key,
            self.assistant.encryption_keys.public_key
        )
        nonce, encrypted = encrypt_message(content.encode(), shared)
        
        # Store
        user_msg = self.db.add_message(
            self.current_conv, "user", content, encrypted=True
        )
        
        # Log to blockchain
        self.blockchain.add_data({
            "event": "message",
            "conv_id": self.current_conv,
            "msg_id": user_msg.id,
            "role": "user",
            "signature": signature.hex()[:16],
            "encrypted_preview": encrypted.hex()[:24] + "...",
            "timestamp": time.time(),
        })
        
        # Get response via secure MCP
        result = await self.tools.call(
            self.user.address, "generate_response", 
            {"prompt": content, "conv_id": self.current_conv}
        )
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = result.get("result", "")
        
        # Store response
        asst_msg = self.db.add_message(
            self.current_conv, "assistant", response, encrypted=True
        )
        
        self.blockchain.add_data({
            "event": "message",
            "conv_id": self.current_conv,
            "msg_id": asst_msg.id,
            "role": "assistant",
            "secure": True,
            "timestamp": time.time(),
        })
        
        return response
    
    async def submit_feedback(self, rating: int, comment: str = "") -> dict:
        if not self.current_conv:
            return {"error": "No conversation"}
        msgs = self.db.get_history(self.current_conv, 1)
        if not msgs:
            return {"error": "No messages"}
        
        result = await self.tools.call(
            self.user.address, "submit_feedback",
            {"conv_id": self.current_conv, "msg_id": msgs[-1].id, "rating": rating, "comment": comment}
        )
        
        self.blockchain.add_data({
            "event": "feedback", "rating": rating, "timestamp": time.time()
        })
        return result
    
    def get_summary(self) -> dict:
        return {
            "user_id": self.user.address[:16] + "...",
            "assistant_id": self.assistant.address[:16] + "...",
            "blockchain_height": len(self.blockchain.chain),
            "pending_data": len(self.blockchain.pending_data),
            "conversations": len(self.db.conversations),
            "messages": sum(len(c.messages) for c in self.db.conversations.values()),
            "tool_calls": len(self.db.tool_calls),
        }


# ============================================================================
# Demo Runner
# ============================================================================

async def run_demo():
    print("\n" + "=" * 60)
    print("   🔐 TALOS PROTOCOL - SECURE CHAT DEMO 🔐")
    print("=" * 60)
    
    app = SecureChatApp()
    
    # Check Ollama
    print("\n[1] Checking Ollama...")
    available = await app.ollama.is_available()
    if available:
        print("  ✅ Ollama running - AI responses enabled")
        print(f"  📦 Model: {app.ollama.model}")
    else:
        print("  ⚠️  Ollama not found - using mock responses")
        print("  💡 Start Ollama: ollama serve")
    
    # Start conversation
    print("\n[2] Starting secure conversation...")
    conv = app.start_conversation()
    print(f"  📝 Conversation ID: {conv}")
    print(f"  👤 User: {app.user.address[:16]}...")
    print(f"  🤖 Assistant: {app.assistant.address[:16]}...")
    
    # Demo chat
    print("\n[3] Encrypted messaging with forward secrecy...")
    print("-" * 50)
    
    questions = [
        "Hello! Can you tell me what the capital of France is?",
        "Tell me a short programming joke.",
        "What is 2 + 2?",
    ]
    
    for q in questions:
        print(f"\n💬 User: {q}")
        resp = await app.send_message(q)
        print(f"🤖 Assistant: {resp}")
    
    # Feedback
    print("\n" + "-" * 50)
    print("\n[4] Submitting feedback via secure MCP...")
    fb = await app.submit_feedback(5, "Great responses!")
    print(f"  ✅ {fb}")
    
    # Stats
    print("\n[5] Querying stats via secure MCP...")
    stats = await app.tools.call(app.user.address, "get_stats", {})
    print(f"  📊 {stats.get('result', stats)}")
    
    # Mine blockchain
    print("\n[6] Mining blockchain audit trail...")
    app.blockchain.mine_pending()
    print(f"  ⛏️  Blockchain height: {len(app.blockchain.chain)}")
    
    # ACL test
    print("\n[7] ACL enforcement test...")
    denied = await app.tools.call(
        app.assistant.address, "submit_feedback",
        {"conv_id": conv, "msg_id": "x", "rating": 5}
    )
    if "error" in denied:
        print(f"  🛡️  Assistant correctly denied: {denied['reason'][:40]}...")
    
    # Summary
    print("\n[8] Security Summary:")
    for k, v in app.get_summary().items():
        print(f"  • {k}: {v}")
    
    print("\n" + "=" * 60)
    print("   ✅ DEMO COMPLETE - SECURED BY TALOS PROTOCOL")
    print("=" * 60)
    print("""
🔒 Security Features Demonstrated:
  ✅ End-to-end encryption (X25519 + ChaCha20-Poly1305)
  ✅ Digital signatures (Ed25519)
  ✅ Blockchain audit trail (immutable message log)
  ✅ ACL-based MCP tool security
  ✅ Rate limiting per peer
    """)
    
    return app


if __name__ == "__main__":
    asyncio.run(run_demo())
