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
RUN cd /tmp && \
    wget https://github.com/NLnetLabs/unbound/archive/refs/tags/${UNBOUND_VERSION}.tar.gz && \
    tar -xzf ${UNBOUND_VERSION}.tar.gz && \
    cd unbound-${UNBOUND_VERSION} && \
    ./configure \
        --prefix=/usr \
        --sysconfdir=/etc \
        --localstatedir=/var \
        --with-conf-file=/etc/unbound/unbound.conf \
        --with-run-dir=/var/run/unbound \
        --with-username=unbound \
        --with-ssl \
        --with-libevent && \
    make -j$(nproc) && \
    make install

FROM pihole/pihole:${PIHOLE_VERSION}

# Install runtime dependencies for Unbound and wget for root hints
RUN apk update && apk add --no-cache \
    wget \
    libevent \
    openssl \
    expat \
    libgcc \
    libstdc++

# Copy compiled Unbound binaries and tools from builder
COPY --from=builder /usr/sbin/unbound /usr/sbin/unbound
COPY --from=builder /usr/sbin/unbound-checkconf /usr/sbin/unbound-checkconf
COPY --from=builder /usr/sbin/unbound-control /usr/sbin/unbound-control
COPY --from=builder /usr/sbin/unbound-control-setup /usr/sbin/unbound-control-setup
COPY --from=builder /usr/sbin/unbound-host /usr/sbin/unbound-host
COPY --from=builder /usr/sbin/unbound-anchor /usr/sbin/unbound-anchor

# Create unbound user, group, and directories if they don't exist
RUN getent group unbound || addgroup -S unbound && \
    getent passwd unbound || adduser -S -G unbound -d /var/run/unbound -s /sbin/nologin unbound && \
    mkdir -p /var/run/unbound /etc/unbound /etc/unbound/unbound.conf.d && \
    echo 'include: "/etc/unbound/unbound.conf.d/*.conf"' > /etc/unbound/unbound.conf && \
    chown -R unbound:unbound /var/run/unbound /etc/unbound

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
