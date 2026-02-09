"""
CPL Parser Module

Parses DCP CPL (Composition Playlist) XML files and extracts:
- CPL UUID
- EditRate
- Aspect Ratio
- Audio configuration
- Reel structure
- Asset UUIDs and references
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import uuid


class CPLParseError(Exception):
    """Raised when CPL parsing fails"""
    pass


class CPLParser:
    """Parser for DCP CPL XML files"""
    
    # Common DCP namespaces
    NAMESPACES = {
        'cpl': 'http://www.smpte-ra.org/schemas/2067-3/2016',
        'cc': 'http://www.smpte-ra.org/schemas/2067-2/2016',
        'cpl2013': 'http://www.smpte-ra.org/schemas/2067-3/2013',
        'cpl2': 'http://www.digicine.com/PROTO-ASDCP-CPL-20040511#',
    }
    
    def __init__(self, cpl_path: str):
        """
        Initialize parser with CPL file path
        
        Args:
            cpl_path: Path to CPL XML file
        """
        self.cpl_path = cpl_path
        self.tree = None
        self.root = None
        self.namespace = None
        
    def parse(self) -> Dict:
        """
        Parse the CPL file and extract all relevant information
        
        Returns:
            Dictionary containing CPL metadata and structure
            
        Raises:
            CPLParseError: If parsing fails
        """
        try:
            self.tree = ET.parse(self.cpl_path)
            self.root = self.tree.getroot()
            
            # Detect namespace
            self.namespace = self._detect_namespace()
            
            return {
                'cpl_uuid': self._extract_cpl_uuid(),
                'content_title': self._extract_content_title(),
                'edit_rate': self._extract_edit_rate(),
                'aspect_ratio': self._extract_aspect_ratio(),
                'audio_layout': self._extract_audio_layout(),
                'reels': self._extract_reels(),
                'encrypted': self._check_encryption(),
                'namespace': self.namespace,
            }
        except ET.ParseError as e:
            raise CPLParseError(f"Failed to parse CPL XML: {e}")
        except Exception as e:
            raise CPLParseError(f"Error parsing CPL: {e}")
    
    def _detect_namespace(self) -> str:
        """Detect which namespace the CPL uses"""
        tag = self.root.tag
        for prefix, uri in self.NAMESPACES.items():
            if uri in tag:
                return uri
        # No namespace or unknown namespace
        return ''
    
    def _get_element(self, path: str, parent=None):
        """Get element with namespace handling"""
        elem = parent if parent is not None else self.root
        
        if self.namespace:
            # Try with detected namespace
            ns_path = '/'.join([f'{{{self.namespace}}}{p}' for p in path.split('/')])
            result = elem.find(ns_path)
            if result is not None:
                return result
        
        # Try without namespace
        return elem.find(path)
    
    def _get_elements(self, path: str, parent=None):
        """Get elements with namespace handling"""
        elem = parent if parent is not None else self.root
        
        if self.namespace:
            # Try with detected namespace
            ns_path = '/'.join([f'{{{self.namespace}}}{p}' for p in path.split('/')])
            results = elem.findall(ns_path)
            if results:
                return results
        
        # Try without namespace
        return elem.findall(path)
    
    def _extract_cpl_uuid(self) -> str:
        """Extract CPL UUID"""
        id_elem = self._get_element('Id')
        if id_elem is not None and id_elem.text:
            # Clean up UUID format (remove urn:uuid: prefix if present)
            cpl_id = id_elem.text.strip()
            if cpl_id.startswith('urn:uuid:'):
                cpl_id = cpl_id[9:]
            return cpl_id
        raise CPLParseError("CPL UUID not found")
    
    def _extract_content_title(self) -> str:
        """Extract content title"""
        title_elem = self._get_element('ContentTitle')
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return "Untitled"
    
    def _extract_edit_rate(self) -> Optional[str]:
        """Extract edit rate from first reel"""
        reel_list = self._get_element('ReelList')
        if reel_list is not None:
            reel = self._get_element('Reel', reel_list)
            if reel is not None:
                # Look for EditRate in MainPicture or MainSound
                for track_type in ['MainPicture', 'MainSound']:
                    track = self._get_element(track_type, reel)
                    if track is not None:
                        edit_rate = self._get_element('EditRate', track)
                        if edit_rate is not None:
                            text = edit_rate.text
                            if text:
                                return text.strip()
        return None
    
    def _extract_aspect_ratio(self) -> Optional[str]:
        """Extract aspect ratio (Flat/Scope)"""
        reel_list = self._get_element('ReelList')
        if reel_list is not None:
            reel = self._get_element('Reel', reel_list)
            if reel is not None:
                picture = self._get_element('MainPicture', reel)
                if picture is not None:
                    # Look for ScreenAspectRatio
                    aspect = self._get_element('ScreenAspectRatio', picture)
                    if aspect is not None and aspect.text:
                        ratio = aspect.text.strip()
                        # Classify as Flat or Scope
                        if '1.85' in ratio or '1.89' in ratio or ratio.startswith('1.8'):
                            return 'Flat'
                        elif '2.39' in ratio or '2.35' in ratio or ratio.startswith('2.3'):
                            return 'Scope'
                        return ratio
        return None
    
    def _extract_audio_layout(self) -> Optional[str]:
        """Extract audio channel layout"""
        reel_list = self._get_element('ReelList')
        if reel_list is not None:
            reel = self._get_element('Reel', reel_list)
            if reel is not None:
                sound = self._get_element('MainSound', reel)
                if sound is not None:
                    # Look for audio layout/channel configuration
                    # This is simplified - real DCP audio can be complex
                    return "5.1"  # Default assumption
        return None
    
    def _extract_reels(self) -> List[Dict]:
        """Extract all reels with their asset references"""
        reels = []
        reel_list = self._get_element('ReelList')
        
        if reel_list is None:
            return reels
        
        for reel_elem in self._get_elements('Reel', reel_list):
            reel_data = {
                'reel_id': self._get_reel_id(reel_elem),
                'assets': []
            }
            
            # Extract assets from different track types
            for track_type in ['MainPicture', 'MainSound', 'MainSubtitle']:
                track = self._get_element(track_type, reel_elem)
                if track is not None:
                    asset_id = self._get_element('Id', track)
                    if asset_id is not None and asset_id.text:
                        asset_uuid = asset_id.text.strip()
                        if asset_uuid.startswith('urn:uuid:'):
                            asset_uuid = asset_uuid[9:]
                        
                        reel_data['assets'].append({
                            'type': track_type,
                            'uuid': asset_uuid,
                            'element': track
                        })
            
            reels.append(reel_data)
        
        return reels
    
    def _get_reel_id(self, reel_elem) -> str:
        """Get or generate reel ID"""
        id_elem = self._get_element('Id', reel_elem)
        if id_elem is not None and id_elem.text:
            reel_id = id_elem.text.strip()
            if reel_id.startswith('urn:uuid:'):
                reel_id = reel_id[9:]
            return reel_id
        # Generate new UUID if not present
        return str(uuid.uuid4())
    
    def _check_encryption(self) -> bool:
        """Check if any assets are encrypted"""
        # Look for KeyId elements which indicate encryption
        if self.namespace:
            key_ids = self.root.findall(f'.//{{{self.namespace}}}KeyId')
        else:
            key_ids = self.root.findall('.//KeyId')
        
        return len(key_ids) > 0


def parse_cpl(cpl_path: str) -> Dict:
    """
    Convenience function to parse a CPL file
    
    Args:
        cpl_path: Path to CPL XML file
        
    Returns:
        Dictionary containing CPL metadata
        
    Raises:
        CPLParseError: If parsing fails
    """
    parser = CPLParser(cpl_path)
    return parser.parse()
