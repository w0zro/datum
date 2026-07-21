#!/usr/bin/env bash
# TPM entry point: set -g @plugin 'w0zro/datum'
# The actual theme is generated into ports/tmux/datum.tmux; this just loads it.
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
tmux source-file "$CURRENT_DIR/ports/tmux/datum.tmux"
