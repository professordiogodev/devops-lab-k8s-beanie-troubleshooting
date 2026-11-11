#!/usr/bin/env bash
rc=0
grep -q 'TODO' DIAGNOSIS.md && { echo "- ❌ DIAGNOSIS.md still has TODO"; rc=1; } || echo "- ✅ DIAGNOSIS.md is filled in"
grep -q '__IMAGE' fixed/*.yaml 2>/dev/null && { echo "- ❌ fixed/ still has placeholders (run ./setup.sh)"; rc=1; } || echo "- ✅ fixed/ has real manifests"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
