# 🎨 AI Image Generation with DALL-E 3

Your Image Canvas Workspace now supports AI image generation through chat commands using OpenAI's DALL-E 3!

## 🚀 Quick Setup

### 1. Get OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Set Environment Variable
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows (Command Prompt)  
set OPENAI_API_KEY=sk-your-key-here

# macOS/Linux
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Services
```bash
# Terminal 1 - Backend
cd backend
python start.py

# Terminal 2 - Frontend  
cd image-canvas
npm run dev
```

## 💬 How to Generate Images

Simply type any of these commands in the chat:

### **Basic Generation:**
- `generate a sunset over mountains`
- `create an image of a futuristic city`
- `draw a cat wearing a spacesuit`
- `make a picture of a dragon`

### **Advanced Commands:**
- `generate a photorealistic portrait of a robot`
- `create an image of abstract art with vibrant colors`
- `draw a medieval castle in a fantasy style`
- `/imagine a cyberpunk street scene at night`

## 🎯 What Happens:

1. **You type**: `"generate a sunset"`
2. **Chat shows**: `"🎨 Generating image: 'a sunset'..."`
3. **DALL-E 3 creates** the image (10-30 seconds)
4. **Image appears** automatically on your canvas
5. **Chat confirms**: `"✅ Image generated and added to canvas!"`

## ✨ Features

### **Smart Prompt Enhancement**
Your prompts are automatically enhanced for better results:
- `"sunset"` → `"sunset, high quality, detailed"`
- Ensures professional-looking images

### **DALL-E 3 Refinement**  
DALL-E 3 may refine your prompt for better results:
- You: `"draw a cat"`
- DALL-E: `"A fluffy orange tabby cat sitting on a windowsill, sunlight streaming through"`

### **Real-time Collaboration**
- Multiple users can generate images simultaneously
- Everyone sees the generated images in real-time
- Chat shows generation progress for all users

### **Canvas Integration**
- Generated images appear at canvas center
- Standard 320px max width (preserves aspect ratio)
- Can be moved, grouped, and deleted like any image
- Works with all existing canvas features

## 🎨 Image Specifications

### **DALL-E 3 Settings:**
- **Model**: DALL-E 3 (latest)
- **Size**: 1024×1024 (square format)
- **Quality**: Standard (faster) or HD (higher quality)
- **Style**: Vivid (hyper-real) or Natural (more natural)

### **Supported Formats:**
- Automatically converted to base64 for storage
- Compatible with all canvas features
- High-resolution output

## 🔧 Advanced Usage

### **API Endpoint**
Direct API access for advanced use:
```bash
POST /api/canvas/{canvas_id}/generate-image
{
  "prompt": "a beautiful sunset",
  "size": "1024x1024", 
  "quality": "standard",
  "style": "vivid"
}
```

### **WebSocket Events**
Real-time events for custom integrations:
- `generation_started` - Generation begins
- `image_generated` - Image ready and added to canvas
- `generation_failed` - Generation error

## 💡 Tips for Better Results

### **Be Specific**
- ❌ `"draw something cool"`
- ✅ `"draw a steampunk airship flying through clouds"`

### **Include Style**
- `"photorealistic portrait of..."`
- `"cartoon-style illustration of..."`
- `"oil painting of..."`
- `"pixel art of..."`

### **Add Context**
- `"sunset over mountains with purple sky"`
- `"cat sitting on a Victorian chair in a library"`

### **Use Lighting**
- `"...in golden hour lighting"`
- `"...with dramatic shadows"`
- `"...in soft morning light"`

## 🚨 Error Handling

### **Common Issues:**

**API Key Not Set:**
```
❌ Failed to generate image: OpenAI API key not configured
```
**Solution**: Set the `OPENAI_API_KEY` environment variable

**Content Policy:**
```
❌ Failed to generate image: Content policy violation
```
**Solution**: Modify your prompt to be more appropriate

**Rate Limits:**
```
❌ Failed to generate image: Rate limit exceeded
```
**Solution**: Wait a moment and try again

## 💰 Pricing

DALL-E 3 pricing (as of 2024):
- **Standard**: ~$0.040 per image (1024×1024)
- **HD Quality**: ~$0.080 per image (1024×1024)

Your OpenAI account will be charged per generation.

## 🔐 Security

- API key is stored as environment variable
- Images are processed securely through OpenAI
- Generated images are stored as base64 data
- No images are permanently stored by default

## 🚀 Ready to Create!

Your AI-powered image generation is now ready! Try typing:
`"generate a magical forest with glowing mushrooms"`

Have fun creating amazing images with AI! 🎨✨
