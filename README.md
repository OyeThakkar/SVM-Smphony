# SVN-Symphony: Weekly Per-Theatre Ad Pod Compiler

Screenvision Media's deterministic ad pod compiler that enforces playback order at the DCP media layer using physical CPL stitching.

## Overview

This system replaces theatre-side ad assembly with upstream-controlled, deterministic ad pod generation. It stitches individual ad CPLs into unified compositions, guaranteeing playback order and eliminating downstream execution risk.

## Problem Statement

Current ad delivery uses individual DCPs assembled by theatre automation, leading to:
- Non-guaranteed playback order
- Revenue and compliance risks
- Complex proof-of-play reconciliation
- Limited upstream enforcement

## Solution

**Physical CPL Stitching:** Combine multiple ad CPLs into a single, ordered CPL per theatre per week.

### Key Features

- ✅ Guaranteed playback order (locked at media layer)
- ✅ Atomic scheduling (one composition per theatre)
- ✅ Clean proof-of-play tracking
- ✅ No encryption/KDM overhead
- ✅ Deterministic & idempotent generation
- ✅ Upstream execution control

## Architecture

### Inputs
- Theatre Name
- Rating (G / PG / PG-13 / R)
- Section (LPS / EPS)
- Aspect (Flat / Scope)
- Start Date (dd-mmm-yyyy)
- Ordered CPL XML files (up to 20)

### Pod Naming Format
```
<THEATERID>_<RATING>_<SECTION>_<ASPECT>_<dd-mmm-yyyy>
```
Example: `T1042_PG13_LPS_FLAT_06-Feb-2026`

### Output Structure
```
<PodName>/
├── ASSETMAP.xml
├── PKL.xml
├── CPL.xml
└── [Referenced MXF files]
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python -m pod_compiler.cli compile \
  --theatre "T1042" \
  --rating "PG-13" \
  --section "LPS" \
  --aspect "Flat" \
  --start-date "06-Feb-2026" \
  --cpls ad1.xml ad2.xml ad3.xml ad4.xml
```

### Web Interface

```bash
python -m pod_compiler.web
```

Then navigate to `http://localhost:5000`

## Validation

The system validates:
- ✓ All assets exist in central repository
- ✓ No encryption (all ads must be unencrypted)
- ✓ Consistent EditRate across all CPLs
- ✓ Consistent container aspect (Flat/Scope)
- ✓ Consistent audio configuration
- ✓ No duplicate assets

## Pod Identity

Pod ID is deterministically generated from:
- Theatre ID
- Rating
- Section
- Aspect
- Start Date
- Ordered CPL UUIDs

**Same inputs → Same pod** (idempotent creation)

## Technical Details

### CPL Stitching Process

1. Parse each input CPL XML
2. Extract reel structures
3. Validate compatibility
4. Clone reels into new unified CPL
5. Assign new reel UUIDs
6. Preserve original asset UUID references

**No media transcoding. No MXF modification. Pure metadata stitching.**

### DCP Package Generation

- New CPL with SHA-1 hashes of all assets
- PKL referencing all MXFs, CPL, and PKL
- AssetMap with complete package inventory

## Scale Characteristics

For 1,500 theatres:
- 1,500 pods per week
- No KDM generation (unencrypted ads)
- Fully deterministic workflow
- Predictable batch processing

## License

MIT License - see LICENSE file
