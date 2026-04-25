
files = [
    "services/ai-gateway/app/domain/interfaces.py",
    "services/ai-gateway/app/adapters/postgres/stores.py",
    "services/ai-gateway/app/api/admin/router.py",
    "services/ai-gateway/app/adapters/postgres/key_store.py",
    "tools/talos-tui/python/src/talos_tui/adapters/gateway_http.py",
    "tools/talos-tui/python/src/talos_tui/domain/models.py",
    "tools/talos-tui/python/src/talos_tui/core/coordinator.py",
    "tools/talos-tui/python/src/talos_tui/ui/screens/budgets.py"
]

for f_path in files:
    try:
        with open(f_path, "r") as f:
            content = f.read()
        new_content = content.replace('\\"', '"')
        if new_content != content:
            with open(f_path, "w") as f:
                f.write(new_content)
            print(f"Fixed {f_path}")
        else:
            print(f"No changes for {f_path}")
    except Exception as e:
        print(f"Error fixing {f_path}: {e}")
