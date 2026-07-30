# ==============================================================================
# Open WebUI — Custom Themed Image
# Extends the official image with custom CSS injected at build time.
# ==============================================================================
# Pin a version tag (not :main) in production to prevent upstream CSS breakage.
# Check releases: https://github.com/open-webui/open-webui/releases
# ==============================================================================

FROM ghcr.io/open-webui/open-webui:main

# Inject custom CSS — Open WebUI's SPA loads /app/build/static/custom.css
COPY custom.css /app/build/static/custom.css
