# Architecture Documentation

## System Overview

SVN-Symphony is a deterministic ad pod compiler that enforces playback order at the DCP media layer through physical CPL stitching. The system transforms individual ad DCPs into unified, theatre-specific ad pods that guarantee execution order.

## Core Components

### 1. CPL Parser (`cpl_parser.py`)

**Purpose:** Parse DCP Composition Playlist (CPL) XML files

**Key Functions:**
- Extract CPL UUID and metadata
- Parse reel structures
- Extract asset references (picture, sound, subtitles)
- Detect EditRate, aspect ratio, audio configuration
- Check encryption status

**Namespaces Supported:**
- SMPTE 2067-3/2016
- SMPTE 2067-3/2013
- PROTO-ASDCP-CPL

### 2. Validator (`validator.py`)

**Purpose:** Validate CPL compatibility and inputs

**Validation Types:**

**Individual CPL Validation:**
- No encryption (critical)
- Valid structure with reels and assets
- Required metadata present

**Cross-CPL Validation:**
- EditRate consistency (critical)
- Aspect ratio consistency (critical)
- Audio layout consistency (warning only)
- No duplicate CPL UUIDs
- No duplicate asset UUIDs

**Pod Input Validation:**
- Theatre ID format
- Rating (G/PG/PG-13/R)
- Section (LPS/EPS)
- Aspect (Flat/Scope)
- Date format (dd-mmm-yyyy)
- CPL count (1-20)

### 3. Pod Identity (`pod_identity.py`)

**Purpose:** Generate deterministic pod names and IDs

**Pod Naming:**
```
Format: <THEATERID>_<RATING>_<SECTION>_<ASPECT>_<dd-mmm-yyyy>
Example: T1042_PG13_LPS_FLAT_06-Feb-2026
```

**Pod ID Generation:**
- SHA-256 hash of: theatre + rating + section + aspect + date + ordered CPL UUIDs
- Same inputs → Same pod ID (idempotent)
- Different inputs → Different pod ID

### 4. CPL Stitcher (`cpl_stitcher.py`)

**Purpose:** Stitch multiple CPLs into one unified CPL

**Process:**
1. Create new CPL root element
2. Add metadata (ID, title, dates)
3. Extract reels from source CPLs in order
4. Clone each reel structure
5. Generate new reel UUIDs
6. Preserve original asset UUIDs
7. Write unified CPL XML

**Key Principle:** No media transcoding, only metadata stitching

### 5. DCP Generator (`dcp_generator.py`)

**Purpose:** Generate complete DCP package structure

**Output Files:**

**CPL.xml:** Unified composition playlist

**PKL.xml (Packing List):**
- List of all assets
- SHA-1 hashes
- File sizes
- Asset types

**ASSETMAP.xml:**
- Complete package inventory
- File paths
- Chunk information
- PKL reference

### 6. Compiler (`compiler.py`)

**Purpose:** Main orchestrator for pod compilation

**Workflow:**
1. Parse all CPL files
2. Validate inputs and compatibility
3. Generate pod identity
4. Stitch CPLs into unified composition
5. Generate DCP package
6. Report results

### 7. CLI (`cli.py`)

**Purpose:** Command-line interface

**Commands:**
- `compile`: Compile ad pod from CPLs
- `validate`: Validate date format

### 8. Web Interface (`web.py` + `templates/index.html`)

**Purpose:** Browser-based UI for pod compilation

**Features:**
- Form-based input for pod parameters
- Drag-and-drop CPL upload (ordered)
- Real-time validation
- Compilation results display

## Data Flow

```
Input CPLs → Parser → Validator → Pod Identity
                                      ↓
                                  Stitcher
                                      ↓
                              DCP Generator
                                      ↓
                            Output Package
```

## Key Design Decisions

### 1. Metadata-Only Stitching
- **Why:** Avoids expensive transcoding
- **How:** Clone XML reel structures, preserve asset UUIDs
- **Benefit:** Fast, deterministic, no quality loss

### 2. Deterministic Pod IDs
- **Why:** Enable idempotent generation
- **How:** Hash of all inputs (excluding timestamp)
- **Benefit:** Same inputs always produce same pod

### 3. Upstream Enforcement
- **Why:** Remove theatre-side execution risk
- **How:** Single CPL = locked playback order
- **Benefit:** Guaranteed ad sequence

### 4. Unencrypted Assets Only
- **Why:** Eliminate KDM complexity
- **How:** Validation rejects encrypted CPLs
- **Benefit:** Simplified operations, no key management

### 5. Weekly Cadence
- **Why:** Balance freshness with operational overhead
- **How:** Start date parameter for scheduling
- **Benefit:** Predictable batch processing

## Validation Strategy

### Hard Failures (Stop Compilation)
- Encrypted content
- EditRate mismatch
- Aspect ratio mismatch
- Invalid input parameters
- Missing required fields

### Warnings (Allow Compilation)
- Audio layout differences
- Missing optional metadata
- Asset repository warnings

## Scale Characteristics

**For 1,500 theatres:**
- 1,500 pods per week
- ~214 pods per day
- Batch processing friendly
- No KDM generation overhead

**Storage:**
- Each pod: ~10KB (XML only, no MXFs)
- Weekly: ~15MB for metadata
- MXFs shared across pods (deduplicated)

## Security Considerations

1. **No Encryption:** Ads are unencrypted (by design)
2. **Asset Integrity:** SHA-1 hashes in PKL
3. **Input Validation:** Strict parameter validation
4. **XML Security:** Standard XML parsing (no external entities)

## Extension Points

### Future Enhancements
1. **Asset Repository Integration:** Copy/link MXF files
2. **Batch Processing:** Multi-pod generation
3. **Version Control:** Track pod revisions
4. **Distribution Integration:** Push to CDN/theatres
5. **Proof-of-Play Integration:** Playback verification
6. **Analytics:** Compilation metrics and monitoring

## Error Handling

### Parse Errors
- Invalid XML structure
- Missing required elements
- Namespace issues

### Validation Errors
- Incompatible CPLs
- Invalid parameters
- Missing assets

### Generation Errors
- File I/O failures
- Permission issues
- Disk space

All errors include:
- Clear error messages
- Context about failure
- Suggestions for resolution

## Testing Strategy

### Unit Tests
- CPL parsing (various namespaces)
- Validation rules (all cases)
- Pod identity generation (determinism)
- Stitching logic (structure preservation)

### Integration Tests
- End-to-end compilation
- Multi-CPL scenarios
- Error handling paths

### Example-Based Testing
- Real-world CPL formats
- Edge cases (1 CPL, 20 CPLs)
- Various aspect ratios and edit rates
