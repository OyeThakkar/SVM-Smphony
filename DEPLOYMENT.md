# Deployment Guide

## Prerequisites

- Python 3.7 or higher
- pip package manager

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/OyeThakkar/SVN-Smphony.git
cd SVN-Smphony
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Test CLI
python -m pod_compiler.cli validate 06-Feb-2026

# Run integration tests
python tests/test_integration.py
```

## Usage

### Command Line Interface

#### Compile a Pod

```bash
python -m pod_compiler.cli compile \
  --theatre T1042 \
  --rating PG-13 \
  --section LPS \
  --aspect Flat \
  --start-date 06-Feb-2026 \
  --cpls ad1.xml ad2.xml ad3.xml ad4.xml \
  --output ./output
```

#### Validate Date Format

```bash
python -m pod_compiler.cli validate 06-Feb-2026
```

#### Get Help

```bash
python -m pod_compiler.cli --help
python -m pod_compiler.cli compile --help
```

### Web Interface

#### Start Web Server

```bash
python -m pod_compiler.web
```

Then navigate to: `http://localhost:5000`

#### Custom Port

Edit `pod_compiler/web.py` and change the port in the `app.run()` call.

### Python API

```python
from pod_compiler.compiler import compile_pod

result = compile_pod(
    theatre_id="T1042",
    rating="PG-13",
    section="LPS",
    aspect="Flat",
    start_date="06-Feb-2026",
    cpl_files=["ad1.xml", "ad2.xml", "ad3.xml", "ad4.xml"],
    output_dir="./output",
    asset_repository=None  # Optional
)

print(f"Pod compiled: {result['pod_name']}")
print(f"Output: {result['output_dir']}")
```

## Directory Structure After Installation

```
SVN-Smphony/
├── pod_compiler/           # Main package
├── examples/              # Example CPL files
├── tests/                 # Test suite
├── output/                # Generated pods (created on first run)
├── README.md
├── ARCHITECTURE.md
├── API.md
└── requirements.txt
```

## Configuration

### Asset Repository (Optional)

If you have a central asset repository with MXF files:

```bash
python -m pod_compiler.cli compile \
  --theatre T1042 \
  --rating PG-13 \
  --section LPS \
  --aspect Flat \
  --start-date 06-Feb-2026 \
  --cpls ad1.xml ad2.xml ad3.xml ad4.xml \
  --assets /path/to/asset/repository
```

This enables:
- Asset existence validation
- SHA-1 hash calculation for assets
- Future MXF file copying/linking

### Output Directory

Default: `./output`

Change with `--output` flag:

```bash
python -m pod_compiler.cli compile ... --output /path/to/output
```

## Production Deployment

### Option 1: Standalone Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start web server
python -m pod_compiler.web
```

### Option 2: Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "-m", "pod_compiler.web"]
```

Build and run:

```bash
docker build -t svn-symphony .
docker run -p 5000:5000 -v /path/to/cpls:/cpls -v /path/to/output:/output svn-symphony
```

### Option 3: Batch Processing

Create a batch script for multiple theatres:

```bash
#!/bin/bash
# batch_compile.sh

THEATRES=("T1042" "T1043" "T1044")
RATING="PG-13"
SECTION="LPS"
ASPECT="Flat"
DATE="06-Feb-2026"

for THEATRE in "${THEATRES[@]}"; do
  python -m pod_compiler.cli compile \
    --theatre "$THEATRE" \
    --rating "$RATING" \
    --section "$SECTION" \
    --aspect "$ASPECT" \
    --start-date "$DATE" \
    --cpls ad1.xml ad2.xml ad3.xml ad4.xml \
    --output ./output
done
```

## Monitoring & Logging

### Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitor Output

Check generated pods:

```bash
ls -la output/
```

Verify pod structure:

```bash
ls -la output/T1042_PG13_LPS_FLAT_06-Feb-2026/
```

## Troubleshooting

### Issue: "CPL is encrypted"

**Solution:** Only unencrypted ads are supported. Use unencrypted CPL files.

### Issue: "EditRate mismatch"

**Solution:** Ensure all CPL files use the same frame rate (e.g., all 24fps).

### Issue: "Aspect ratio mismatch"

**Solution:** Ensure all CPL files use the same aspect ratio (all Flat or all Scope).

### Issue: "Invalid date format"

**Solution:** Use `dd-mmm-yyyy` format (e.g., `06-Feb-2026`, not `2026-02-06`).

### Issue: "Too many CPL files"

**Solution:** Maximum is 20 CPL files per pod. Split into multiple pods if needed.

### Issue: Web interface not accessible

**Solution:** 
1. Check firewall settings
2. Ensure port 5000 is not in use
3. Try binding to 0.0.0.0 instead of localhost

## Performance Considerations

### Compilation Speed

- CPL parsing: ~10-50ms per file
- Validation: ~5-20ms per CPL
- Stitching: ~50-100ms for 4 CPLs
- Package generation: ~10-30ms

**Total:** Typical 4-CPL pod compiles in < 1 second

### Scale Testing

For 1,500 theatres:
- Sequential: ~25 minutes
- Parallel (10 workers): ~2.5 minutes
- Parallel (50 workers): ~30 seconds

### Memory Usage

- Per compilation: ~10-20 MB
- Base process: ~30-50 MB
- Web server: ~50-100 MB

## Backup & Recovery

### Backup Considerations

**What to backup:**
- Input CPL files
- Generated pods (optional, can be regenerated)
- Configuration files

**What NOT to backup:**
- Python cache (`__pycache__`)
- Temporary files
- Generated output (if using idempotent regeneration)

### Recovery

If output is lost:
1. Re-run compilation with same inputs
2. Pod ID will be identical (deterministic)
3. Output will be functionally identical

## Maintenance

### Regular Tasks

1. **Clean old pods:**
   ```bash
   # Delete pods older than 30 days
   find output/ -type d -mtime +30 -exec rm -rf {} +
   ```

2. **Update dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   python tests/test_integration.py
   ```

## Support

For issues and questions:
1. Check documentation (README.md, ARCHITECTURE.md, API.md)
2. Review error messages
3. Run integration tests
4. Check GitHub issues

## Version Information

Current Version: 1.0.0

**Release Date:** February 2026

**Python Support:** 3.7+

**Dependencies:**
- Flask >= 2.3.0
- Standard library only for core functionality
