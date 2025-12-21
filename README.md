# Kompan - AI Communication Assistant

🗣️ **An AI-powered communication assistant for people with severe physical disabilities**

Kompan enables communication through simple YES/NO responses using scanning interface, Polish text-to-speech, and AI conversation management.

## ✨ Features

- **🔄 Scanning Interface**: Large YES/NO buttons with configurable timing
- **🎵 Polish TTS**: Multi-engine support (Edge TTS, Google TTS, pyttsx3)
- **🤖 AI Conversations**: Claude AI integration with offline fallbacks
- **📱 Web Interface**: Responsive design, works on any device
- **⚙️ Configurable**: Adjustable scanning speed, TTS engine selection
- **💾 Session Logging**: Conversation history for caregivers
- **🐳 Containerized**: Easy deployment with Docker

## 🚀 Quick Installation

### Prerequisites
- **Docker** installed and running
- **Windows, macOS, or Linux** system

### One-Command Installation

**Linux/macOS:**
```bash
git clone https://github.com/your-repo/kompan.git
cd kompan
./install.sh
```

**Windows:**
```cmd
git clone https://github.com/your-repo/kompan.git
cd kompan
install.bat
```

## 🎯 Usage

After installation, you'll have these commands:

### Starting Kompan
```bash
# Linux/macOS
~/kompan/start-kompan.sh

# Windows
%USERPROFILE%\kompan\start-kompan.bat
```

### Stopping Kompan
```bash
# Linux/macOS
~/kompan/stop-kompan.sh

# Windows
%USERPROFILE%\kompan\stop-kompan.bat
```

### Viewing Logs
```bash
# Linux/macOS
~/kompan/logs-kompan.sh

# Windows
%USERPROFILE%\kompan\logs-kompan.bat
```

## 📱 Interface

1. **Open your browser** to `http://localhost:8082`
2. **Click anywhere** to start a conversation
3. **Wait for scanning** to highlight YES or NO
4. **Click again** when your choice is highlighted
5. **Listen** to the AI's response and continue

### Controls
- **Pause**: Pause/resume scanning
- **Restart**: Start a new conversation
- **Settings**: Adjust scanning speed and TTS engine

## ⚙️ Configuration

Edit your settings file:
- **Linux/macOS**: `~/kompan/config/settings.json`
- **Windows**: `%USERPROFILE%\kompan\config\settings.json`

```json
{
  "scanning_interval": 2.0,         // Seconds between YES/NO highlights
  "tts_engine": "auto",             // "auto", "edge_tts", "gtts", "pyttsx3"
  "language": "pl",                 // Language (Polish)
  "claude_api_key": "",             // Your Claude API key (optional)
  "gui_port": 8082,                 // Web interface port
  "api_port": 8081                  // API port
}
```

### Adding Claude AI Support

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Edit `settings.json` and add your key to `claude_api_key`
3. Restart Kompan

**Without Claude API key**: Uses offline conversation patterns.

## 🔧 API Endpoints

For external applications:

- `GET /health` - Health check
- `GET /api/settings` - Get current settings
- `POST /api/settings` - Update settings
- `POST /api/conversation/start` - Start new conversation
- `POST /api/respond` - Send YES/NO response
- `GET /api/conversation/summary` - Get conversation summary
- `WebSocket /ws` - Real-time communication

## 📁 File Structure

```
kompan/
├── src/
│   ├── main.py              # FastAPI application
│   ├── gui/                 # Web interface (HTML/CSS/JS)
│   ├── tts/                 # Text-to-speech engines
│   ├── ai/                  # Claude AI integration
│   ├── conversation/        # Session management
│   └── api/                 # API endpoints
├── config/
│   └── settings.json        # Configuration
├── data/                    # Conversation logs
├── Dockerfile               # Container setup
├── requirements.txt         # Python dependencies
├── install.sh / install.bat # Installation scripts
└── README.md               # This file
```

## 🛠️ Development

### Local Development

```bash
# Clone repository
git clone https://github.com/your-repo/kompan.git
cd kompan

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
export PYTHONPATH=$(pwd)/src
python src/main.py
```

### Docker Development

```bash
# Build image
docker build -t kompan:latest .

# Run container with audio support
docker run -d \
  --name kompan \
  -p 8082:8082 \
  -p 8081:8081 \
  -v "$(pwd)/data":/app/data \
  -v "$(pwd)/config":/app/config \
  --device /dev/snd \
  kompan:latest

# Stop container
docker stop kompan && docker rm kompan
```

## 🔍 Troubleshooting

### Common Issues

**Docker not running**
- Ensure Docker Desktop is started
- Check with: `docker info`

**TTS not working**
- Check audio system is working
- Try different TTS engine in settings
- Linux: May need audio group permissions

**Claude API not responding**
- Verify API key in settings.json
- Check network connectivity
- Falls back to offline mode automatically

**Web interface not loading**
- Check if port 8082 is available
- Try different port in settings
- Check firewall settings

### Logs

View detailed logs:
```bash
# Application logs
docker logs kompan

# Follow live logs
docker logs -f kompan
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude AI API
- **Microsoft** for Edge TTS
- **Google** for Google TTS
- **FastAPI** community
- **Accessibility** advocates and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/kompan/issues)
- **Documentation**: This README
- **Community**: [Discussions](https://github.com/your-repo/kompan/discussions)

---

**Made with ❤️ for accessibility and inclusive communication**