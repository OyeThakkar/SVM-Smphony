# API Reference

## Command Line Interface

### Compile Command

Compile an ad pod from multiple CPL files.

```bash
python -m pod_compiler.cli compile \
  --theatre THEATRE_ID \
  --rating RATING \
  --section SECTION \
  --aspect ASPECT \
  --start-date DATE \
  --cpls CPL_FILE [CPL_FILE ...] \
  [--output OUTPUT_DIR] \
  [--assets ASSET_REPO]
```

**Parameters:**

| Parameter | Required | Type | Options | Description |
|-----------|----------|------|---------|-------------|
| `--theatre` | Yes | String | - | Theatre identifier (e.g., T1042) |
| `--rating` | Yes | String | G, PG, PG-13, R | Content rating |
| `--section` | Yes | String | LPS, EPS | Section type |
| `--aspect` | Yes | String | Flat, Scope | Aspect ratio |
| `--start-date` | Yes | String | dd-mmm-yyyy | Start date (e.g., 06-Feb-2026) |
| `--cpls` | Yes | List | - | Ordered CPL XML files (1-20) |
| `--output` | No | String | - | Output directory (default: ./output) |
| `--assets` | No | String | - | Asset repository path (optional) |

**Example:**

```bash
python -m pod_compiler.cli compile \
  --theatre T1042 \
  --rating PG-13 \
  --section LPS \
  --aspect Flat \
  --start-date 06-Feb-2026 \
  --cpls ad1.xml ad2.xml ad3.xml ad4.xml
```

**Exit Codes:**
- 0: Success
- 1: Failure (validation, compilation, or system error)

### Validate Command

Validate date format.

```bash
python -m pod_compiler.cli validate DATE
```

**Example:**

```bash
python -m pod_compiler.cli validate 06-Feb-2026
```

## Web API

### POST /api/compile

Compile an ad pod.

**Request:**

Content-Type: `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `theatre_id` | String | Yes | Theatre identifier |
| `rating` | String | Yes | Content rating (G/PG/PG-13/R) |
| `section` | String | Yes | Section (LPS/EPS) |
| `aspect` | String | Yes | Aspect ratio (Flat/Scope) |
| `start_date` | String | Yes | Start date (dd-mmm-yyyy) |
| `cpl_files` | File[] | Yes | CPL XML files (1-20) |

**Response (Success):**

```json
{
  "success": true,
  "pod_name": "T1042_PG13_LPS_FLAT_06-Feb-2026",
  "pod_id": "84a366cb8af4dfbd0f259276c77b843a8c4e04796c0efa2da618bee21a161b08",
  "output_dir": "./output/T1042_PG13_LPS_FLAT_06-Feb-2026",
  "cpl_count": 4,
  "asset_count": 8,
  "warnings": []
}
```

**Response (Error):**

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

**Status Codes:**
- 200: Success
- 400: Validation error or bad request
- 500: Server error

### POST /api/validate-date

Validate date format.

**Request:**

Content-Type: `application/json`

```json
{
  "date": "06-Feb-2026"
}
```

**Response:**

```json
{
  "valid": true,
  "date": "06-Feb-2026"
}
```

## Python API

### pod_compiler.compiler.compile_pod()

Main function to compile a pod.

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
```

**Returns:**

```python
{
    'success': True,
    'pod_name': 'T1042_PG13_LPS_FLAT_06-Feb-2026',
    'pod_id': '84a366cb8af4dfbd0f259276c77b843a8c4e04796c0efa2da618bee21a161b08',
    'output_dir': './output/T1042_PG13_LPS_FLAT_06-Feb-2026',
    'cpl_count': 4,
    'asset_count': 8,
    'validation_warnings': [],
    'package_info': {...}
}
```

**Raises:**
- `PodCompilerError`: If compilation fails

### pod_compiler.cpl_parser.parse_cpl()

Parse a CPL file.

```python
from pod_compiler.cpl_parser import parse_cpl

cpl_data = parse_cpl("ad1.xml")
```

**Returns:**

```python
{
    'cpl_uuid': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'content_title': 'Ad 1 - Product Launch',
    'edit_rate': '24',
    'aspect_ratio': 'Flat',
    'audio_layout': '5.1',
    'reels': [
        {
            'reel_id': '11111111-1111-1111-1111-111111111111',
            'assets': [
                {
                    'type': 'MainPicture',
                    'uuid': 'pic11111-1111-1111-1111-111111111111',
                    'element': <Element>
                },
                {
                    'type': 'MainSound',
                    'uuid': 'snd11111-1111-1111-1111-111111111111',
                    'element': <Element>
                }
            ]
        }
    ],
    'encrypted': False,
    'namespace': 'http://www.smpte-ra.org/schemas/2067-3/2016'
}
```

**Raises:**
- `CPLParseError`: If parsing fails

### pod_compiler.validator.CPLValidator

Validate CPL files and inputs.

```python
from pod_compiler.validator import CPLValidator

validator = CPLValidator(asset_repository="/path/to/assets")

# Validate individual CPL
warnings = validator.validate_individual_cpl(cpl_data)

# Validate cross-CPL compatibility
warnings = validator.validate_cross_cpl_compatibility([cpl1, cpl2])

# Validate complete pod inputs
result = validator.validate_pod_inputs(
    theatre_id="T1042",
    rating="PG-13",
    section="LPS",
    aspect="Flat",
    start_date="06-Feb-2026",
    cpl_data_list=[cpl1, cpl2]
)
# Returns: {'valid': bool, 'errors': list, 'warnings': list}
```

**Raises:**
- `ValidationError`: If critical validation fails

### pod_compiler.pod_identity.PodIdentity

Generate pod names and IDs.

```python
from pod_compiler.pod_identity import PodIdentity

# Generate pod name
pod_name = PodIdentity.generate_pod_name(
    theatre_id="T1042",
    rating="PG-13",
    section="LPS",
    aspect="Flat",
    start_date="06-Feb-2026"
)
# Returns: "T1042_PG13_LPS_FLAT_06-Feb-2026"

# Generate deterministic pod ID
pod_id = PodIdentity.generate_pod_id(
    theatre_id="T1042",
    rating="PG-13",
    section="LPS",
    aspect="Flat",
    start_date="06-Feb-2026",
    cpl_uuids=["uuid1", "uuid2", "uuid3"]
)
# Returns: "84a366cb8af4dfbd0f259276c77b843a8c4e04796c0efa2da618bee21a161b08"

# Validate date format
valid = PodIdentity.validate_date_format("06-Feb-2026")
# Returns: True/False

# Parse date
date_obj = PodIdentity.parse_date("06-Feb-2026")
# Returns: datetime object
```

### pod_compiler.cpl_stitcher.CPLStitcher

Stitch multiple CPLs into one.

```python
from pod_compiler.cpl_stitcher import CPLStitcher

stitcher = CPLStitcher(
    pod_name="T1042_PG13_LPS_FLAT_06-Feb-2026",
    pod_id="84a366cb8af4dfbd0f259276c77b843a8c4e04796c0efa2da618bee21a161b08"
)

# Stitch and write
pod_id = stitcher.stitch_and_write(
    cpl_data_list=[cpl1, cpl2, cpl3],
    output_path="output/CPL.xml"
)
```

### pod_compiler.dcp_generator.DCPPackageGenerator

Generate DCP package structure.

```python
from pod_compiler.dcp_generator import DCPPackageGenerator

generator = DCPPackageGenerator(
    pod_name="T1042_PG13_LPS_FLAT_06-Feb-2026",
    output_dir="./output/T1042_PG13_LPS_FLAT_06-Feb-2026"
)

package_info = generator.generate_package(
    cpl_path="output/CPL.xml",
    cpl_uuid="pod-uuid",
    asset_uuids=["uuid1", "uuid2", "uuid3"],
    asset_repository="/path/to/assets"
)
```

## Data Formats

### Pod Name Format

```
<THEATERID>_<RATING>_<SECTION>_<ASPECT>_<dd-mmm-yyyy>
```

**Rules:**
- Uppercase
- Underscores as separators
- PG-13 → PG13 (no hyphen)
- Date: dd-mmm-yyyy (e.g., 06-Feb-2026)

**Examples:**
- `T1042_PG13_LPS_FLAT_06-Feb-2026`
- `T5500_R_EPS_SCOPE_15-Mar-2026`
- `T0001_G_LPS_FLAT_01-Jan-2026`

### Date Format

**Format:** `dd-mmm-yyyy`

**Examples:**
- 06-Feb-2026
- 15-Mar-2026
- 01-Jan-2026

**Month Abbreviations:**
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec

### CPL UUID Format

Standard UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

May include `urn:uuid:` prefix (automatically stripped during parsing).

## Error Messages

### Validation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| "CPL is encrypted" | CPL has encryption | Use unencrypted CPLs only |
| "EditRate mismatch" | Different edit rates | Ensure all CPLs use same frame rate |
| "Aspect ratio mismatch" | Different aspects | Ensure all CPLs use same aspect |
| "Invalid date format" | Wrong date format | Use dd-mmm-yyyy format |
| "Invalid rating" | Unknown rating | Use G/PG/PG-13/R |
| "Too many CPL files" | More than 20 CPLs | Limit to 20 CPLs per pod |

### Compilation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| "Failed to parse CPL" | Invalid XML | Check CPL XML structure |
| "CPL UUID not found" | Missing ID element | Ensure CPL has valid ID |
| "No reels found" | Empty CPL | Use CPLs with reel content |

## Best Practices

### CPL Preparation

1. **Verify Compatibility:**
   - Same edit rate across all CPLs
   - Same aspect ratio
   - No encryption

2. **Order Matters:**
   - Upload/specify CPLs in desired playback order
   - Order cannot be changed after stitching

3. **Naming:**
   - Use descriptive CPL content titles
   - Keep CPL file names organized

### Pod Management

1. **Determinism:**
   - Same inputs always produce same pod
   - Use for rebuild/verification

2. **Storage:**
   - Clean up old pods regularly
   - Archive completed weeks

3. **Distribution:**
   - Validate pod before distribution
   - Test playback on target systems

### Error Handling

1. **Validation Warnings:**
   - Review all warnings
   - Decide if acceptable for use case

2. **Failed Compilation:**
   - Check error message details
   - Verify CPL files are valid
   - Ensure parameters are correct

3. **Asset Issues:**
   - Verify asset repository path
   - Check asset file names match UUIDs
