# Daft-Daytona Hackathon PoC

AI Image Generation & Analysis Pipeline using Daytona.io and Daft AI

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Run the setup script
python setup.py

# This will:
# - Create necessary directories
# - Create .env file from template
# - Verify Python version
```

### 2. Configure API Keys

Edit `.env` file and add your Daytona API key:
```
DAYTONA_API_KEY=your-actual-api-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test Daytona Connection

```bash
python infrastructure/sandbox/test_connection.py
```

## 📁 Project Structure

```
daft_daytona_hackathon/
├── infrastructure/
│   ├── sandbox/         # Daytona sandbox code
│   └── daft/           # Daft pipeline code
├── api/                # FastAPI endpoints
├── notebooks/          # Jupyter notebooks
├── data/              # Input data
├── output/            # Generated outputs
└── models/            # Model configurations
```

## 🔧 Architecture

1. **Image Generation** (Daytona)
   - Host Flux or similar models in secure sandboxes
   - Sub-90ms startup times for rapid iteration

2. **Data Processing** (Daft)
   - Process multimodal data (images + metadata)
   - Extract embeddings and features
   - Analyze with LLMs

3. **Similarity Pipeline**
   - Analyze generated images
   - Extract style and content features
   - Generate similar variations

## 🛡️ Security Notes

- Never commit `.env` file (it's in .gitignore)
- Use `.env.example` as template for team members
- API keys should be kept secure

## 📝 TODO

- [ ] Set up Flux model on Daytona
- [ ] Create Daft pipeline for image processing
- [ ] Implement LLM analysis integration
- [ ] Build similarity generation loop
- [ ] Create FastAPI endpoints
- [ ] Add demo notebook
