#!/usr/bin/env bash
# SecuRAX installer for Linux, macOS and Windows (inside WSL). Doc 75 has the details.
#
#   curl -fsSLO https://github.com/{{REPO_SLUG}}/releases/latest/download/install.sh
#   less install.sh                  # read it first: it is short
#   bash install.sh                  # the rolling channel (main): what the nightly update follows
#   bash install.sh --stable         # the newest release tag instead
#   bash install.sh --version v0.2.0 # one exact release
#   bash install.sh --offline FILE   # no network: a release .tar.gz plus its SHA256SUMS next to it
#
# What it does: checks the tools, puts the code in ~/securax (or $SECURAX_DIR), adds the `securax` shortcut, and prints
# the next command. It never uses sudo, never starts anything and never changes an existing folder.
set -euo pipefail

say(){ printf '\033[1;36m%s\033[0m\n' "$*"; }
die(){ printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# The release pipeline writes the repository's name in here; a copy taken straight from git reads it from brand.env.
REPO="${SECURAX_REPO:-{{REPO_SLUG}}}"
case "$REPO" in *"{{"*|"")
  _here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
  REPO="$(sed -n 's/^REPO_SLUG=//p' "$_here/brand.env" 2>/dev/null | head -1)"
  [ -n "$REPO" ] || die "Which repository? Run:  SECURAX_REPO=owner/repo bash install.sh" ;;
esac
DIR="${SECURAX_DIR:-$HOME/securax}"
MODE=rolling; WANT=""; ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --stable) MODE=stable ;;
    --version) MODE=stable; WANT="${2:?--version needs a tag, e.g. v0.2.0}"; shift ;;
    --offline) MODE=offline; ARCHIVE="${2:?--offline needs the release .tar.gz}"; shift ;;
    --dir) DIR="${2:?--dir needs a folder}"; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) die "Unknown option: $1   (see: bash install.sh --help)" ;;
  esac; shift
done

# 1) The machine
OS="$(uname -s)"; WSL=""
grep -qi microsoft /proc/version 2>/dev/null && WSL=" (WSL)"
case "$OS" in Linux|Darwin) ;; *) die "This installer is for Linux, macOS or WSL. On Windows, run install.ps1 in PowerShell: it sets up WSL first." ;; esac
say "SecuRAX installer · $OS$WSL · into $DIR"
[ -e "$DIR" ] && die "$DIR already exists. To update it:  cd \"$DIR\" && ./securax update    (or pick another folder: --dir PATH)"
need(){ command -v "$1" >/dev/null 2>&1; }
need python3 || die "Python 3.10 or newer is needed. Linux: sudo apt install python3   macOS: xcode-select --install"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || die "Python 3.10 or newer is needed (found $(python3 -V 2>&1))."
[ "$MODE" = offline ] || need git || die "git is needed. Linux: sudo apt install git   macOS: xcode-select --install"
need docker || say "  ⚠ Docker is not installed yet. The CLI and the Life OS work without it; the full estate needs it (doc 75 says how)."

# 2) The code
case "$MODE" in
  rolling)
    git clone --quiet "https://github.com/$REPO.git" "$DIR" ;;
  stable)
    if [ -z "$WANT" ]; then   # the newest release: GitHub redirects /releases/latest to /releases/tag/<tag>, no API token needed
      WANT="$(curl -fsSIL -o /dev/null -w '%{url_effective}' "https://github.com/$REPO/releases/latest" | sed -n 's#.*/tag/##p')"
      [ -n "$WANT" ] || die "Could not find the newest release (no network, or no release yet). Try the rolling channel:  bash install.sh"
    fi
    git clone --quiet --branch "$WANT" "https://github.com/$REPO.git" "$DIR" ;;
  offline)
    [ -f "$ARCHIVE" ] || die "Not found: $ARCHIVE"
    SUMS="$(dirname "$ARCHIVE")/SHA256SUMS"
    [ -f "$SUMS" ] || die "SHA256SUMS must sit next to $ARCHIVE (download both from the same release)."
    if need sha256sum; then H="sha256sum"; else H="shasum -a 256"; fi
    ( cd "$(dirname "$ARCHIVE")" && grep " $(basename "$ARCHIVE")\$" SHA256SUMS | $H -c - >/dev/null ) \
      || die "Checksum mismatch: $ARCHIVE is not the file the release published. Do not use it."
    say "  ✔ checksum matches the release"
    mkdir -p "$DIR" && tar -xzf "$ARCHIVE" -C "$DIR" --strip-components=1
    say "  (an offline copy has no git history, so ./securax update cannot pull: install a newer archive the same way)" ;;
esac
chmod +x "$DIR/securax"
say "  ✔ code in $DIR ($( [ "$MODE" = rolling ] && echo "rolling: main" || echo "release ${WANT:-from archive}"))"

# 3) The shortcut, so `securax` works from any folder
"$DIR/securax" shortcut >/dev/null 2>&1 && say "  ✔ shortcut: type  securax <command>  from any folder (open a new terminal first)" || true

say ""
say "Next, one command:"
say "  cd \"$DIR\" && ./securax up"
say "It starts the estate, opens the Command Center and tells you what is left to set up (./securax finish)."
