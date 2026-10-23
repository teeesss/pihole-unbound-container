ARG PIHOLE_VERSION=latest
FROM pihole/pihole:${PIHOLE_VERSION} AS builder

ARG UNBOUND_VERSION=latest

# Install build dependencies for Unbound
RUN apk update && apk add --no-cache \
    build-base \
    openssl-dev \
    libevent-dev \
    expat-dev \
    wget \
    tar \
    bison \
    flex

# Download and compile Unbound from source
RUN mkdir -p /tmp/unbound-src && \
    wget -qO /tmp/unbound.tar.gz https://github.com/NLnetLabs/unbound/archive/refs/tags/${UNBOUND_VERSION}.tar.gz && \
    tar -xzf /tmp/unbound.tar.gz -C /tmp/unbound-src --strip-components=1 && \
    cd /tmp/unbound-src && \
    ./configure \
        --prefix=/usr \
        --sysconfdir=/etc \
        --localstatedir=/var \
        --with-conf-file=/etc/unbound/unbound.conf \
        --with-run-dir=/var/run/unbound \
        --with-chrootdir="" \
        --with-username=unbound \
        --with-ssl \
        --with-libevent && \
    make -j$(nproc) && \
    make install && \
    strip /usr/sbin/unbound* /usr/lib/libunbound*.so* 2>/dev/null || true

FROM pihole/pihole:${PIHOLE_VERSION}

# Install runtime dependencies for Unbound and bind-tools for DNS testing / healthcheck
RUN apk update && apk add --no-cache \
    wget \
    bind-tools \
    libevent \
    openssl \
    expat \
    libgcc \
    libstdc++

# Copy compiled Unbound binaries, shared libraries, and tools from builder
COPY --from=builder /usr/lib/libunbound* /usr/lib/
COPY --from=builder /usr/sbin/unbound /usr/sbin/unbound
COPY --from=builder /usr/sbin/unbound-checkconf /usr/sbin/unbound-checkconf
COPY --from=builder /usr/sbin/unbound-control /usr/sbin/unbound-control
COPY --from=builder /usr/sbin/unbound-control-setup /usr/sbin/unbound-control-setup
COPY --from=builder /usr/sbin/unbound-host /usr/sbin/unbound-host
COPY --from=builder /usr/sbin/unbound-anchor /usr/sbin/unbound-anchor

# Create unbound user, group, and directories if they don't exist
RUN getent group unbound || addgroup -S unbound && \
    getent passwd unbound || adduser -S -G unbound -h /var/run/unbound -s /sbin/nologin -D unbound && \
    mkdir -p /var/run/unbound /etc/unbound /etc/unbound/unbound.conf.d /var/lib/unbound && \
    echo 'include: "/etc/unbound/unbound.conf.d/*.conf"' > /etc/unbound/unbound.conf && \
    date -u +%Y > /etc/build_year && \
    chown -R unbound:unbound /var/run/unbound /etc/unbound /var/lib/unbound

# Download latest root hints for Unbound recursion with size validation
RUN wget --timeout=15 --tries=3 -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && \
    [ -s /var/lib/unbound/root.hints ] && \
    chown -R unbound:unbound /var/lib/unbound

# Copy configuration files
COPY unbound-pihole.conf /etc/unbound/unbound.conf.d/pi-hole.conf
COPY 99-edns.conf /etc/dnsmasq.d/99-edns.conf
COPY ntp-servers.conf /etc/unbound/ntp-servers.conf

# Setup directory for Unbound service
RUN mkdir -p /etc/services.d/unbound

# Pi-hole v6 does not read /etc/dnsmasq.d unless misc.etc_dnsmasq_d is on, and
# the documented compose file bind-mounts over that directory. FTL applies this
# line itself, so the EDNS cap still matches Unbound when the file is hidden.
ENV FTLCONF_misc_dnsmasq_lines=edns-packet-max=1232

# Entrypoint setup
COPY custom-entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

ENTRYPOINT ["/custom-entrypoint.sh"]
