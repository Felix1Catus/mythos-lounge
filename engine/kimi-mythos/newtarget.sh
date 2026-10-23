#!/usr/bin/env bash
# MYTHOS newtarget — scaffold ~/targets/<prog>/ with the full STATE structure and templates.
# Idempotent: never overwrites an existing file (skips with a note).
#   newtarget.sh <program>
# LOCATION: ~/.kimi-code/mythos/newtarget.sh
set -uo pipefail

PROG="${1:-}"
if [[ -z "$PROG" ]]; then
    echo "usage: newtarget.sh <program>" >&2
    exit 2
fi

TROOT="$HOME/targets/$PROG"
SDIR="$TROOT/STATE"
TPL="$HOME/.kimi-code/mythos/templates"

mkdir -p "$SDIR" "$TROOT"/{scripts,notes,results,evidence,recon,reports}
chmod 700 "$TROOT/evidence" 2>/dev/null || true

for t in SCOPE.md TARGET_MODEL.md LEADS.md CHAIN_LEDGER.md RESUME.md GAP_PLAN.md DEADENDS.md; do
    if [[ -f "$SDIR/$t" ]]; then
        echo "skip (exists): $SDIR/$t"
    elif [[ -f "$TPL/$t" ]]; then
        sed "s/{PROG}/$PROG/g" "$TPL/$t" > "$SDIR/$t"
        echo "created: $SDIR/$t"
    else
        echo "warn: template missing: $TPL/$t" >&2
    fi
done

echo "dirs: $TROOT/{STATE,scripts,notes,results,evidence,recon,reports}"
echo "next: bash ~/.kimi-code/mythos/mtarget.sh $PROG  — then ground, then hunt."
