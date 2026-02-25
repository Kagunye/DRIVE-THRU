# Setting Up Ollama and Whisper for Better Voice Recognition

## Overview

This system now supports **Ollama + Whisper** for significantly better speech recognition accuracy compared to Google Speech Recognition.

## Benefits

- **Better Accuracy**: Whisper provides superior speech-to-text accuracy
- **Offline Capable**: Works without internet connection (after initial model download)
- **Multi-language**: Supports many languages including Kenyan English
- **Ollama Integration**: Optional AI processing for order understanding

## Installation

### Step 1: Install Ollama

**Windows:**
1. Download from: https://ollama.ai/download
2. Install and run: `ollama serve`
3. Pull Whisper model: `ollama pull whisper`

**Linux/Raspberry Pi:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull whisper
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `openai-whisper` - Speech recognition
- `ollama` - Ollama Python client
- `torch` - Required for Whisper

### Step 3: Download Whisper Model

The first time you run the system, Whisper will automatically download the model. You can choose:
- `tiny` - Fastest, least accurate (39 MB)
- `base` - Balanced (74 MB) - **Recommended**
- `small` - Better accuracy (244 MB)
- `medium` - High accuracy (769 MB)
- `large` - Best accuracy (1550 MB)

## Configuration

Edit `config.json`:

```json
{
  "use_ollama_whisper": true,
  "whisper_model": "base",
  "use_ollama_for_processing": false,
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "llama2"
}
```

### Options

- **use_ollama_whisper**: `true` to use Whisper, `false` for Google Speech Recognition
- **whisper_model**: Model size (`tiny`, `base`, `small`, `medium`, `large`)
- **use_ollama_for_processing**: `true` to use Ollama for order processing
- **ollama_base_url**: Ollama server URL (default: localhost:11434)
- **ollama_model**: Ollama model name (default: llama2)

## Usage

### Basic Setup (Whisper only)

1. Set `use_ollama_whisper: true` in config.json
2. Run the system - Whisper will download model on first run
3. Enjoy better speech recognition!

### Full Setup (Whisper + Ollama)

1. Start Ollama server: `ollama serve`
2. Pull a model: `ollama pull llama2` (or another model)
3. Set both `use_ollama_whisper: true` and `use_ollama_for_processing: true`
4. Run the system

## Performance

### Whisper Model Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny  | 39MB | Fastest | Good | Raspberry Pi, low resources |
| base  | 74MB | Fast | Very Good | **Recommended** |
| small | 244MB | Medium | Excellent | Better accuracy needed |
| medium| 769MB | Slow | Excellent | High accuracy required |
| large | 1550MB | Slowest | Best | Maximum accuracy |

### Recommended Settings

- **Raspberry Pi**: `whisper_model: "tiny"` or `"base"`
- **Windows/Linux Desktop**: `whisper_model: "base"` or `"small"`
- **High-end Server**: `whisper_model: "medium"` or `"large"`

## Troubleshooting

### Whisper Model Not Loading

```bash
# Manually download model
python -c "import whisper; whisper.load_model('base')"
```

### Ollama Connection Failed

1. Check Ollama is running: `ollama list`
2. Verify URL in config.json matches your Ollama server
3. Test connection: `curl http://localhost:11434/api/tags`

### Out of Memory

- Use smaller Whisper model (`tiny` or `base`)
- Close other applications
- On Raspberry Pi, consider using Google Speech Recognition instead

### Slow Performance

- Use smaller Whisper model
- Disable Ollama processing if not needed
- Use Google Speech Recognition for faster response

## Fallback Behavior

If Whisper fails, the system automatically falls back to Google Speech Recognition. You'll see:
```
⚠ Whisper transcription failed: [error]
  Falling back to Google Speech Recognition...
```

## Testing

Run the test script to verify setup:

```bash
python test.py
```

The test will verify:
- Whisper model loading
- Speech recognition accuracy
- Ollama connection (if enabled)
