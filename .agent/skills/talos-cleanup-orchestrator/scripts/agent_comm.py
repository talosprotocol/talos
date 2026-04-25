import json
import os
import sys

def init_state(state_file):
    if not os.path.exists(state_file):
        with open(state_file, 'w') as f:
            json.dump({
                "tasks": {},
                "messages": [],
                "shared_resources": {}
            }, f, indent=2)
        print(f"Initialized state at {state_file}")

def post_message(state_file, sender, message):
    with open(state_file, 'r') as f:
        state = json.load(f)
    state['messages'].append({"sender": sender, "content": message})
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Message from {sender} posted.")

def update_task(state_file, task_id, status, details=None):
    with open(state_file, 'r') as f:
        state = json.load(f)
    state['tasks'][task_id] = {"status": status, "details": details}
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Task {task_id} updated to {status}.")

def get_state(state_file):
    with open(state_file, 'r') as f:
        state = json.load(f)
    return state

if __name__ == "__main__":
    cmd = sys.argv[1]
    state_file = sys.argv[2]
    if cmd == "init":
        init_state(state_file)
    elif cmd == "post":
        post_message(state_file, sys.argv[3], sys.argv[4])
    elif cmd == "update":
        update_task(state_file, sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
    elif cmd == "get":
        print(json.dumps(get_state(state_file), indent=2))
