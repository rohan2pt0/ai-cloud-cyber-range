#!/bin/sh
# Lite-range machine start-up. ROLE=host|jump starts the services listed in SERVICES; ROLE=tool runs the given command.
# /range-config (read-only) holds: users (name:password per line), index.html, dns-hosts, domain.
set -eu
if [ "${ROLE:-host}" = tool ]; then exec "$@"; fi
CFG=/range-config
while IFS=: read -r name pass; do
  [ -n "$name" ] || continue
  id "$name" >/dev/null 2>&1 || adduser -D -s /bin/bash "$name"
  echo "$name:$pass" | chpasswd >/dev/null
  [ -f "/home/$name/notes.txt" ] || echo "Work notes for $name" > "/home/$name/notes.txt"
done < "$CFG/users"
if [ -n "${ADMIN:-}" ]; then addgroup "$ADMIN" wheel 2>/dev/null || true; fi
# exercise control's green-team account: an administrator reached by key only (the rules forbid touching it)
if [ -s "$CFG/green_user" ] && [ -s "$CFG/green_key.pub" ]; then
  g=$(cat "$CFG/green_user")
  id "$g" >/dev/null 2>&1 || adduser -D -s /bin/bash "$g"
  sed -i "s/^$g:!:/$g:*:/" /etc/shadow        # no password, but not "locked": sshd refuses even key logins to locked accounts
  addgroup "$g" wheel 2>/dev/null || true
  mkdir -p "/home/$g/.ssh"; cp "$CFG/green_key.pub" "/home/$g/.ssh/authorized_keys"
  chown -R "$g:$g" "/home/$g/.ssh"; chmod 700 "/home/$g/.ssh"; chmod 600 "/home/$g/.ssh/authorized_keys"
fi
for s in $(echo "${SERVICES:-}" | tr ',' ' '); do svc start "$s"; done
echo "ready: $(hostname) services=${SERVICES:-none}"
exec sleep infinity
