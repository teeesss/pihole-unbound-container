ARG PIHOLE_VERSION=latest
FROM pihole/pihole:${PIHOLE_VERSION}

# Install Unbound and wget for root hints
RUN apk update && apk add --no-cache unbound wget

# Download latest root hints for Unbound recursion
RUN mkdir -p /var/lib/unbound && \
    wget https://www.internic.net/domain/named.root -qO- | tee /var/lib/unbound/root.hints && \
    chown unbound:unbound /var/lib/unbound/root.hints

# Copy configuration files
COPY lighttpd-external.conf /etc/lighttpd/external.conf 
COPY unbound-pihole.conf /etc/unbound/unbound.conf.d/pi-hole.conf
COPY 99-edns.conf /etc/dnsmasq.d/99-edns.conf

# Setup directory for Unbound service
RUN mkdir -p /etc/services.d/unbound

# Entrypoint setup
COPY custom-entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

ENTRYPOINT ["/custom-entrypoint.sh"]
