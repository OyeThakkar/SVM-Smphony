#!/usr/bin/env python3
"""
Integration test script for SVN-Symphony Pod Compiler

Tests the complete workflow from CPL parsing to DCP package generation.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pod_compiler.cpl_parser import parse_cpl, CPLParseError
from pod_compiler.validator import CPLValidator, ValidationError
from pod_compiler.pod_identity import PodIdentity
from pod_compiler.compiler import PodCompiler


def test_cpl_parsing():
    """Test CPL parsing functionality"""
    print("Testing CPL parsing...")
    
    # Test with example CPL
    cpl_file = "examples/ad1_cpl.xml"
    if not os.path.exists(cpl_file):
        print(f"  ⚠ Skipping (file not found: {cpl_file})")
        return True
    
    try:
        cpl_data = parse_cpl(cpl_file)
        
        # Verify required fields
        assert cpl_data['cpl_uuid'], "CPL UUID is missing"
        assert cpl_data['edit_rate'], "EditRate is missing"
        assert cpl_data['reels'], "No reels found"
        assert not cpl_data['encrypted'], "CPL should not be encrypted"
        
        print(f"  ✓ Parsed CPL: {cpl_data['cpl_uuid']}")
        print(f"  ✓ Edit Rate: {cpl_data['edit_rate']}")
        print(f"  ✓ Aspect: {cpl_data['aspect_ratio']}")
        print(f"  ✓ Reels: {len(cpl_data['reels'])}")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_validation():
    """Test validation functionality"""
    print("\nTesting validation...")
    
    # Test date validation
    assert PodIdentity.validate_date_format("06-Feb-2026"), "Valid date failed"
    assert not PodIdentity.validate_date_format("2026-02-06"), "Invalid date passed"
    print("  ✓ Date validation working")
    
    # Test pod name generation
    pod_name = PodIdentity.generate_pod_name(
        "T1042", "PG-13", "LPS", "Flat", "06-Feb-2026"
    )
    assert pod_name == "T1042_PG13_LPS_FLAT_06-Feb-2026", f"Wrong pod name: {pod_name}"
    print(f"  ✓ Pod name generation: {pod_name}")
    
    # Test deterministic pod ID
    cpl_uuids = ["uuid1", "uuid2"]
    pod_id_1 = PodIdentity.generate_pod_id(
        "T1042", "PG-13", "LPS", "Flat", "06-Feb-2026", cpl_uuids
    )
    pod_id_2 = PodIdentity.generate_pod_id(
        "T1042", "PG-13", "LPS", "Flat", "06-Feb-2026", cpl_uuids
    )
    assert pod_id_1 == pod_id_2, "Pod IDs should be deterministic"
    print("  ✓ Deterministic pod ID generation working")
    
    return True


def test_cross_cpl_validation():
    """Test cross-CPL validation"""
    print("\nTesting cross-CPL validation...")
    
    cpl_files = ["examples/ad1_cpl.xml", "examples/ad2_cpl.xml"]
    
    # Check if files exist
    if not all(os.path.exists(f) for f in cpl_files):
        print("  ⚠ Skipping (example files not found)")
        return True
    
    try:
        # Parse CPLs
        cpl_data_list = [parse_cpl(f) for f in cpl_files]
        
        # Validate
        validator = CPLValidator()
        warnings = validator.validate_cross_cpl_compatibility(cpl_data_list)
        
        print("  ✓ Cross-CPL validation completed")
        if warnings:
            print(f"  ⚠ Warnings: {len(warnings)}")
        
        return True
    except ValidationError as e:
        print(f"  ✗ Validation failed: {e}")
        return False


def test_full_compilation():
    """Test complete pod compilation"""
    print("\nTesting full compilation...")
    
    cpl_files = [
        "examples/ad1_cpl.xml",
        "examples/ad2_cpl.xml",
        "examples/ad3_cpl.xml",
        "examples/ad4_cpl.xml"
    ]
    
    # Check if files exist
    if not all(os.path.exists(f) for f in cpl_files):
        print("  ⚠ Skipping (example files not found)")
        return True
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            compiler = PodCompiler()
            result = compiler.compile_pod(
                theatre_id="TEST001",
                rating="PG-13",
                section="LPS",
                aspect="Flat",
                start_date="01-Jan-2026",
                cpl_files=cpl_files,
                output_dir=temp_dir
            )
            
            # Verify result
            assert result['success'], "Compilation failed"
            assert result['cpl_count'] == 4, "Wrong CPL count"
            assert result['pod_name'] == "TEST001_PG13_LPS_FLAT_01-Jan-2026"
            
            # Verify output files exist
            pod_dir = Path(result['output_dir'])
            assert (pod_dir / 'CPL.xml').exists(), "CPL.xml not generated"
            assert (pod_dir / 'PKL.xml').exists(), "PKL.xml not generated"
            assert (pod_dir / 'ASSETMAP.xml').exists(), "ASSETMAP.xml not generated"
            
            print(f"  ✓ Compilation successful")
            print(f"  ✓ Pod: {result['pod_name']}")
            print(f"  ✓ CPLs: {result['cpl_count']}")
            print(f"  ✓ Assets: {result['asset_count']}")
            print(f"  ✓ Output files verified")
            
            return True
        except Exception as e:
            print(f"  ✗ Compilation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("SVN-Symphony Integration Tests")
    print("=" * 70)
    
    tests = [
        ("CPL Parsing", test_cpl_parsing),
        ("Validation", test_validation),
        ("Cross-CPL Validation", test_cross_cpl_validation),
        ("Full Compilation", test_full_compilation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
