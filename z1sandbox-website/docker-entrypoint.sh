#!/bin/sh
# Generate a config file from environment variables on container startup
# This bridges the gap between Kubernetes OS environment and the Browser JS environment.

echo "window._env_ = {" > /app/dist/env-config.js
echo "  VITE_RECAPTCHA_SITE_KEY: \"$VITE_RECAPTCHA_SITE_KEY\"," >> /app/dist/env-config.js
echo "  VITE_GOOGLE_CHAT_WEBHOOK_URL: \"$VITE_GOOGLE_CHAT_WEBHOOK_URL\"," >> /app/dist/env-config.js
echo "};" >> /app/dist/env-config.js

echo "[Startup] Generated runtime config in /app/dist/env-config.js"

# Execute the main command (CMD in Dockerfile)
exec "$@"
