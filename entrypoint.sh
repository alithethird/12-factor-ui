#!/bin/sh
set -e

echo "Starting snapd service..."
# Start snapd in the background
/usr/lib/snapd/snapd &

# Wait for snapd to be ready
sleep 15

# Install snaps if they're not present
if ! snap list | grep -q rockcraft; then
  echo "Installing rockcraft..."
  snap install rockcraft --classic
else
  echo "Rockcraft already installed."
fi

if ! snap list | grep -q charmcraft; then
  echo "Installing charmcraft..."
  snap install charmcraft --classic
else
  echo "Charmcraft already installed."
fi

# The PATH is already set by the Dockerfile, but this is good for scripts.
export PATH=$PATH:/snap/bin

# Execute the main command
echo "Starting server..."
if [ "$BUILD_ENV" = "development" ]; then
  # Use nodemon for development
  echo "Running in development mode (nodemon)"
  # We are in /srv/app, so this path is correct
  exec nodemon --exec "node dist/server/server.js"
else
  # Use node for production
  echo "Running in production mode"
  exec node dist/server/server.js
fi