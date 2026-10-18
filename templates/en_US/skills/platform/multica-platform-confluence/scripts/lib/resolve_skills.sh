#!/bin/bash
# Resolve skill directories — delegates to templates/skills/_lib
_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../_lib" && pwd)"
# shellcheck source=/dev/null
source "$_LIB/resolve_skills.sh"
