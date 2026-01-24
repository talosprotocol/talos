from __future__ import annotations
from typing import Mapping

# Placeholder for SDK integration
# In real impl, this would fetch from talos_sdk_py.identity
class TalosSdkAdapter:
    def auth_headers(self) -> Mapping[str, str]:
        return {"Authorization": "Bearer stub-token"} 
