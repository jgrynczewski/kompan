#!/bin/bash
set -e

echo "🚀 Kompan Installation Script"
echo "=============================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Please don't run this script as root"
   exit 1
fi

# Check system requirements
echo "🔍 Checking system requirements..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker."
    exit 1
fi

# Check for git (optional)
if ! command -v git &> /dev/null; then
    echo "⚠️  Git is not installed, but installation can continue."
fi

echo "✅ System requirements met"

# Setup directories
echo "📁 Setting up directories..."
INSTALL_DIR="$HOME/kompan"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/config"

# Copy or create config if it doesn't exist
if [ ! -f "$INSTALL_DIR/config/settings.json" ]; then
    echo "⚙️  Creating default configuration..."
    cat > "$INSTALL_DIR/config/settings.json" << 'EOF'
{
  "scanning_interval": 2.0,
  "tts_engine": "auto",
  "language": "pl",
  "api_timeout": 10,
  "conversation_history_days": 30,
  "claude_api_key": "",
  "gui_port": 8080,
  "api_port": 8081,
  "audio_device": "default"
}
EOF
fi

# Build Docker image
echo "🔨 Building Docker image..."
cd "$(dirname "$0")"
docker build -t kompan:latest .

echo "✅ Docker image built successfully"

# Create startup script
echo "📝 Creating startup script..."
cat > "$INSTALL_DIR/start-kompan.sh" << 'EOF'
#!/bin/bash

# Stop existing container if running
docker stop kompan 2>/dev/null || true
docker rm kompan 2>/dev/null || true

# Start new container
docker run -d \
  --name kompan \
  -p 8080:8080 \
  -p 8081:8081 \
  -v "$HOME/kompan/data:/app/data" \
  -v "$HOME/kompan/config:/app/config" \
  --restart unless-stopped \
  kompan:latest

echo "🚀 Kompan started successfully!"
echo "📱 Open http://localhost:8080 in your browser"
echo "🔧 API available at http://localhost:8081"

# Try to open browser automatically
if command -v xdg-open &> /dev/null; then
    sleep 3
    xdg-open http://localhost:8080 &
elif command -v open &> /dev/null; then
    sleep 3
    open http://localhost:8080 &
fi
EOF

chmod +x "$INSTALL_DIR/start-kompan.sh"

# Create stop script
cat > "$INSTALL_DIR/stop-kompan.sh" << 'EOF'
#!/bin/bash
echo "🛑 Stopping Kompan..."
docker stop kompan 2>/dev/null || echo "Kompan was not running"
docker rm kompan 2>/dev/null || true
echo "✅ Kompan stopped"
EOF

chmod +x "$INSTALL_DIR/stop-kompan.sh"

# Create logs script
cat > "$INSTALL_DIR/logs-kompan.sh" << 'EOF'
#!/bin/bash
echo "📋 Kompan logs (press Ctrl+C to exit):"
docker logs -f kompan
EOF

chmod +x "$INSTALL_DIR/logs-kompan.sh"

echo ""
echo "🎉 Kompan installation completed successfully!"
echo ""
echo "📍 Installation directory: $INSTALL_DIR"
echo "🚀 To start: $INSTALL_DIR/start-kompan.sh"
echo "🛑 To stop:  $INSTALL_DIR/stop-kompan.sh"
echo "📋 To view logs: $INSTALL_DIR/logs-kompan.sh"
echo ""
echo "⚙️  Configuration file: $INSTALL_DIR/config/settings.json"
echo "📁 Conversation data: $INSTALL_DIR/data/"
echo ""
echo "🔑 To use Claude AI features:"
echo "   1. Get an API key from https://console.anthropic.com/"
echo "   2. Edit $INSTALL_DIR/config/settings.json"
echo "   3. Set 'claude_api_key' to your API key"
echo "   4. Restart with $INSTALL_DIR/stop-kompan.sh && $INSTALL_DIR/start-kompan.sh"
echo ""
echo "🌐 Ready to start? Run: $INSTALL_DIR/start-kompan.sh"