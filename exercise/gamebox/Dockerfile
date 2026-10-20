# One small image for every lite-range machine: a scored host (ssh, web, dns, mail), the blue team's jump box,
# the scoring bot and the red-team bot. Built locally by `./securax exercise lite up`; nothing is pulled at run time.
# It runs as root on purpose: sshd logs in many staff users, dnsmasq binds port 53 and smtpd port 25, and the blue team
# must be able to harden it. It only ever sits on internal-only practice networks (doc 79), never on a real network.
FROM alpine:3.20@sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
RUN apk add --no-cache openssh-server openssh-client sshpass dnsmasq opensmtpd busybox-extras sudo bash python3 tini curl bind-tools nmap \
 && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
 && echo '%wheel ALL=(ALL) ALL' > /etc/sudoers.d/wheel && chmod 0440 /etc/sudoers.d/wheel
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY svc /usr/local/bin/svc
RUN chmod 0755 /usr/local/bin/entrypoint.sh /usr/local/bin/svc
HEALTHCHECK --interval=30s --timeout=3s CMD [ "${ROLE:-host}" = tool ] || [ -f /run/range-ready ]
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/entrypoint.sh"]
