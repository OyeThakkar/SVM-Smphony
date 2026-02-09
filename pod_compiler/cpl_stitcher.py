"""
CPL Stitcher Module

Stitches multiple ad CPLs into a single unified CPL:
- Extracts reels from source CPLs
- Clones reel structures
- Assigns new reel UUIDs
- Preserves asset UUID references
- Generates new unified CPL

No media transcoding. No MXF modification. Pure metadata stitching.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict
import uuid
from datetime import datetime


class CPLStitcher:
    """Stitches multiple CPLs into one unified CPL"""
    
    # SMPTE CPL namespace
    NAMESPACE = 'http://www.smpte-ra.org/schemas/2067-3/2016'
    CC_NAMESPACE = 'http://www.smpte-ra.org/schemas/2067-2/2016'
    
    def __init__(self, pod_name: str, pod_id: str):
        """
        Initialize stitcher
        
        Args:
            pod_name: Name for the new pod CPL
            pod_id: Unique identifier for the pod
        """
        self.pod_name = pod_name
        self.pod_id = pod_id
        
    def stitch_cpls(self, cpl_data_list: List[Dict]) -> ET.Element:
        """
        Stitch multiple CPLs into one unified CPL
        
        Args:
            cpl_data_list: List of parsed CPL data dictionaries
            
        Returns:
            XML Element representing the new unified CPL
        """
        if not cpl_data_list:
            raise ValueError("No CPLs provided for stitching")
        
        # Create new CPL root element
        cpl_root = self._create_cpl_root()
        
        # Add basic metadata
        self._add_cpl_metadata(cpl_root, cpl_data_list[0])
        
        # Create reel list
        reel_list = ET.SubElement(cpl_root, f'{{{self.NAMESPACE}}}ReelList')
        
        # Stitch reels from all CPLs in order
        for cpl_data in cpl_data_list:
            for reel in cpl_data['reels']:
                self._add_reel_to_list(reel_list, reel, cpl_data)
        
        return cpl_root
    
    def _create_cpl_root(self) -> ET.Element:
        """Create CPL root element with namespaces"""
        root = ET.Element(
            f'{{{self.NAMESPACE}}}CompositionPlaylist',
            attrib={
                'xmlns': self.NAMESPACE,
                f'{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation': 
                    f'{self.NAMESPACE} CPL.xsd'
            }
        )
        return root
    
    def _add_cpl_metadata(self, root: ET.Element, reference_cpl: Dict):
        """Add CPL metadata (ID, title, dates, etc.)"""
        # ID
        id_elem = ET.SubElement(root, f'{{{self.NAMESPACE}}}Id')
        id_elem.text = f'urn:uuid:{self.pod_id}'
        
        # Content Title
        title_elem = ET.SubElement(root, f'{{{self.NAMESPACE}}}ContentTitle')
        title_elem.text = self.pod_name
        
        # Annotation
        annotation_elem = ET.SubElement(root, f'{{{self.NAMESPACE}}}Annotation')
        annotation_elem.text = f'Ad Pod: {self.pod_name}'
        
        # Issue Date (current time)
        issue_date = ET.SubElement(root, f'{{{self.NAMESPACE}}}IssueDate')
        issue_date.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Issuer
        issuer = ET.SubElement(root, f'{{{self.NAMESPACE}}}Issuer')
        issuer.text = 'SVN-Symphony Ad Pod Compiler'
        
        # Creator
        creator = ET.SubElement(root, f'{{{self.NAMESPACE}}}Creator')
        creator.text = 'SVN-Symphony v1.0'
        
        # Content Kind
        content_kind = ET.SubElement(root, f'{{{self.NAMESPACE}}}ContentKind')
        content_kind.text = 'advertisement'
        
        # Edit Rate (from reference CPL)
        if reference_cpl.get('edit_rate'):
            edit_rate = ET.SubElement(root, f'{{{self.NAMESPACE}}}EditRate')
            edit_rate.text = reference_cpl['edit_rate']
    
    def _add_reel_to_list(
        self, 
        reel_list: ET.Element, 
        reel_data: Dict,
        cpl_data: Dict
    ):
        """
        Add a reel to the unified CPL
        
        Args:
            reel_list: ReelList element to add to
            reel_data: Reel data from parsed CPL
            cpl_data: Full CPL data for reference
        """
        # Create new reel element
        reel = ET.SubElement(reel_list, f'{{{self.NAMESPACE}}}Reel')
        
        # Generate new reel UUID
        new_reel_id = str(uuid.uuid4())
        reel_id_elem = ET.SubElement(reel, f'{{{self.NAMESPACE}}}Id')
        reel_id_elem.text = f'urn:uuid:{new_reel_id}'
        
        # Copy assets from source reel, preserving their UUIDs
        for asset in reel_data['assets']:
            self._clone_asset(reel, asset, cpl_data)
    
    def _clone_asset(
        self, 
        reel: ET.Element, 
        asset: Dict,
        cpl_data: Dict
    ):
        """
        Clone an asset reference into the new reel
        
        Args:
            reel: Reel element to add asset to
            asset: Asset data with UUID and type
            cpl_data: Full CPL data for reference
        """
        asset_type = asset['type']
        asset_uuid = asset['uuid']
        
        # Create asset element based on type
        asset_elem = ET.SubElement(reel, f'{{{self.NAMESPACE}}}{asset_type}')
        
        # Add asset ID (preserve original UUID)
        id_elem = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}Id')
        id_elem.text = f'urn:uuid:{asset_uuid}'
        
        # Add basic metadata
        # EditRate
        if cpl_data.get('edit_rate'):
            edit_rate = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}EditRate')
            edit_rate.text = cpl_data['edit_rate']
        
        # IntrinsicDuration (placeholder - would need from source)
        intrinsic = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}IntrinsicDuration')
        intrinsic.text = '0'
        
        # EntryPoint
        entry_point = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}EntryPoint')
        entry_point.text = '0'
        
        # Duration (placeholder - would need from source)
        duration = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}Duration')
        duration.text = '0'
        
        # ScreenAspectRatio (for picture)
        if asset_type == 'MainPicture' and cpl_data.get('aspect_ratio'):
            aspect = ET.SubElement(asset_elem, f'{{{self.NAMESPACE}}}ScreenAspectRatio')
            # Convert Flat/Scope to ratio
            if cpl_data['aspect_ratio'] == 'Flat':
                aspect.text = '1.85'
            elif cpl_data['aspect_ratio'] == 'Scope':
                aspect.text = '2.39'
            else:
                aspect.text = cpl_data['aspect_ratio']
    
    def write_cpl(self, cpl_root: ET.Element, output_path: str):
        """
        Write CPL to XML file
        
        Args:
            cpl_root: CPL root element
            output_path: Path to write CPL XML file
        """
        # Register namespaces for pretty output
        ET.register_namespace('', self.NAMESPACE)
        ET.register_namespace('cc', self.CC_NAMESPACE)
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
        # Create tree and write
        tree = ET.ElementTree(cpl_root)
        ET.indent(tree, space='  ')
        tree.write(
            output_path,
            encoding='utf-8',
            xml_declaration=True,
            method='xml'
        )
    
    def stitch_and_write(
        self, 
        cpl_data_list: List[Dict], 
        output_path: str
    ) -> str:
        """
        Convenience method to stitch CPLs and write to file
        
        Args:
            cpl_data_list: List of parsed CPL data
            output_path: Path to write output CPL
            
        Returns:
            Pod ID (UUID) of the generated CPL
        """
        cpl_root = self.stitch_cpls(cpl_data_list)
        self.write_cpl(cpl_root, output_path)
        return self.pod_id


def stitch_cpls(
    pod_name: str,
    pod_id: str,
    cpl_data_list: List[Dict],
    output_path: str
) -> str:
    """
    Convenience function to stitch CPLs
    
    Args:
        pod_name: Name for the pod
        pod_id: Unique pod identifier
        cpl_data_list: List of parsed CPL data
        output_path: Path to write output CPL
        
    Returns:
        Pod ID
    """
    stitcher = CPLStitcher(pod_name, pod_id)
    return stitcher.stitch_and_write(cpl_data_list, output_path)
