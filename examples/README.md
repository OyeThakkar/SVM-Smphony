# Example Usage

This directory contains example CPL files for testing the ad pod compiler.

## Quick Test

Run the following command from the repository root:

```bash
python -m pod_compiler.cli compile \
  --theatre T1042 \
  --rating PG-13 \
  --section LPS \
  --aspect Flat \
  --start-date 06-Feb-2026 \
  --cpls examples/ad1_cpl.xml examples/ad2_cpl.xml examples/ad3_cpl.xml examples/ad4_cpl.xml \
  --output ./output
```

## Expected Output

This will create a pod directory:

```
output/T1042_PG13_LPS_FLAT_06-Feb-2026/
├── ASSETMAP.xml
├── PKL.xml
└── CPL.xml
```

## Example CPL Files

- **ad1_cpl.xml**: Product Launch ad (30 seconds, 720 frames @ 24fps)
- **ad2_cpl.xml**: Brand Awareness ad (20 seconds, 480 frames @ 24fps)
- **ad3_cpl.xml**: Holiday Special ad (25 seconds, 600 frames @ 24fps)
- **ad4_cpl.xml**: Coming Soon ad (22.5 seconds, 540 frames @ 24fps)

All example ads use:
- 24 fps edit rate
- Flat (1.85) aspect ratio
- Unencrypted content
- Single reel with picture and sound

## Pod Identity

For these inputs, the compiler will generate:

**Pod Name:** `T1042_PG13_LPS_FLAT_06-Feb-2026`

**Pod ID:** Deterministic hash of:
- Theatre: T1042
- Rating: PG-13
- Section: LPS
- Aspect: Flat
- Start Date: 06-Feb-2026
- Ordered CPL UUIDs

## Validation

The compiler will validate:
- ✓ All CPLs use 24 fps edit rate (compatible)
- ✓ All CPLs use Flat (1.85) aspect ratio (compatible)
- ✓ No CPLs are encrypted
- ✓ All CPLs have valid structure

## Web Interface Test

You can also test via the web interface:

```bash
python -m pod_compiler.web
```

Then navigate to http://localhost:5000 and upload the example CPL files in order.
