# Quick Start: Using Ollama + Whisper

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Enable Whisper in Config

Edit `config.json`:
```json
{
  "use_ollama_whisper": true,
  "whisper_model": "base"
}
```

### 3. Run the System

```bash
python simulate_loop.py
```

**That's it!** Whisper will automatically download on first run and provide better accuracy.

## Optional: Full Ollama Setup

### Step 1: Install Ollama

**Windows:**
- Download: https://ollama.ai/download
- Run installer
- Start: `ollama serve`

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

### Step 2: Enable Ollama Processing

Edit `config.json`:
```json
{
  "use_ollama_whisper": true,
  "use_ollama_for_processing": true,
  "ollama_model": "llama2"
}
```

### Step 3: Pull Model

```bash
ollama pull llama2
```

## Benefits

✅ **Better Accuracy**: Whisper is more accurate than Google Speech Recognition  
✅ **Offline**: Works without internet (after model download)  
✅ **Multi-language**: Supports many languages  
✅ **AI Processing**: Ollama can understand and format orders better  

## Model Recommendations

- **Whisper**: Use `base` for best balance (74MB)
- **Ollama**: Use `llama2` or `mistral` for order processing

## Troubleshooting

**Whisper not loading?**
- First run downloads model automatically
- Check internet connection for download
- Use smaller model: `"whisper_model": "tiny"`

**Ollama connection failed?**
- Make sure Ollama is running: `ollama serve`
- Check URL in config.json matches your setup
- Test: `ollama list`
