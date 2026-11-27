#!/usr/bin/env bash
# Download the three typefaces the pack is designed around, into fonts/.
# Free and openly licensed (SIL Open Font License), served by the Google Fonts
# repository. Skip this script and the pack still builds: the CSS falls back to
# Georgia, Arial and DejaVu, which look close but not identical.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p fonts

base="https://raw.githubusercontent.com/google/fonts/main/ofl"
get() { echo "fetching $2"; curl -fsSL "$1" -o "fonts/$2"; }

get "$base/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf" "SourceSerif4.ttf"
get "$base/inter/Inter%5Bopsz%2Cwght%5D.ttf" "Inter.ttf"
get "$base/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf" "JetBrainsMono.ttf"

ls -la fonts
