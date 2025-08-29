# Image Canvas Workspace with AI Style Analysis

A collaborative image canvas application that leverages AI to analyze image styles and integrates with external APIs like Freepik to generate similar images. Built with TypeScript frontend and FastAPI backend powered by Daft dataframes and machine learning models.

![Project Architecture](https://img.shields.io/badge/Architecture-Canvas%20%2B%20AI%20Analysis-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Daft-green)
![Frontend](https://img.shields.io/badge/Frontend-TypeScript%20%2B%20Canvas-orange)
![AI](https://img.shields.io/badge/AI-OpenAI%20%2B%20Moondream-purple)

## 🚀 Overview

This project creates a collaborative workspace where users can:

1. **Upload and organize images** on an infinite canvas with drag-and-drop functionality
2. **Analyze image styles** using AI models (OpenAI GPT-4 Vision or local Moondream)
3. **Extract dominant colors and artistic elements** from images
4. **Generate similar images** through external API integrations (Freepik, etc.)
5. **Collaborate in real-time** with other users via WebSocket connections
6. **Group and manipulate images** with an intuitive canvas interface

## 🏗️ Architecture

### Backend (`/backend/`)
- **FastAPI** server with WebSocket support for real-time collaboration
- **Daft** dataframes for efficient image data processing and storage
- **AI Integration** with OpenAI GPT-4 Vision API and local Moondream model
- **Style Analysis Pipeline** using UDFs (User Defined Functions) for image processing
- **RESTful API** for canvas state management and image operations

### Frontend (`/image-canvas/`)
- **TypeScript** application with HTML5 Canvas for image manipulation
- **Responsive UI** with toolbar, canvas, and chat interface
- **Real-time collaboration** via WebSocket connections
- **Image handling** with drag-and-drop, file upload, and URL input
- **Canvas operations** including zoom, pan, select, group/ungroup images

## 📋 Features

### 🖼️ Image Management
- **Multiple upload methods**: File selection, drag & drop, URL input, paste from clipboard
- **Canvas manipulation**: Drag, zoom (Ctrl+scroll), pan (Space+drag), marquee selection
- **Image grouping**: Group related images together with visual indicators
- **Real-time sync**: Changes are instantly shared across all connected clients

### 🤖 AI-Powered Style Analysis
- **Intelligent style detection** using computer vision and LLMs
- **Color palette extraction** with dominant color identification
- **Artistic element recognition** (abstract, realistic, impressionist, etc.)
- **Detailed style descriptions** for each uploaded image
- **Integration ready** for external APIs like Freepik to generate similar images

### 👥 Collaboration Features
- **Multi-user canvas** with real-time updates
- **Chat system** for communication between collaborators
- **User presence indicators** showing when users join/leave
- **Synchronized selections** and operations across clients

### 🎨 Canvas Interface
- **Infinite canvas** with smooth zooming and panning
- **Selection tools**: Click to select, Shift+click for multi-select, marquee selection
- **Visual feedback**: Selection highlights, group indicators, hover effects
- **Keyboard shortcuts**: Delete selected images, space for pan mode

## 🛠️ Setup Instructions

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Virtual environment** (recommended)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend/
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv ../venv
   source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp env.config .env
   # Edit .env file with your API keys:
   # - HF_TOKEN: HuggingFace token for Moondream model
   # - OPENAI_API_KEY: OpenAI API key (optional, will use local model if not provided)
   ```

5. **Run setup script (optional):**
   ```bash
   python setup.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd image-canvas/
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

### Environment Configuration

The backend supports multiple AI models with fallback options:

- **Primary**: OpenAI GPT-4 Vision (requires `OPENAI_API_KEY`)
- **Fallback**: Local Moondream model (requires `HF_TOKEN`)
- **Optimization**: Configure warmup and compilation via environment variables [[memory:6136603]]

Available environment variables:
```bash
# AI Model Configuration
OPENAI_API_KEY=your_openai_key_here
HF_TOKEN=your_huggingface_token_here

# Performance Optimization
FLUX_COMPILE_MODE=enabled|disabled
FLUX_WARMUP_STEPS=10
FAL_SKIP_WARMUP=true|false

# Offline Mode (uses preloaded caches only)
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
DIFFUSERS_OFFLINE=1

# Server Configuration
PORT=8001
HOST=0.0.0.0
DAFT_PROGRESS_BAR=0
```

## 🚀 Quick Start

### Using the Makefile

```bash
# Start both backend and frontend
make start

# Start only backend
make start-backend

# Start only frontend
make start-frontend

# Install all dependencies
make install

# Clean up processes
make clean
```

### Manual Start

**Backend:**
```bash
cd backend/
source ../venv/bin/activate
python start.py
# Server runs on http://localhost:8001
```

**Frontend:**
```bash
cd image-canvas/
npm run dev
# Frontend runs on http://localhost:5173
```

## 📡 API Documentation

### Canvas Management
- `POST /api/cs` - Create new canvas
- `GET /api/canvas/{canvas_id}` - Get canvas state
- `PUT /api/canvas/{canvas_id}` - Update canvas state

### Image Operations
- `POST /api/upload` - Upload image file
- `POST /api/analyze-image` - Upload image for AI analysis
- `POST /api/analyze-styles` - Trigger style analysis for images
- `GET /api/canvas/{canvas_id}/analyzed-images` - Get analysis results

### Real-time Communication
- `WebSocket /ws/{canvas_id}` - Real-time collaboration
- `POST /api/canvas/{canvas_id}/messages` - Send chat message

### System Endpoints
- `GET /health` - Health check with system status
- `GET /debug/daft-summary` - Daft DataFrame statistics
- `POST /debug/simple-test` - Connection test

## 🔌 API Integration Guide

### Integrating with External APIs (e.g., Freepik)

The system provides style analysis data that can be used with external APIs:

```javascript
// Example: Using style analysis results with Freepik API
const styleAnalysis = await fetch('/api/canvas/canvas_id/analyzed-images')
  .then(r => r.json());

const imageStyle = styleAnalysis.images[0];
const searchQuery = {
  style: imageStyle.style_description,
  colors: imageStyle.dominant_colors,
  elements: imageStyle.artistic_elements
};

// Use with Freepik API or similar services
const similarImages = await freepikAPI.search(searchQuery);
```

## 🎨 Usage Guide

### Basic Operations
1. **Add images**: Drag files onto canvas, use toolbar buttons, or paste URLs
2. **Navigate**: Scroll to zoom, Ctrl+scroll to zoom at cursor, Space+drag to pan
3. **Select images**: Click to select, Shift+click for multi-select, drag for marquee
4. **Group images**: Select multiple images and click "Group Selected"
5. **Analyze styles**: Images are automatically sent for AI analysis upon upload

### Collaboration
1. **Share canvas**: Share the canvas URL with collaborators
2. **Real-time updates**: See changes from other users instantly
3. **Chat**: Use the chat bar for communication
4. **Style insights**: View AI-generated style analysis in the chat

### Keyboard Shortcuts
- `Space + Drag`: Pan canvas
- `Ctrl/Cmd + Scroll`: Zoom at cursor position
- `Shift + Click`: Add/remove from selection
- `Delete/Backspace`: Delete selected images
- `Ctrl/Cmd + V`: Paste image URL from clipboard

## 🧠 AI Style Analysis

The system uses advanced AI models to analyze images and extract:

- **Style characteristics**: Artistic movement, technique, composition
- **Color palette**: Dominant colors with hex codes
- **Visual elements**: Abstract, realistic, geometric, organic features
- **Mood and atmosphere**: Emotional tone and artistic intent

### Supported Models

1. **OpenAI GPT-4 Vision**
   - High accuracy style analysis
   - Detailed natural language descriptions
   - Requires API key and internet connection

2. **Local Moondream Model**
   - Privacy-focused local processing
   - Good performance for style detection
   - Requires HuggingFace token for download

## 🔧 Development

### Project Structure
```
daft_daytona_hackathon/
├── backend/                 # FastAPI server
│   ├── main.py             # Main application with AI integration
│   ├── start.py            # Server startup script
│   ├── setup.py            # Environment setup
│   ├── requirements.txt    # Python dependencies
│   └── env.config          # Environment template
├── image-canvas/           # TypeScript frontend
│   ├── src/
│   │   ├── main.ts         # Application entry point
│   │   ├── canvas.ts       # Canvas manipulation logic
│   │   ├── api.ts          # Backend API client
│   │   ├── types.ts        # TypeScript definitions
│   │   └── style.css       # Application styles
│   ├── index.html          # HTML template
│   └── package.json        # Node.js dependencies
└── venv/                   # Python virtual environment
```

### Key Technologies
- **Backend**: FastAPI, Daft, PyTorch, Transformers, OpenAI
- **Frontend**: TypeScript, HTML5 Canvas, WebSocket API
- **AI/ML**: Computer Vision, Large Language Models, Image Processing
- **Data**: Daft dataframes for efficient image data management

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Follow code style**: Use TypeScript for frontend, Python type hints for backend
4. **Test thoroughly**: Ensure both AI models work correctly
5. **Submit pull request**: Include description of changes and AI model compatibility

## 📜 License

This project is part of the Daft Daytona Hackathon and demonstrates the power of combining canvas-based UIs with AI-powered data analysis using Daft dataframes.

## 🆘 Troubleshooting

### Common Issues

**Backend fails to start:**
- Check Python version (3.8+ required)
- Verify virtual environment activation
- Install missing dependencies: `pip install -r requirements.txt`

**AI analysis not working:**
- Verify API keys in `.env` file
- Check HuggingFace token for Moondream access
- Ensure internet connection for OpenAI API

**Frontend not loading:**
- Check Node.js version (16+ required)
- Run `npm install` in image-canvas directory
- Verify backend is running on port 8001

**WebSocket connection issues:**
- Check firewall settings
- Verify backend WebSocket endpoint is accessible
- Try refreshing the browser page

### Performance Optimization

For faster startup times [[memory:6136603]]:
```bash
# Configure compilation mode
export FLUX_COMPILE_MODE=disabled
export FLUX_WARMUP_STEPS=5
export FAL_SKIP_WARMUP=true

# Enable offline mode to use cached models
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export DIFFUSERS_OFFLINE=1
```

## 📞 Support

For technical support or questions about the AI style analysis features, please check the project documentation or create an issue in the repository.

---

**Built with ❤️ for the Daft Daytona Hackathon**
