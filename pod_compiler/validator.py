"""
Validator Module

Validates CPL files and cross-CPL compatibility for ad pod compilation:
- Individual CPL validation (encryption, assets)
- Cross-CPL validation (EditRate, Aspect, Audio)
- Asset existence checks
"""

from typing import List, Dict, Optional
from pathlib import Path


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class CPLValidator:
    """Validates CPL files and their compatibility"""
    
    def __init__(self, asset_repository_path: Optional[str] = None):
        """
        Initialize validator
        
        Args:
            asset_repository_path: Path to central asset repository (optional)
        """
        self.asset_repository_path = asset_repository_path
        
    def validate_individual_cpl(self, cpl_data: Dict) -> List[str]:
        """
        Validate a single CPL
        
        Args:
            cpl_data: Parsed CPL data dictionary
            
        Returns:
            List of validation warnings (empty if all OK)
            
        Raises:
            ValidationError: If critical validation fails
        """
        warnings = []
        
        # Check encryption
        if cpl_data.get('encrypted', False):
            raise ValidationError(
                f"CPL {cpl_data['cpl_uuid']} is encrypted. "
                "Only unencrypted ads are supported."
            )
        
        # Check for required fields
        if not cpl_data.get('cpl_uuid'):
            raise ValidationError("CPL UUID is missing")
        
        if not cpl_data.get('reels'):
            raise ValidationError(
                f"CPL {cpl_data['cpl_uuid']} has no reels"
            )
        
        # Check for assets
        if not any(reel.get('assets') for reel in cpl_data['reels']):
            raise ValidationError(
                f"CPL {cpl_data['cpl_uuid']} has no assets"
            )
        
        # Warn if missing metadata
        if not cpl_data.get('edit_rate'):
            warnings.append(
                f"CPL {cpl_data['cpl_uuid']}: EditRate not found"
            )
        
        if not cpl_data.get('aspect_ratio'):
            warnings.append(
                f"CPL {cpl_data['cpl_uuid']}: Aspect ratio not found"
            )
        
        return warnings
    
    def validate_cross_cpl_compatibility(self, cpl_data_list: List[Dict]) -> List[str]:
        """
        Validate compatibility across multiple CPLs
        
        Args:
            cpl_data_list: List of parsed CPL data dictionaries
            
        Returns:
            List of validation warnings
            
        Raises:
            ValidationError: If CPLs are incompatible
        """
        if not cpl_data_list:
            raise ValidationError("No CPLs provided for validation")
        
        if len(cpl_data_list) < 2:
            return []  # Single CPL, no cross-validation needed
        
        warnings = []
        
        # Get reference values from first CPL
        reference = cpl_data_list[0]
        ref_edit_rate = reference.get('edit_rate')
        ref_aspect = reference.get('aspect_ratio')
        ref_audio = reference.get('audio_layout')
        
        # Validate all CPLs against reference
        for i, cpl_data in enumerate(cpl_data_list[1:], start=2):
            cpl_uuid = cpl_data.get('cpl_uuid', f'CPL #{i}')
            
            # Check EditRate
            if ref_edit_rate and cpl_data.get('edit_rate'):
                if cpl_data['edit_rate'] != ref_edit_rate:
                    raise ValidationError(
                        f"EditRate mismatch: CPL {cpl_uuid} has "
                        f"'{cpl_data['edit_rate']}' but expected '{ref_edit_rate}'"
                    )
            
            # Check Aspect Ratio
            if ref_aspect and cpl_data.get('aspect_ratio'):
                if cpl_data['aspect_ratio'] != ref_aspect:
                    raise ValidationError(
                        f"Aspect ratio mismatch: CPL {cpl_uuid} has "
                        f"'{cpl_data['aspect_ratio']}' but expected '{ref_aspect}'"
                    )
            
            # Check Audio Layout (warning only, not critical)
            if ref_audio and cpl_data.get('audio_layout'):
                if cpl_data['audio_layout'] != ref_audio:
                    warnings.append(
                        f"Audio layout difference: CPL {cpl_uuid} has "
                        f"'{cpl_data['audio_layout']}' vs '{ref_audio}'"
                    )
        
        # Check for duplicate CPL UUIDs
        uuids = [cpl['cpl_uuid'] for cpl in cpl_data_list if cpl.get('cpl_uuid')]
        if len(uuids) != len(set(uuids)):
            raise ValidationError("Duplicate CPL UUIDs detected")
        
        # Check for duplicate asset UUIDs across CPLs
        all_asset_uuids = []
        for cpl_data in cpl_data_list:
            for reel in cpl_data.get('reels', []):
                for asset in reel.get('assets', []):
                    all_asset_uuids.append(asset['uuid'])
        
        if len(all_asset_uuids) != len(set(all_asset_uuids)):
            warnings.append(
                "Duplicate asset UUIDs detected across CPLs "
                "(same asset used in multiple ads)"
            )
        
        return warnings
    
    def validate_assets_exist(self, cpl_data_list: List[Dict]) -> List[str]:
        """
        Validate that all referenced assets exist in repository
        
        Args:
            cpl_data_list: List of parsed CPL data dictionaries
            
        Returns:
            List of missing assets (empty if all exist)
            
        Note:
            If no asset_repository_path is set, this check is skipped
        """
        if not self.asset_repository_path:
            return []  # Skip check if no repository configured
        
        repo_path = Path(self.asset_repository_path)
        if not repo_path.exists():
            return [f"Asset repository not found: {self.asset_repository_path}"]
        
        missing_assets = []
        
        for cpl_data in cpl_data_list:
            cpl_uuid = cpl_data.get('cpl_uuid', 'Unknown')
            
            for reel in cpl_data.get('reels', []):
                for asset in reel.get('assets', []):
                    asset_uuid = asset['uuid']
                    
                    # Check if asset file exists (MXF)
                    # Common patterns: <uuid>.mxf or <uuid>_*.mxf
                    asset_found = False
                    for pattern in [f"{asset_uuid}.mxf", f"{asset_uuid}_*.mxf"]:
                        if list(repo_path.glob(pattern)):
                            asset_found = True
                            break
                    
                    if not asset_found:
                        missing_assets.append(
                            f"CPL {cpl_uuid}: Asset {asset_uuid} not found"
                        )
        
        return missing_assets
    
    def validate_pod_inputs(
        self,
        theatre_id: str,
        rating: str,
        section: str,
        aspect: str,
        start_date: str,
        cpl_data_list: List[Dict]
    ) -> Dict:
        """
        Comprehensive validation of all pod inputs
        
        Args:
            theatre_id: Theatre identifier
            rating: Content rating
            section: Section (LPS/EPS)
            aspect: Aspect ratio (Flat/Scope)
            start_date: Start date
            cpl_data_list: List of parsed CPL data
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        # Validate input parameters
        if not theatre_id or not theatre_id.strip():
            errors.append("Theatre ID is required")
        
        valid_ratings = ['G', 'PG', 'PG-13', 'R']
        if rating not in valid_ratings:
            errors.append(
                f"Invalid rating '{rating}'. Must be one of: {', '.join(valid_ratings)}"
            )
        
        valid_sections = ['LPS', 'EPS']
        if section not in valid_sections:
            errors.append(
                f"Invalid section '{section}'. Must be one of: {', '.join(valid_sections)}"
            )
        
        valid_aspects = ['Flat', 'Scope']
        if aspect not in valid_aspects:
            errors.append(
                f"Invalid aspect '{aspect}'. Must be one of: {', '.join(valid_aspects)}"
            )
        
        if not cpl_data_list:
            errors.append("No CPL files provided")
        elif len(cpl_data_list) > 20:
            errors.append(
                f"Too many CPL files ({len(cpl_data_list)}). Maximum is 20."
            )
        
        # If basic validation failed, return early
        if errors:
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Validate individual CPLs
        try:
            for i, cpl_data in enumerate(cpl_data_list, start=1):
                indiv_warnings = self.validate_individual_cpl(cpl_data)
                warnings.extend(indiv_warnings)
        except ValidationError as e:
            errors.append(str(e))
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Validate cross-CPL compatibility
        try:
            cross_warnings = self.validate_cross_cpl_compatibility(cpl_data_list)
            warnings.extend(cross_warnings)
        except ValidationError as e:
            errors.append(str(e))
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Check for aspect ratio match
        cpl_aspects = [
            cpl.get('aspect_ratio') 
            for cpl in cpl_data_list 
            if cpl.get('aspect_ratio')
        ]
        if cpl_aspects and all(a == cpl_aspects[0] for a in cpl_aspects):
            if cpl_aspects[0] != aspect:
                warnings.append(
                    f"Requested aspect '{aspect}' differs from CPL aspect '{cpl_aspects[0]}'"
                )
        
        # Validate assets exist
        missing = self.validate_assets_exist(cpl_data_list)
        if missing:
            warnings.extend(missing)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
