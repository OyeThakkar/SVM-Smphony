"""
Pod Compiler Module

Main orchestrator for ad pod compilation:
1. Parse CPL files
2. Validate compatibility
3. Generate pod identity
4. Stitch CPLs
5. Generate DCP package
"""

from pathlib import Path
from typing import List, Dict, Optional
import shutil

from .cpl_parser import parse_cpl, CPLParseError
from .validator import CPLValidator, ValidationError
from .pod_identity import PodIdentity
from .cpl_stitcher import CPLStitcher
from .dcp_generator import DCPPackageGenerator


class PodCompilerError(Exception):
    """Raised when pod compilation fails"""
    pass


class PodCompiler:
    """Main orchestrator for ad pod compilation"""
    
    def __init__(self, asset_repository: Optional[str] = None):
        """
        Initialize pod compiler
        
        Args:
            asset_repository: Optional path to central asset repository
        """
        self.asset_repository = asset_repository
        self.validator = CPLValidator(asset_repository)
        
    def compile_pod(
        self,
        theatre_id: str,
        rating: str,
        section: str,
        aspect: str,
        start_date: str,
        cpl_files: List[str],
        output_dir: str
    ) -> Dict:
        """
        Compile an ad pod from multiple CPL files
        
        Args:
            theatre_id: Theatre identifier (e.g., "T1042")
            rating: Content rating (G/PG/PG-13/R)
            section: Section (LPS/EPS)
            aspect: Aspect ratio (Flat/Scope)
            start_date: Start date in dd-mmm-yyyy format
            cpl_files: Ordered list of CPL file paths (up to 20)
            output_dir: Directory to create pod package in
            
        Returns:
            Dictionary with compilation results
            
        Raises:
            PodCompilerError: If compilation fails
        """
        # Step 1: Parse all CPL files
        print(f"Parsing {len(cpl_files)} CPL files...")
        cpl_data_list = []
        for i, cpl_file in enumerate(cpl_files, start=1):
            try:
                cpl_data = parse_cpl(cpl_file)
                cpl_data['source_file'] = cpl_file
                cpl_data_list.append(cpl_data)
                print(f"  [{i}/{len(cpl_files)}] Parsed: {Path(cpl_file).name}")
            except CPLParseError as e:
                raise PodCompilerError(f"Failed to parse {cpl_file}: {e}")
        
        # Step 2: Validate inputs
        print("\nValidating inputs...")
        validation_result = self.validator.validate_pod_inputs(
            theatre_id, rating, section, aspect, start_date, cpl_data_list
        )
        
        if not validation_result['valid']:
            error_msg = "Validation failed:\n" + "\n".join(
                f"  - {err}" for err in validation_result['errors']
            )
            raise PodCompilerError(error_msg)
        
        if validation_result['warnings']:
            print("Validation warnings:")
            for warning in validation_result['warnings']:
                print(f"  ⚠ {warning}")
        else:
            print("  ✓ All validations passed")
        
        # Step 3: Generate pod identity
        print("\nGenerating pod identity...")
        pod_name = PodIdentity.generate_pod_name(
            theatre_id, rating, section, aspect, start_date
        )
        
        cpl_uuids = [cpl['cpl_uuid'] for cpl in cpl_data_list]
        pod_id = PodIdentity.generate_pod_id(
            theatre_id, rating, section, aspect, start_date, cpl_uuids
        )
        
        print(f"  Pod Name: {pod_name}")
        print(f"  Pod ID: {pod_id}")
        
        # Step 4: Stitch CPLs
        print("\nStitching CPLs...")
        stitcher = CPLStitcher(pod_name, pod_id)
        cpl_root = stitcher.stitch_cpls(cpl_data_list)
        
        # Create output directory
        pod_output_dir = Path(output_dir) / pod_name
        pod_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write stitched CPL
        cpl_output_path = pod_output_dir / 'CPL.xml'
        stitcher.write_cpl(cpl_root, str(cpl_output_path))
        print(f"  ✓ Stitched CPL written to: {cpl_output_path}")
        
        # Step 5: Generate DCP package
        print("\nGenerating DCP package...")
        
        # Collect all asset UUIDs
        all_asset_uuids = []
        for cpl_data in cpl_data_list:
            for reel in cpl_data['reels']:
                for asset in reel['assets']:
                    all_asset_uuids.append(asset['uuid'])
        
        generator = DCPPackageGenerator(pod_name, str(pod_output_dir))
        package_info = generator.generate_package(
            str(cpl_output_path),
            pod_id,
            all_asset_uuids,
            self.asset_repository
        )
        
        print(f"  ✓ PKL written to: {package_info['pkl_path']}")
        print(f"  ✓ ASSETMAP written to: {package_info['assetmap_path']}")
        print(f"  ✓ Package contains {len(package_info['assets'])} assets")
        
        # Step 6: Summary
        print(f"\n{'='*60}")
        print(f"Pod compilation completed successfully!")
        print(f"{'='*60}")
        print(f"Pod Name:      {pod_name}")
        print(f"Pod ID:        {pod_id}")
        print(f"Output Dir:    {pod_output_dir}")
        print(f"CPL Count:     {len(cpl_data_list)}")
        print(f"Total Assets:  {len(all_asset_uuids)}")
        print(f"{'='*60}")
        
        return {
            'success': True,
            'pod_name': pod_name,
            'pod_id': pod_id,
            'output_dir': str(pod_output_dir),
            'cpl_count': len(cpl_data_list),
            'asset_count': len(all_asset_uuids),
            'validation_warnings': validation_result['warnings'],
            'package_info': package_info
        }
    
    def check_pod_exists(
        self,
        theatre_id: str,
        rating: str,
        section: str,
        aspect: str,
        start_date: str,
        cpl_uuids: List[str],
        output_dir: str
    ) -> bool:
        """
        Check if a pod with the same inputs already exists (idempotency check)
        
        Args:
            theatre_id: Theatre identifier
            rating: Content rating
            section: Section
            aspect: Aspect ratio
            start_date: Start date
            cpl_uuids: Ordered list of CPL UUIDs
            output_dir: Output directory to check
            
        Returns:
            True if pod already exists, False otherwise
        """
        pod_name = PodIdentity.generate_pod_name(
            theatre_id, rating, section, aspect, start_date
        )
        pod_dir = Path(output_dir) / pod_name
        
        # Check if directory exists and has required files
        if pod_dir.exists():
            required_files = ['CPL.xml', 'PKL.xml', 'ASSETMAP.xml']
            if all((pod_dir / f).exists() for f in required_files):
                return True
        
        return False


def compile_pod(
    theatre_id: str,
    rating: str,
    section: str,
    aspect: str,
    start_date: str,
    cpl_files: List[str],
    output_dir: str,
    asset_repository: Optional[str] = None
) -> Dict:
    """
    Convenience function to compile a pod
    
    Args:
        theatre_id: Theatre identifier
        rating: Content rating
        section: Section (LPS/EPS)
        aspect: Aspect ratio (Flat/Scope)
        start_date: Start date
        cpl_files: List of CPL file paths
        output_dir: Output directory
        asset_repository: Optional asset repository path
        
    Returns:
        Compilation results dictionary
    """
    compiler = PodCompiler(asset_repository)
    return compiler.compile_pod(
        theatre_id, rating, section, aspect, start_date,
        cpl_files, output_dir
    )
