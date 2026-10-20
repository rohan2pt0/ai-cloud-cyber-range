# One small image for every lite-range machine: a scored host (ssh, web, dns, mail), the blue team's jump box,
# the scoring bot and the red-team bot. Built locally by `./securax exercise lite up`; nothing is pulled at run time.
FROM alpine:3.20@sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
RUN apk add --no-cache openssh-server openssh-client sshpass dnsmasq opensmtpd busybox-extras sudo bash python3 tini curl bind-tools nmap \
 && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
 && echo '%wheel ALL=(ALL) ALL' > /etc/sudoers.d/wheel && chmod 0440 /etc/sudoers.d/wheel
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY svc /usr/local/bin/svc
RUN chmod 0755 /usr/local/bin/entrypoint.sh /usr/local/bin/svc
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/entrypoint.sh"]
