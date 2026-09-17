# ─── PocketBase — Single binary SQLite database ───────────────────────────────
FROM alpine:3.20

ARG PB_VERSION=0.22.20
RUN apk add --no-cache curl ca-certificates unzip && \
    curl -fsSL "https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip" \
      -o /tmp/pb.zip && \
    unzip /tmp/pb.zip -d /pb && \
    rm /tmp/pb.zip && \
    chmod +x /pb/pocketbase

# Persistent data directory (mount a volume here)
VOLUME /pb/pb_data

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/api/health || exit 1

CMD ["/pb/pocketbase", "serve", "--http=0.0.0.0:8090", "--dir=/pb/pb_data", "--migrationsDir=/pb/pb_migrations"]

# Copy migration scripts into image
COPY pb_migrations/ /pb/pb_migrations/
