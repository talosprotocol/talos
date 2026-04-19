import os
import sys
import hmac
import hashlib
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "services/ai-gateway"))

from app.adapters.postgres.models import Base, LlmUpstream, ModelGroup, Deployment, Team, Org, VirtualKey, Role, RoleBinding, Principal
from app.utils.id import uuid7

# Configuration
DATABASE_URL = os.getenv("DATABASE_WRITE_URL", "postgresql://talos:talos_dev_password@localhost:5433/talos")
PEPPER = os.getenv("TALOS_KEY_PEPPER", "dev-pepper")
PEPPER_ID = "p1"
AUTH_TOKEN = "test-key-hard"
ADMIN_PRINCIPAL_ID = "dev-admin"

def generate_key_hash(raw_key: str, pepper: str, pepper_id: str) -> str:
    h = hmac.new(pepper.encode(), raw_key.encode(), hashlib.sha256)
    return f"{pepper_id}:{h.hexdigest()}"

def seed():
    engine = create_engine(DATABASE_URL)
    
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Cleanup for a clean test state using CASCADE to handle foreign keys
        print("Cleaning up existing data...")
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE a2a_tasks, a2a_sessions, a2a_frames, a2a_groups, usage_events, virtual_keys, teams, orgs, role_bindings, roles, principals CASCADE;"))
            
            # Create MCP idempotency table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mcp_idempotency (
                    server_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    request_digest TEXT NOT NULL,
                    tool_effect_id TEXT,
                    tool_effect_digest TEXT,
                    tool_effect_payload JSONB,
                    PRIMARY KEY (server_id, tool_name, idempotency_key, principal_id)
                );
            """))
            conn.commit()

        # 2. Setup Org and Team (Using fixed IDs matching A2A dev auth context)
        org_id = "019da2a2-8a74-749e-b2a5-b839a84ac989"
        team_id = "019da2a2-8a74-7c16-ac38-4e85e53093b4"
        key_id = "019da2a2-8a74-712e-9698-57ce81b535b1"
        
        org = Org(id=org_id, name="Test Org")
        db.add(org)
        
        team = Team(id=team_id, org_id=org_id, name="Test Team")
        db.add(team)
        db.flush()
        print(f"✓ Created Org ({org_id}) and Team ({team_id})")

        # 3. Setup Virtual Key with full RBAC
        key_hash = generate_key_hash(AUTH_TOKEN, PEPPER, PEPPER_ID)
        
        vk = VirtualKey(
            id=key_id,
            team_id=team_id,
            key_hash=key_hash,
            scopes=["*:*", "a2a.*", "llm.*", "mcp.*"],
            allowed_model_groups=["*"],
            allowed_mcp_servers=["*"],
            revoked=False
        )
        db.add(vk)
        print(f"✓ Created VirtualKey: {AUTH_TOKEN} (ID: {key_id})")

        # 4. Setup Admin RBAC
        # Create Principal first
        admin_principal = Principal(
            id=ADMIN_PRINCIPAL_ID,
            type="user",
            display_name="Dev Admin",
            email="admin@talos.network",
            org_id=org_id
        )
        db.add(admin_principal)

        role_id = "role-admin"
        admin_role = Role(
            id=role_id,
            name="Super Admin",
            permissions=["*", "*:*"]
        )
        db.add(admin_role)
        
        admin_binding = RoleBinding(
            id=str(uuid7()),
            principal_id=ADMIN_PRINCIPAL_ID,
            role_id=role_id,
            scope_type="GLOBAL"
        )
        db.add(admin_binding)
        print(f"✓ Created Admin Role ({role_id}) and Binding for {ADMIN_PRINCIPAL_ID}")

        # 5. Setup Ollama Upstream
        ollama_id = "ollama-local"
        existing_u = db.query(LlmUpstream).filter(LlmUpstream.id == ollama_id).first()
        if not existing_u:
            upstream = LlmUpstream(
                id=ollama_id,
                provider="openai", 
                endpoint="http://localhost:11434/v1",
                credentials_ref="NONE",
                enabled=True,
                version=1
            )
            db.add(upstream)
            print(f"✓ Created Ollama upstream: {ollama_id}")

        # 4. Setup Model Group
        group_id = "ollama-group"
        existing_g = db.query(ModelGroup).filter(ModelGroup.id == group_id).first()
        if not existing_g:
            group = ModelGroup(id=group_id, name="Ollama Group", enabled=True, version=1)
            db.add(group)
            db.flush() 

            deployment = Deployment(
                id=str(uuid7()),
                model_group_id=group_id,
                upstream_id=ollama_id,
                model_name="gemma4:latest",
                weight=100
            )
            db.add(deployment)
            print(f"✓ Created Model Group {group_id} linked to Ollama")

        db.commit()
        print("\n🚀 Database seeding complete. Ready for Postman testing.")
        
    except Exception as e:
        print(f"❌ Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
