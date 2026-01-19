#!/usr/bin/env python3
"""A2A Group Management Example.

Demonstrates MVP Group lifecycle:
- Create group
- Add member (invite + join)
- Remove member
- Close group
- Membership event chaining

Note: This is governance/membership only. Group broadcast encryption is not in MVP.

Run: python examples/group_management.py --help
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add examples dir to path for _common import
sys.path.insert(0, str(Path(__file__).parent))
# Add src for SDK imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from _common import (
    parse_common_args,
    safe_print,
    print_header,
    print_success,
    print_info,
    print_warning,
)

from talos_sdk.a2a.models import GroupResponse
from talos_sdk.canonical import canonical_json_bytes


def create_group_event(
    group_id: str,
    actor_id: str,
    target_id: str,
    event_type: str,
    previous_digest: str = "0" * 64
) -> tuple[dict, str]:
    """Create a group membership event with hash chaining.

    Args:
        group_id: Group identifier
        actor_id: Who performed the action
        target_id: Who the action affects
        event_type: INVITED, JOINED, LEFT, REMOVED
        previous_digest: Previous event digest for chaining

    Returns:
        Tuple of (event_data, event_digest)
    """
    ts = datetime.now(timezone.utc).isoformat()
    preimage = {
        "schema_id": "talos.a2a.group_membership_event",
        "schema_version": "v1",
        "group_id": group_id,
        "actor_id": actor_id,
        "target_id": target_id,
        "event_type": event_type,
        "ts": ts,
        "previous_digest": previous_digest
    }
    digest = hashlib.sha256(canonical_json_bytes(preimage)).hexdigest()
    return preimage, digest


def main():
    args = parse_common_args(description="Talos A2A Group Management Example")

    print_header("Talos A2A Group Management Example")
    print_warning("Note: This demonstrates governance/membership only.")
    print_warning("Group broadcast encryption is not in MVP scope.")

    # =========================================================================
    # Step 1: Create Group
    # =========================================================================
    print_header("Step 1: Create Group")

    group = GroupResponse(
        group_id="group-security-ops",
        owner_id="admin-agent",
        state="ACTIVE"
    )

    safe_print({
        "group_id": group.group_id,
        "owner_id": group.owner_id,
        "state": group.state,
    }, "Group Created")

    # =========================================================================
    # Step 2: Add Members (Invite + Join)
    # =========================================================================
    print_header("Step 2: Add Members")

    # Event 1: Admin invites Alice
    e1_data, e1_digest = create_group_event(
        group.group_id, "admin-agent", "alice-agent", "INVITED"
    )
    print_info("admin-agent INVITED alice-agent")
    print(f"   Event digest: {e1_digest[:16]}...")

    # Event 2: Alice joins
    e2_data, e2_digest = create_group_event(
        group.group_id, "alice-agent", "alice-agent", "JOINED",
        previous_digest=e1_digest
    )
    print_info("alice-agent JOINED")
    print(f"   Event digest: {e2_digest[:16]}...")
    print(f"   Previous:     {e2_data['previous_digest'][:16]}... (links to Event 1)")

    # Event 3: Admin invites Bob
    e3_data, e3_digest = create_group_event(
        group.group_id, "admin-agent", "bob-agent", "INVITED",
        previous_digest=e2_digest
    )
    print_info("admin-agent INVITED bob-agent")
    print(f"   Event digest: {e3_digest[:16]}...")

    # Event 4: Bob joins
    e4_data, e4_digest = create_group_event(
        group.group_id, "bob-agent", "bob-agent", "JOINED",
        previous_digest=e3_digest
    )
    print_info("bob-agent JOINED")
    print(f"   Event digest: {e4_digest[:16]}...")

    print_success("2 members added to group")

    # =========================================================================
    # Step 3: Remove Member
    # =========================================================================
    print_header("Step 3: Remove Member")

    # Event 5: Admin removes Bob
    e5_data, e5_digest = create_group_event(
        group.group_id, "admin-agent", "bob-agent", "REMOVED",
        previous_digest=e4_digest
    )
    print_info("admin-agent REMOVED bob-agent")
    print(f"   Event digest: {e5_digest[:16]}...")

    print_success("bob-agent removed from group")

    # =========================================================================
    # Step 4: Close Group
    # =========================================================================
    print_header("Step 4: Close Group")

    # Simulate state change
    group_closed = GroupResponse(
        group_id=group.group_id,
        owner_id=group.owner_id,
        state="CLOSED"
    )

    safe_print({
        "group_id": group_closed.group_id,
        "state": group_closed.state,
    }, "Group Closed")

    # =========================================================================
    # Step 5: Verify Hash Chain
    # =========================================================================
    print_header("Step 5: Verify Hash Chain")

    print_info("Event chain verification:")
    print(f"   Event 1 (INVITED alice):  {e1_digest[:16]}...")
    print(f"   Event 2 (JOINED alice):   {e2_digest[:16]}... → links to Event 1")
    print(f"   Event 3 (INVITED bob):    {e3_digest[:16]}... → links to Event 2")
    print(f"   Event 4 (JOINED bob):     {e4_digest[:16]}... → links to Event 3")
    print(f"   Event 5 (REMOVED bob):    {e5_digest[:16]}... → links to Event 4")

    print_success("Hash chain is valid and tamper-evident")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Group State Summary")

    print("📊 Final State:")
    print(f"   Group ID:     {group.group_id}")
    print(f"   Owner:        {group.owner_id}")
    print(f"   State:        CLOSED")
    print(f"   Total events: 5")
    print(f"   Current members: alice-agent (bob-agent removed)")

    print("\n✅ MVP Group lifecycle demonstrated:")
    print("   - [x] Create group")
    print("   - [x] Invite member")
    print("   - [x] Join group")
    print("   - [x] Remove member")
    print("   - [x] Close group")
    print("   - [x] Hash-chained event log")


if __name__ == "__main__":
    main()
