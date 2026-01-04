# Operations Script Inventory
**Date**: Sat Jan  3 15:28:43 CST 2026
**Run ID**: 20260103_152843

| Repository | Canonical `scripts/start.sh` | Root `start.sh` | `scripts/test.sh` | Makefile Targets |
|------------|--------------------------|-----------------|-------------------|------------------|
| talos-dashboard | ✅ | ✅ | ✅ | all,install,build,test,lint,start,stop,status,clean, |
| talos-mcp-connector | ✅ | ✅ | ✅ | all,install,build,test,lint,start,stop,clean, |
| talos-gateway | ✅ | ❌ | ✅ | all,install,build,test,lint,start,stop,status,clean, |
| talos-audit-service | ✅ | ❌ | ✅ | all,install,build,test,lint,start,stop,status,clean, |
| talos-sdk-ts | ❌ | ✅ | ✅ | all,install,build,test,lint,clean,start,stop, |

## Summary
**Status**: ❌ FAILED - Missing canonical entrypoints.
