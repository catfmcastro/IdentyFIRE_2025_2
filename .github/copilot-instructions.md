# IdentyFIRE - AI Agent Instructions

## Project Overview

**IdentyFIRE** is a fire detection system using Deep Learning (CNN) with a client-server architecture. It consists of three main GUI applications that work together: training, server (API), and client (detection).

### Architecture Pattern

```
Training GUI (training_gui.py) → Trains models → Saves to /models
                                ↓
Server GUI (server_gui.py) ← Loads models ← Flask API on port 5000
                                ↓
Client GUI (client_gui.py) → Sends images → Gets predictions
```

**Critical**: This is a **loosely-coupled** system where components communicate via:
- File system (`/models` directory for `.h5` model files)
- HTTP REST API (Flask server at `http://127.0.0.1:5000`)
- Shared `config.json` configuration

## Core Components

### 1. Training System (`main.py` + `training_gui.py`)
- **main.py**: CLI script for CNN training using TensorFlow/Keras
- **training_gui.py**: Tkinter GUI that wraps `main.py` via subprocess
- **Key Pattern**: GUI spawns `main.py` as subprocess, parses stdout for progress
- **Model Architecture**: 4-layer CNN (Conv2D→MaxPooling2D) + Dropout(0.5) + Dense layers
- **Output**: Generates `.h5` model files, training graphs (PNG), confusion matrix, results JSON

### 2. Server System (`server_gui.py`)
- **Flask REST API** with these endpoints:
  - `/health` - Server status check
  - `/models` - List available models
  - `/current_model` - Get loaded model info
  - `/load_model` - Load a specific model
  - `/predict` - Single image prediction
  - `/predict_batch` - Batch processing (GPU-optimized)
- **Critical**: Server runs in a separate thread; GUI uses `make_server()` from `werkzeug.serving` for graceful shutdown
- **Model Loading**: Can auto-load default model on startup (see `config.json`)

### 3. Client System (`client_gui.py`)
- **Tkinter GUI** that makes HTTP requests to server
- **Two modes**: Single image or batch folder processing
- **Batch Optimization**: Uses `/predict_batch` endpoint which processes multiple images simultaneously on GPU (10-20x faster than sequential)

### 4. Utilities (`utils.py`)
- Shared functions for all components
- **Key Functions**:
  - `load_config()` - Loads `config.json` with proper path resolution
  - `scan_models()` - Auto-discovers `.h5` files in models directory
  - `process_image_from_bytes()` - Preprocessing (resize to 150x150, normalize to [0,1])
  - `make_prediction()` - Wrapper for model inference with threshold logic

## Configuration System

**File**: `config.json` at project root
- Used by all components (training, server, client)
- **Path Resolution Pattern**: All paths in config can be relative (resolved from project root) or absolute
- **Important Settings**:
  - `server.models_directory`: Where models are stored (default: `./models`)
  - `server.auto_load_default`: Auto-load model on server startup
  - `model.img_height/img_width`: Must match training dimensions (default: 150x150)
  - `model.prediction_threshold`: Fire detection threshold (default: 0.5)

## Critical Workflows

### Training a Model
1. User opens `training_gui.py`
2. Configures dataset path (must have `train/`, `valid/`, `test/` with `fire/` and `nofire/` subdirectories)
3. GUI calls `main.py` via subprocess with command-line args: `python main.py <dataset_dir> <model_name> <epochs> <batch_size>`
4. `main.py` outputs progress to stdout (GUI parses for epoch updates)
5. Generates: `<model_name>.h5`, `<model_name>_best.h5`, graphs, confusion matrix, results JSON
6. If "auto-save" enabled, moves model to `/models` directory
7. If "auto-load" enabled, sends HTTP POST to `/load_model` endpoint

### Loading Model on Server
**Two methods**:
1. **Auto-load**: Set `config.json` → `server.auto_load_default = true` → Server loads on startup
2. **Manual**: Training GUI → Gerenciamento tab → Select model → "Carregar no Servidor" button → HTTP POST to `/load_model`

### Making Predictions
1. Client connects to server (checks `/health` endpoint)
2. Verifies model is loaded (checks `/current_model`)
3. User selects image → Client sends multipart/form-data POST to `/predict`
4. Server preprocesses (150x150, normalize), runs inference, returns JSON with `fire_detected` and `confidence`

## Technology Stack & Dependencies

- **TensorFlow**: Uses `tensorflow-directml-plugin` for universal GPU support (AMD/Intel/NVIDIA)
- **GUI**: Tkinter (native Python, no external deps)
- **Server**: Flask + Flask-CORS
- **Image Processing**: Pillow (PIL), NumPy
- **Key Version**: `tensorflow-directml-plugin==0.4.0.dev230202` (specific version for DirectML compatibility)

## Environment Setup

**Critical**: Project uses Windows with DirectML for GPU acceleration
- **Shell**: PowerShell (`pwsh.exe`)
- **Activation**: Scripts in `/scripts` directory (`.bat` for batch, `.ps1` for PowerShell, `.sh` for Linux/Mac)
- **Virtual Environment**: `.venv` in project root (not tracked in git)
- **Python**: 3.8+ required

## Common Patterns & Conventions

### Path Handling
```python
# All modules use this pattern for config/model paths:
if not os.path.isabs(path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up from /src
    path = os.path.join(project_root, path)
```

### Threading Pattern
- **GUIs**: Always use `threading.Thread(target=..., daemon=True)` for long operations
- **Server**: Flask runs in separate thread to keep GUI responsive
- **Critical**: Use `master.after(0, callback)` to update Tkinter UI from threads

### Error Handling in API
- **Success Response**: `{'success': True, 'fire_detected': bool, 'confidence': float, ...}`
- **Error Response**: `{'success': False, 'error': str, 'message': str}`
- Always return JSON, even for errors (with appropriate HTTP status codes)

### Model File Naming
- Primary model: `<name>.h5`
- Best checkpoint: `<name>_best.h5` (saved by ModelCheckpoint callback based on val_accuracy)
- Related files: `<name>_training_history.png`, `<name>_confusion_matrix.png`, `<name>_results.json`

## Dataset Structure
**Required structure** for training:
```
dataset/
├── train/
│   ├── fire/      # Images with fire
│   └── nofire/    # Images without fire
├── valid/
│   ├── fire/
│   └── nofire/
└── test/
    ├── fire/
    └── nofire/
```

## GPU Optimization Notes

- **Batch Processing**: Server's `/predict_batch` endpoint processes all images in single `model.predict()` call for GPU efficiency
- **Memory Management**: `tf.config.experimental.set_memory_growth(gpu, True)` allows dynamic VRAM allocation
- **Data Augmentation**: Only applied to training data (rotation, shift, flip, zoom)
- **Image Preprocessing**: All images resized to 150x150, normalized to [0,1] range

## Testing & Debugging

### Verify Installation
```powershell
python -c "import tensorflow as tf; print('TF:', tf.__version__); print('GPUs:', len(tf.config.list_physical_devices('GPU')))"
```

### Test Server Manually
```powershell
curl http://127.0.0.1:5000/health
curl -X POST -F "image=@test.jpg" http://127.0.0.1:5000/predict
```

### Common Issues
1. **"Model not loaded"**: Check server console, verify model loaded via `/current_model` endpoint
2. **GPU not detected**: Reinstall `tensorflow-directml-plugin==0.4.0.dev230202`
3. **"Image processing failed"**: Check image format (must be RGB), size (<10MB), valid extension
4. **Model loading from training_gui fails**: 
   - Verify server is running (`http://127.0.0.1:5000/health`)
   - Check models directory path resolution (server vs training_gui)
   - Enable debug logging in `training_gui.py` functions: `auto_load_model_to_server()` and `load_model_to_server()`
   - Verify model file exists in models directory before loading

## Scripts & Automation

All scripts in `/scripts` directory:
- **install.bat/sh**: Creates venv, installs requirements
- **start_server.bat**: Launches `server_gui.py`
- **start_client.bat**: Launches `client_gui.py`
- **start_training.bat**: Launches `training_gui.py`
- **start_all.bat**: Launches all GUIs simultaneously (Windows only)

## Code Organization Rules

- **Never import GUI modules into each other** - they are independent entry points
- **utils.py is the ONLY shared code** - all common logic goes here
- **main.py is CLI-only** - no GUI imports, must work standalone
- **All GUIs import from utils.py** - not from each other
- **config.json is the single source of truth** - don't hardcode paths/URLs

## When Modifying Code

1. **Changing image dimensions**: Update `config.json` → `model.img_height/img_width` + retrain models
2. **Adding API endpoints**: Update both `server_gui.py` (server) and `client_gui.py` (client)
3. **Changing model architecture**: Modify `main.py` only (GUIs are agnostic to architecture)
4. **Adding new utilities**: Always add to `utils.py` with proper docstrings
5. **Path handling**: Use the path resolution pattern (see "Path Handling" above)

## Performance Considerations

- **Batch size 32** is optimal for most GPUs (16 for <4GB VRAM, 64+ for high-end)
- **Epochs 20-30** usually sufficient for convergence
- **Batch endpoint** should always be preferred over sequential predictions for multiple images
- **ModelCheckpoint callback** saves best model automatically during training

## Expected Model Performance

With balanced dataset (50% fire/50% nofire, 1000+ images per class):
- Training accuracy: 95-98%
- Validation accuracy: 92-96%
- Test accuracy: 90-95%

## Important Notes

- **DirectML** allows universal GPU support on Windows without CUDA (works with AMD, Intel, NVIDIA)
- **Tkinter GUIs** are single-threaded - always use `threading.Thread` + `master.after()` for updates
- **Flask development server** (`werkzeug`) is fine for this use case (single-user, local)
- **No database** - all state persisted in files (models, config, logs)
