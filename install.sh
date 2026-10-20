#!/usr/bin/env bash
# SecuRAX installer for Linux, macOS and Windows (inside WSL). Doc 75 has the details.
#
#   curl -fsSLO https://github.com/{{REPO_SLUG}}/releases/latest/download/install.sh
#   less install.sh                  # read it first: it is short
#   bash install.sh                  # the rolling channel (main): what the nightly update follows
#   bash install.sh --stable         # the newest release tag instead
#   bash install.sh --version v0.2.0 # one exact release
#   bash install.sh --offline FILE   # no network: a release .tar.gz plus its SHA256SUMS next to it
#   bash install.sh --restore BACKUP # a new or replacement machine: install, then bring back your data from a ./securax backup
#                                    #   (add --keyfile PATH for an encrypted backup)
#   sudo bash install.sh --server    # an always-on Ubuntu server (a small VPS, doc 85): Docker, a firewall that lets in SSH only,
#                                    #   security updates, swap; SecuRAX for its own user `securax`; started; then `online setup`
#
# What it does: checks the tools, puts the code in ~/securax (or $SECURAX_DIR), adds the `securax` shortcut, and prints
# the next command. It never uses sudo, never starts anything and never changes an existing folder.
# --server is the one exception: it is for a fresh server you own, it must run as root, and it says each step as it goes.
set -euo pipefail

say(){ printf '\033[1;36m%s\033[0m\n' "$*"; }
die(){ printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# The release pipeline writes the repository's name in here; a copy taken straight from git reads it from brand.env.
_TEMPLATE='{{REPO_SLUG}}'                 # one assignment of its own: inside ${VAR:-…} the braces would end the expansion early
REPO="${SECURAX_REPO:-$_TEMPLATE}"
case "$REPO" in *"{{"*|"")
  _here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
  REPO="$(sed -n 's/^REPO_SLUG=//p' "$_here/brand.env" 2>/dev/null | head -1 || true)"   # no brand.env (a lone download): ask below
  [ -n "$REPO" ] || die "Which repository? Run:  SECURAX_REPO=owner/repo bash install.sh" ;;
esac
DIR="${SECURAX_DIR:-$HOME/securax}"
MODE=rolling; WANT=""; ARCHIVE=""; RESTORE=""; KEYFILE=""; SERVER=0
while [ $# -gt 0 ]; do
  case "$1" in
    --stable) MODE=stable ;;
    --version) MODE=stable; WANT="${2:?--version needs a tag, e.g. v0.2.0}"; shift ;;
    --offline) MODE=offline; ARCHIVE="${2:?--offline needs the release .tar.gz}"; shift ;;
    --dir) DIR="${2:?--dir needs a folder}"; shift ;;
    --restore) RESTORE="${2:?--restore needs a backup file (securax-YYYYMMDD-HHMMSS.tar.gz or .gpg)}"; shift ;;
    --keyfile) KEYFILE="${2:?--keyfile needs the key file of an encrypted backup}"; shift ;;
    --server) SERVER=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) die "Unknown option: $1   (see: bash install.sh --help)" ;;
  esac; shift
done

# 0) --server: make a fresh Ubuntu server ready, then install as its own user and start (doc 85)
if [ "$SERVER" = 1 ]; then
  [ "$(id -u)" = 0 ] || die "--server sets up the machine itself, so run it as root:  sudo bash install.sh --server"
  . /etc/os-release 2>/dev/null || true
  case "${ID:-}" in ubuntu|debian) ;; *) die "--server supports Ubuntu (22.04 or 24.04) and Debian. This is ${PRETTY_NAME:-unknown}." ;; esac
  DRY="${SECURAX_SERVER_DRYRUN:-0}"                       # 1 = say every step, change nothing (the tests use it)
  run(){ if [ "$DRY" = 1 ]; then echo "  [would run] $*"; else "$@"; fi; }
  export DEBIAN_FRONTEND=noninteractive
  say "SecuRAX server setup · ${PRETTY_NAME:-Linux} · $(nproc 2>/dev/null || echo ?) CPU · $(awk '/MemTotal/{printf "%.0f GB", $2/1048576}' /proc/meminfo 2>/dev/null)"
  say "1/6 system packages and security updates"
  run apt-get update -qq
  run apt-get install -y -qq ca-certificates curl git python3 ufw unattended-upgrades openssh-client gnupg cron tzdata >/dev/null
  run dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true
  # Routines fire by this machine's clock, and a new server is on UTC: "Sunday 8pm" would come at 1:30 am in India. SECURAX_TZ changes it.
  _tz="${SECURAX_TZ:-Asia/Kolkata}"
  if [ -e "/usr/share/zoneinfo/$_tz" ]; then
    { run timedatectl set-timezone "$_tz" 2>/dev/null || run ln -sf "/usr/share/zoneinfo/$_tz" /etc/localtime; } && say "  ✔ time zone $_tz"
  else say "  ⚠ unknown time zone $_tz (e.g. Asia/Kolkata); the clock stays on $(date +%Z)"; fi
  run systemctl enable --now cron >/dev/null 2>&1 || run service cron start >/dev/null 2>&1 || true
  say "2/6 Docker, from Docker's own signed repository"
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then say "  ✔ already installed"
  else
    run install -m 0755 -d /etc/apt/keyrings
    run curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
    run chmod a+r /etc/apt/keyrings/docker.asc
    _deb="deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME:-stable} stable"
    if [ "$DRY" = 1 ]; then echo "  [would write] /etc/apt/sources.list.d/docker.list: $_deb"; else echo "$_deb" > /etc/apt/sources.list.d/docker.list; fi
    run apt-get update -qq
    # judged by the result, not apt's exit code: without systemd (a container) the package's start-up step fails though Docker is installed
    run apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null || true
    [ "$DRY" = 1 ] || { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; } \
      || die "Docker did not install. Run:  apt-get install -y docker-ce docker-compose-plugin   and read the error it prints."
    say "  ✔ $(docker --version 2>/dev/null || echo docker)"
  fi
  say "3/6 firewall: SSH in (rate-limited), nothing else (the estate is reached only through the outbound tunnel)"
  if [ "$DRY" = 1 ]; then echo "  [would run] ufw default deny incoming; ufw limit OpenSSH; ufw --force enable"
  elif ufw default deny incoming >/dev/null 2>&1 && ufw default allow outgoing >/dev/null 2>&1 && ufw limit OpenSSH >/dev/null 2>&1 && ufw --force enable >/dev/null 2>&1; then
    say "  ✔ on (more than 6 SSH attempts in 30 seconds from one address are refused)"
  else say "  ⚠ the firewall could not be switched on here (a container?). Every SecuRAX port listens on 127.0.0.1 only, so nothing is exposed either way."; fi
  # SSH is the one door left open to the internet, and many VPS images ship it accepting passwords, root included: it is then
  # guessed at all day. Keys only, and no root password login, but ONLY when a key is already installed, so this can never lock
  # you out. Checked with sshd -t before it applies; a bad file is removed again.
  _keys="$(cat /root/.ssh/authorized_keys /home/*/.ssh/authorized_keys 2>/dev/null | grep -cE '^(ssh-|ecdsa-|sk-)' || true)"
  if [ "$DRY" = 1 ]; then echo "  [would run] SSH: keys only, no root password (when a key is installed: $_keys found)"
  elif [ "${_keys:-0}" -gt 0 ] && [ -d /etc/ssh/sshd_config.d ]; then
    printf '%s\n' "# SecuRAX (install.sh --server): keys only. Remove this file to undo." "PasswordAuthentication no" \
      "KbdInteractiveAuthentication no" "PermitRootLogin prohibit-password" "MaxAuthTries 3" "X11Forwarding no" > /etc/ssh/sshd_config.d/10-securax.conf
    if sshd -t 2>/dev/null; then { systemctl reload ssh 2>/dev/null || systemctl reload sshd 2>/dev/null || service ssh reload 2>/dev/null || true; }
      say "  ✔ SSH: keys only, no root password login (your key keeps working; undo: rm /etc/ssh/sshd_config.d/10-securax.conf)"
    else rm -f /etc/ssh/sshd_config.d/10-securax.conf; say "  ⚠ SSH left as it was (its configuration did not accept the change)"; fi
  else
    _ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    say "  ⚠ SSH still accepts passwords: no SSH key is installed on this server yet. From your laptop:  ssh-copy-id root@${_ip:-$(hostname)}"
    say "    then run this installer again (it is safe to repeat) and it switches passwords off."
  fi
  say "4/6 swap, so a busy moment does not stop a service"
  if [ -n "$(swapon --show=NAME --noheadings 2>/dev/null)" ]; then say "  ✔ already there"
  elif [ "$DRY" = 1 ]; then echo "  [would run] a 4 GB /swapfile, kept across restarts"
  elif [ "$(df -Pk / | awk 'NR==2{print int($4/1048576)}')" -lt 12 ]; then say "  ⚠ skipped: less than 12 GB free on the disk (the estate needs that room more)"
  elif { fallocate -l 4G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=4096 status=none; } && chmod 600 /swapfile \
      && mkswap /swapfile >/dev/null && swapon /swapfile; then
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    say "  ✔ 4 GB"
  else rm -f /swapfile; say "  ⚠ no swap (this machine does not allow it); SecuRAX still runs"
  fi
  say "5/6 the user that runs SecuRAX (not root)"
  id securax >/dev/null 2>&1 || run useradd -m -s /bin/bash securax
  getent group docker >/dev/null 2>&1 || run groupadd docker          # normally made by Docker's package; not when its start-up step failed
  run usermod -aG docker securax
  run systemctl enable --now docker >/dev/null 2>&1 || true
  say "6/6 SecuRAX itself, as that user"
  _me="$(mktemp /tmp/securax-install.XXXXXX.sh)"; cp "${BASH_SOURCE[0]:-$0}" "$_me"; chmod 755 "$_me"
  _args=(); [ "$MODE" = stable ] && _args+=(--stable); [ -n "$WANT" ] && _args+=(--version "$WANT")
  if [ -n "$RESTORE" ]; then _r="/home/securax/$(basename "$RESTORE")"; run install -o securax -m 600 "$RESTORE" "$_r"; _args+=(--restore "$_r"); fi
  if [ -n "$KEYFILE" ]; then _k="/home/securax/$(basename "$KEYFILE")"; run install -o securax -m 600 "$KEYFILE" "$_k"; _args+=(--keyfile "$_k"); fi
  if [ "$DRY" = 1 ]; then echo "  [would run] as securax: bash install.sh ${_args[*]:-}, then ./securax up, then ./securax online setup"; rm -f "$_me"; exit 0; fi
  [ -e /home/securax/securax ] || sudo -iu securax env SECURAX_REPO="$REPO" bash "$_me" ${_args[@]+"${_args[@]}"}
  rm -f "$_me"
  [ -n "$RESTORE" ] || sudo -iu securax env SECURAX_NO_OPEN=1 bash -lc 'cd ~/securax && ./securax up' || die "The estate did not start. Run:  sudo -iu securax  then  cd ~/securax && ./securax doctor"
  # the schedules (nightly backup, code mirror, clean-ups, alerts) run from cron, as the securax user
  sudo -iu securax bash -lc 'cd ~/securax && ./securax routines install' >/dev/null 2>&1 && say "  ✔ schedules on (./securax routines list)" \
    || say "  ⚠ schedules not on yet: sudo -iu securax  then  cd ~/securax && ./securax routines install"
  say ""
  say "✔ The server is ready and SecuRAX is running (it starts again by itself after a reboot)."
  # A server's disk is copied by the provider's snapshots, and every backup holds .env with all your keys: lock the backups before
  # anything else (doc 87). It shows the key once, waits until you saved it in your password manager, then proves a backup opens.
  say "Next, about 1 minute: lock the backups (they hold every key this server uses)."
  if [ -t 0 ]; then sudo -iu securax bash -lc 'cd ~/securax && ./securax protect' || say "  ⚠ backups are not locked yet: sudo -iu securax  then  cd ~/securax && ./securax protect"
  else say "  sudo -iu securax   then   cd ~/securax && ./securax protect"; fi
  say "Last step, about 5 minutes: put it on your own addresses, behind your sign-in."
  if [ -t 0 ]; then sudo -iu securax bash -lc 'cd ~/securax && ./securax online setup' || true
  else say "  sudo -iu securax   then   cd ~/securax && ./securax online setup"; fi
  exit 0
fi

# 1) The machine
OS="$(uname -s)"; WSL=""
grep -qi microsoft /proc/version 2>/dev/null && WSL=" (WSL)"
case "$OS" in Linux|Darwin) ;; *) die "This installer is for Linux, macOS or WSL. On Windows, run install.ps1 in PowerShell: it sets up WSL first." ;; esac
say "SecuRAX installer · $OS$WSL · into $DIR"
if [ -n "$RESTORE" ]; then              # check the backup BEFORE anything is installed, so a typo costs nothing
  [ -f "$RESTORE" ] || die "Backup not found: $RESTORE"
  RESTORE="$(cd "$(dirname "$RESTORE")" && pwd)/$(basename "$RESTORE")"
  case "$RESTORE" in *.gpg) [ -n "$KEYFILE" ] && [ -f "$KEYFILE" ] || die "That backup is encrypted: add --keyfile PATH (the key file it was made with)." ;;
    *) tar tzf "$RESTORE" >/dev/null 2>&1 || die "Not a readable backup: $RESTORE" ;; esac
fi
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

if [ -n "$RESTORE" ]; then
  if need docker && docker info >/dev/null 2>&1; then
    say "Restoring your data from $(basename "$RESTORE") (it checks every file first, then starts the estate)…"
    exec "$DIR/securax" restore "$RESTORE" ${KEYFILE:+--keyfile "$KEYFILE"}
  fi
  say "  ⚠ Docker is not running, so your data cannot be restored yet. Start Docker, then run:"
  say "    cd \"$DIR\" && ./securax restore \"$RESTORE\"${KEYFILE:+ --keyfile \"$KEYFILE\"}"
  exit 0
fi
say ""
say "Next, one command:"
say "  cd \"$DIR\" && ./securax up"
say "It starts the estate, opens the Command Center and tells you what is left to set up (./securax finish)."
