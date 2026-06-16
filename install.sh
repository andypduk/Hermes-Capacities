#!/usr/bin/env bash
# install.sh — Capacities MCP Server installer for Hermes Agent
set -e

REPO="andydennis/hermes-capacities"
INSTALL_DIR="${HERMES_HOME:-$HOME/.hermes}/mcp-servers/capacities"

echo "📦 Installing Capacities MCP Server..."

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download server
echo "⬇️  Downloading from github.com/$REPO..."
curl -sL "https://raw.githubusercontent.com/$REPO/main/server.py" -o "$INSTALL_DIR/server.py"
chmod +x "$INSTALL_DIR/server.py"

echo ""
echo "✅ Installed to $INSTALL_DIR/server.py"
echo ""
echo "Next steps:"
echo "  1. Get your API token from Capacities desktop app:"
echo "     Settings > Capacities API > Generate Token"
echo ""
echo "  2. Configure Hermes:"
echo "     hermes mcp add capacities \\"
echo "       --command python3 \\"
echo "       --args $INSTALL_DIR/server.py \\"
echo "       --env CAPACITIES_API_TOKEN=<your_...echo ""
echo "  Or add to your MCP client config directly."
echo ""
echo "  3. Test:"
echo "     hermes mcp test capacities"
