# Picture Analyzer - Development Principles & Structure

## Core Principles

### 1. Minimize LLM Dependencies
**Aim: Build standalone tools that don't require AI API calls for core functionality**

- **Coordinate-based cropping** (`src/core/coordinate_cropper.py`): Uses pre-defined pixel coordinates, no LLM required
- **Vision-based cropping** (`src/core/vision_cropper.py`): Optional LLM for adaptive detection
- **One-time setup**: Run LLM analysis once to generate coordinates, then reuse forever

**Philosophy**: LLMs are powerful but expensive and slow. For production workloads with consistent layouts, pre-computed coordinates are faster, cheaper, and more reliable.

### 2. Maximize Reusability
**Aim: Create modular components that can be mixed and matched**

- **Core modules** (`src/core/`): Layout parsing, image operations, panel detection
- **API layer** (`src/api/`): RESTful interface to core functionality
- **CLI tools** (`src/cli/`): Command-line access to same core modules
- **Clean interfaces**: Each module exposes clear, documented APIs

**Philosophy**: Write once, use everywhere. The same cropping logic powers both the API and CLI tools.

### 3. Maintain Organization
**Aim: Keep codebase navigable and professional**

```
picture-analyzer/
├── src/                    # All source code
│   ├── core/              # Core business logic
│   ├── api/               # REST API
│   └── cli/               # Command-line tools
├── config/                # Configuration files
│   └── dashboards/        # Dashboard definitions
├── docs/                  # Documentation
├── screenshots/           # Input data
├── outputs/              # Generated outputs
└── [entry points]         # Simple launchers
```

**Philosophy**: Logical grouping makes code easy to find, understand, and modify.

### 4. Enforce File Size Limits
**Aim: No file longer than 300 lines**

- Forces modular design
- Easier to understand and review
- Prevents "god objects"
- Encourages separation of concerns

**Philosophy**: If a file is too long, it's doing too much. Split it.

## Architecture

### Dependency Flow

```
Entry Points (crop-fast, run-api)
         ↓
    CLI / API Layer
         ↓
    Core Modules
         ↓
   Image Operations
```

**Key principle**: Dependencies flow downward only. Core modules don't import from CLI or API layers.

### Module Responsibilities

#### `src/core/`
**Purpose**: Core business logic with zero external dependencies (except libs)

- `layout.py` (174 lines): Dashboard structure parsing
- `image_ops.py` (59 lines): Image manipulation primitives
- `coordinate_cropper.py` (103 lines): Fast coordinate-based cropping
- `vision_cropper.py` (228 lines): AI-powered adaptive cropping

#### `src/api/`
**Purpose**: RESTful HTTP interface

- `app.py` (39 lines): Flask app initialization
- `routes.py` (298 lines): HTTP endpoint handlers
- `utils.py` (32 lines): Request/response helpers

#### `src/cli/`
**Purpose**: Command-line interfaces

- `crop_fast.py` (165 lines): Fast cropping CLI
- Additional tools as needed

#### `config/dashboards/`
**Purpose**: Dashboard definitions (not code)

- `static_pack.yaml`: Layout structure
- `coordinates.yaml`: Panel pixel coordinates
- `run_pack.yaml`: Runtime configuration

### Clean Dependency Network

```
coordinate_cropper ─┐
vision_cropper ─────┼─→ image_ops
                    │
                    └─→ layout

api/routes ────→ core/*
cli/crop_fast ─→ core/*
```

**No circular dependencies. No deep nesting. Each module has clear inputs/outputs.**

## File Size Compliance

Current status:
- ✅ `src/core/layout.py`: 174 lines
- ✅ `src/core/image_ops.py`: 59 lines
- ✅ `src/core/coordinate_cropper.py`: 103 lines
- ✅ `src/core/vision_cropper.py`: 228 lines
- ✅ `src/api/app.py`: 39 lines
- ✅ `src/api/routes.py`: 298 lines
- ✅ `src/api/utils.py`: 32 lines
- ✅ `src/cli/crop_fast.py`: 165 lines

**All files under 300 lines ✓**

## Production Readiness Checklist

- [x] Modular architecture
- [x] Clean separation of concerns
- [x] No circular dependencies
- [x] Files under 300 lines
- [x] Standalone operation (no LLM required for core use)
- [x] Comprehensive documentation
- [x] Error handling
- [x] Type hints where beneficial
- [x] Consistent naming conventions
- [x] Entry point scripts for easy usage

## Usage Patterns

### Production: Fast Coordinate-Based Cropping
```bash
# One-time: Generate coordinates (uses LLM once)
python -m src.cli.analyze_layout screenshots/sample.png my-dashboard

# Production: Crop instantly (no LLM, no API calls)
./crop-fast --batch
```

**Result**: ~0.1 seconds per panel, $0.00 cost

### Development/Testing: Vision-Based Cropping
```bash
# Use AI vision for adaptive detection
python -m src.cli.crop_vision screenshot.png --panel S1-L-write
```

**Result**: ~3-5 seconds per panel, ~$0.01-0.05 cost

### API Access
```bash
# Start server
./run-api

# Crop via HTTP
curl -X POST http://localhost:5000/crop-panel \
  -F "image=@dashboard.png" \
  -F "dashboard_name=my-dashboard" \
  -F "panel_id=S1-L-write"
```

## Adding New Features

### Adding a New Dashboard

1. Take a screenshot
2. Run: `python -m src.cli.analyze_layout screenshot.png dashboard-name`
3. Coordinates saved to: `config/dashboards/dashboard-name/coordinates.yaml`
4. Ready to use with `crop-fast`

### Adding a New CLI Tool

1. Create `src/cli/my_tool.py` (< 300 lines)
2. Import from `src.core.*` only
3. Create entry point: `my-tool` → calls `src.cli.my_tool.main()`
4. Make executable: `chmod +x my-tool`

### Adding a New API Endpoint

1. Add route handler to `src/api/routes.py`
2. Use existing core modules
3. If route handler file gets too long (>300 lines), split into multiple blueprints

### Adding a New Core Module

1. Create `src/core/my_module.py` (< 300 lines)
2. Add to `src/core/__init__.py` exports
3. Import in CLI/API as needed
4. **Never import from CLI/API layers**

## Testing

```bash
# Validate structure
python -m src.utils.validate_setup

# Test coordinate cropping
./crop-fast screenshot.png -p S1-L-write

# Test API
./run-api &
curl http://localhost:5000/health
```

## Maintenance Guidelines

### When Adding Code

- **Check file length**: If approaching 300 lines, split now
- **Check dependencies**: Does this import from a higher layer? Refactor.
- **Check reusability**: Could this be used elsewhere? Extract to core.

### When Refactoring

- **Start from leaves**: Refactor core modules first, then API/CLI
- **Test incrementally**: Don't break everything at once
- **Maintain backwards compatibility**: Deprecate, don't delete

### When Documenting

- **Update this file**: Architecture changes? Document here.
- **Update docs/**: User-facing changes? Update guides.
- **Comment complex logic**: Why, not what.

## Design Decisions

### Why coordinate-based over LLM-only?

**Speed**: 40x faster (0.1s vs 4s per panel)
**Cost**: Free vs $0.01-0.05 per panel
**Reliability**: Same result every time
**Scalability**: No API rate limits

**Trade-off**: Requires dashboard structure is consistent

### Why split API into app + routes + utils?

**Testability**: Can test route logic without Flask app
**Clarity**: app.py shows configuration, routes.py shows behavior
**Scalability**: Easy to add new blueprints as API grows

### Why not use a framework for CLI?

**Simplicity**: argparse is stdlib, zero dependencies
**Flexibility**: Easy to customize behavior
**Size**: Keeps CLI files small

## Future Considerations

### If codebase grows beyond current structure:

- **Add `src/services/`**: For complex multi-module operations
- **Add `src/models/`**: For data models and schemas
- **Split `src/cli/`** into submodules if tools proliferate
- **Consider plugins**: For dashboard-specific logic

### If performance becomes critical:

- **Cache coordinates** in memory
- **Batch image operations**
- **Async API** with FastAPI
- **C extensions** for image processing

### If collaboration expands:

- **Add type stubs** (`.pyi` files)
- **Add property-based tests**
- **CI/CD pipeline** for validation
- **Pre-commit hooks** for formatting

## Summary

**This codebase prioritizes**:
1. **Independence** from expensive LLM calls
2. **Reusability** through modular design
3. **Organization** with clear structure
4. **Maintainability** through size limits

**The result**: Production-ready code that's fast, cheap, and easy to understand.
