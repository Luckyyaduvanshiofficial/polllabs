#!/bin/sh
# Writes the browser-visible origins into a small script the page loads before
# its own modules.
#
# Astro inlines PUBLIC_* at build time, so a static image built without those
# build args ships localhost origins and every request from a deployed site goes
# to the viewer's own machine. Generating the values here instead means ordinary
# runtime environment variables work, and one image can serve any environment.
#
# Runtime values win over anything baked in at build time.
set -eu

CONFIG_PATH="/usr/share/nginx/html/runtime-config.js"

# Trim a trailing slash so the values concatenate predictably.
trim() {
  printf '%s' "$1" | sed 's|/*$||'
}

API_URL="$(trim "${PUBLIC_API_URL:-}")"
SITE_URL="$(trim "${PUBLIC_SITE_URL:-}")"
PB_URL="$(trim "${PUBLIC_PB_URL:-}")"

# Escape quotes and backslashes so a stray character cannot break the script.
escape() {
  printf '%s' "$1" | sed 's|\\|\\\\|g; s|"|\\"|g'
}

cat > "$CONFIG_PATH" <<EOF
/* Generated at container start by docker-entrypoint.sh. Do not edit. */
window.__POLLS_LAB_CONFIG__ = {
  apiUrl: "$(escape "$API_URL")",
  siteUrl: "$(escape "$SITE_URL")",
  pbUrl: "$(escape "$PB_URL")"
};
EOF

echo "polls-lab: runtime config written to $CONFIG_PATH"
echo "  PUBLIC_API_URL=${API_URL:-(unset, falling back to the build-time value)}"
echo "  PUBLIC_PB_URL=${PB_URL:-(unset, falling back to the build-time value)}"
echo "  PUBLIC_SITE_URL=${SITE_URL:-(unset, page metadata uses the build-time value)}"

if [ -z "$API_URL" ] || [ -z "$PB_URL" ]; then
  echo "polls-lab: WARNING — PUBLIC_API_URL and PUBLIC_PB_URL are not both set." >&2
  echo "polls-lab: the site will use whatever was baked in at build time, which is" >&2
  echo "polls-lab: localhost unless build args were passed. Set them on this service." >&2
fi

exec "$@"
