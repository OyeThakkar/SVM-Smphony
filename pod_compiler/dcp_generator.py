"""
DCP Package Generator Module

Generates complete DCP package structure:
- ASSETMAP.xml: References all files in the package
- PKL.xml: Packing list with asset hashes
- CPL.xml: Composition playlist (stitched)
- References to MXF files

Creates a valid DCP directory structure.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import uuid
from datetime import datetime


class DCPPackageGenerator:
    """Generates DCP package with ASSETMAP, PKL, and CPL"""
    
    # Namespaces
    ASSETMAP_NS = 'http://www.smpte-ra.org/schemas/429-9/2007/AM'
    PKL_NS = 'http://www.smpte-ra.org/schemas/2067-2/2016'
    
    def __init__(self, pod_name: str, output_dir: str):
        """
        Initialize DCP package generator
        
        Args:
            pod_name: Name of the pod
            output_dir: Directory to create DCP package in
        """
        self.pod_name = pod_name
        self.output_dir = Path(output_dir)
        self.assets = []
        
    def generate_package(
        self,
        cpl_path: str,
        cpl_uuid: str,
        asset_uuids: List[str],
        asset_repository: Optional[str] = None
    ):
        """
        Generate complete DCP package
        
        Args:
            cpl_path: Path to the stitched CPL file
            cpl_uuid: UUID of the CPL
            asset_uuids: List of asset UUIDs referenced in CPL
            asset_repository: Optional path to asset repository
        """
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect all assets
        self._collect_assets(cpl_path, cpl_uuid, asset_uuids, asset_repository)
        
        # Generate PKL
        pkl_uuid = str(uuid.uuid4())
        pkl_path = self.output_dir / 'PKL.xml'
        self._generate_pkl(pkl_path, pkl_uuid)
        
        # Generate ASSETMAP
        assetmap_uuid = str(uuid.uuid4())
        assetmap_path = self.output_dir / 'ASSETMAP.xml'
        self._generate_assetmap(assetmap_path, assetmap_uuid, pkl_uuid)
        
        return {
            'output_dir': str(self.output_dir),
            'cpl_path': str(self.output_dir / 'CPL.xml'),
            'pkl_path': str(pkl_path),
            'assetmap_path': str(assetmap_path),
            'assets': self.assets
        }
    
    def _collect_assets(
        self,
        cpl_path: str,
        cpl_uuid: str,
        asset_uuids: List[str],
        asset_repository: Optional[str]
    ):
        """Collect information about all assets in the package"""
        # Add CPL as an asset
        cpl_file_path = Path(cpl_path)
        self.assets.append({
            'id': cpl_uuid,
            'type': 'text/xml',
            'path': 'CPL.xml',
            'size': cpl_file_path.stat().st_size if cpl_file_path.exists() else 0,
            'hash': self._calculate_hash(cpl_path) if cpl_file_path.exists() else None
        })
        
        # Add MXF assets
        # Note: In a real implementation, we would copy or reference MXF files
        # For now, we'll just record their metadata
        if asset_repository:
            repo_path = Path(asset_repository)
            for asset_uuid in asset_uuids:
                # Try to find the MXF file
                mxf_files = list(repo_path.glob(f'{asset_uuid}*.mxf'))
                if mxf_files:
                    mxf_file = mxf_files[0]
                    self.assets.append({
                        'id': asset_uuid,
                        'type': 'application/mxf',
                        'path': mxf_file.name,
                        'size': mxf_file.stat().st_size,
                        'hash': self._calculate_hash(str(mxf_file))
                    })
                else:
                    # Asset not found, add placeholder
                    self.assets.append({
                        'id': asset_uuid,
                        'type': 'application/mxf',
                        'path': f'{asset_uuid}.mxf',
                        'size': 0,
                        'hash': None
                    })
    
    def _calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-1 hash of a file"""
        try:
            sha1 = hashlib.sha1()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha1.update(chunk)
            return sha1.hexdigest()
        except Exception:
            return None
    
    def _generate_pkl(self, pkl_path: Path, pkl_uuid: str):
        """Generate PKL (Packing List) XML"""
        root = ET.Element(
            f'{{{self.PKL_NS}}}PackingList',
            attrib={'xmlns': self.PKL_NS}
        )
        
        # ID
        id_elem = ET.SubElement(root, f'{{{self.PKL_NS}}}Id')
        id_elem.text = f'urn:uuid:{pkl_uuid}'
        
        # Annotation
        annotation = ET.SubElement(root, f'{{{self.PKL_NS}}}Annotation')
        annotation.text = f'Packing List for {self.pod_name}'
        
        # Issue Date
        issue_date = ET.SubElement(root, f'{{{self.PKL_NS}}}IssueDate')
        issue_date.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Issuer
        issuer = ET.SubElement(root, f'{{{self.PKL_NS}}}Issuer')
        issuer.text = 'SVN-Symphony'
        
        # Creator
        creator = ET.SubElement(root, f'{{{self.PKL_NS}}}Creator')
        creator.text = 'SVN-Symphony v1.0'
        
        # Asset List
        asset_list = ET.SubElement(root, f'{{{self.PKL_NS}}}AssetList')
        
        for asset in self.assets:
            asset_elem = ET.SubElement(asset_list, f'{{{self.PKL_NS}}}Asset')
            
            # Asset ID
            asset_id = ET.SubElement(asset_elem, f'{{{self.PKL_NS}}}Id')
            asset_id.text = f'urn:uuid:{asset["id"]}'
            
            # Type
            asset_type = ET.SubElement(asset_elem, f'{{{self.PKL_NS}}}Type')
            asset_type.text = asset['type']
            
            # Original File Name
            orig_name = ET.SubElement(asset_elem, f'{{{self.PKL_NS}}}OriginalFileName')
            orig_name.text = asset['path']
            
            # Size
            size_elem = ET.SubElement(asset_elem, f'{{{self.PKL_NS}}}Size')
            size_elem.text = str(asset['size'])
            
            # Hash
            if asset['hash']:
                hash_elem = ET.SubElement(
                    asset_elem,
                    f'{{{self.PKL_NS}}}Hash',
                    attrib={'Algorithm': 'http://www.w3.org/2000/09/xmldsig#sha1'}
                )
                hash_elem.text = asset['hash']
        
        # Write PKL
        ET.register_namespace('', self.PKL_NS)
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(pkl_path, encoding='utf-8', xml_declaration=True, method='xml')
        
        # Add PKL itself to assets for ASSETMAP
        self.assets.append({
            'id': pkl_uuid,
            'type': 'text/xml',
            'path': 'PKL.xml',
            'size': pkl_path.stat().st_size,
            'hash': self._calculate_hash(str(pkl_path))
        })
    
    def _generate_assetmap(self, assetmap_path: Path, assetmap_uuid: str, pkl_uuid: str):
        """Generate ASSETMAP XML"""
        root = ET.Element(
            f'{{{self.ASSETMAP_NS}}}AssetMap',
            attrib={'xmlns': self.ASSETMAP_NS}
        )
        
        # ID
        id_elem = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}Id')
        id_elem.text = f'urn:uuid:{assetmap_uuid}'
        
        # Annotation
        annotation = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}Annotation')
        annotation.text = f'Asset Map for {self.pod_name}'
        
        # Creator
        creator = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}Creator')
        creator.text = 'SVN-Symphony v1.0'
        
        # Volume Count
        vol_count = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}VolumeCount')
        vol_count.text = '1'
        
        # Issue Date
        issue_date = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}IssueDate')
        issue_date.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Issuer
        issuer = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}Issuer')
        issuer.text = 'SVN-Symphony'
        
        # Asset List
        asset_list = ET.SubElement(root, f'{{{self.ASSETMAP_NS}}}AssetList')
        
        for asset in self.assets:
            asset_elem = ET.SubElement(asset_list, f'{{{self.ASSETMAP_NS}}}Asset')
            
            # Asset ID
            asset_id = ET.SubElement(asset_elem, f'{{{self.ASSETMAP_NS}}}Id')
            asset_id.text = f'urn:uuid:{asset["id"]}'
            
            # Packing List (only for PKL)
            if asset['id'] == pkl_uuid:
                is_pkl = ET.SubElement(asset_elem, f'{{{self.ASSETMAP_NS}}}PackingList')
                is_pkl.text = 'true'
            
            # Chunk List
            chunk_list = ET.SubElement(asset_elem, f'{{{self.ASSETMAP_NS}}}ChunkList')
            chunk = ET.SubElement(chunk_list, f'{{{self.ASSETMAP_NS}}}Chunk')
            
            # Path
            path_elem = ET.SubElement(chunk, f'{{{self.ASSETMAP_NS}}}Path')
            path_elem.text = asset['path']
            
            # Volume Index
            vol_idx = ET.SubElement(chunk, f'{{{self.ASSETMAP_NS}}}VolumeIndex')
            vol_idx.text = '1'
            
            # Offset
            offset = ET.SubElement(chunk, f'{{{self.ASSETMAP_NS}}}Offset')
            offset.text = '0'
            
            # Length
            length = ET.SubElement(chunk, f'{{{self.ASSETMAP_NS}}}Length')
            length.text = str(asset['size'])
        
        # Write ASSETMAP
        ET.register_namespace('', self.ASSETMAP_NS)
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(assetmap_path, encoding='utf-8', xml_declaration=True, method='xml')


def generate_dcp_package(
    pod_name: str,
    output_dir: str,
    cpl_path: str,
    cpl_uuid: str,
    asset_uuids: List[str],
    asset_repository: Optional[str] = None
) -> Dict:
    """
    Convenience function to generate DCP package
    
    Args:
        pod_name: Pod name
        output_dir: Output directory
        cpl_path: Path to CPL file
        cpl_uuid: CPL UUID
        asset_uuids: List of asset UUIDs
        asset_repository: Optional asset repository path
        
    Returns:
        Dictionary with package information
    """
    generator = DCPPackageGenerator(pod_name, output_dir)
    return generator.generate_package(cpl_path, cpl_uuid, asset_uuids, asset_repository)
