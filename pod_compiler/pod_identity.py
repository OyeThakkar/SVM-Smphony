"""
Pod Identity Module

Generates deterministic pod names and IDs for ad pods:
- Pod naming format: <THEATERID>_<RATING>_<SECTION>_<ASPECT>_<dd-mmm-yyyy>
- Pod ID: deterministic hash from inputs
"""

import hashlib
from datetime import datetime
from typing import List


class PodIdentity:
    """Generates deterministic pod identifiers"""
    
    @staticmethod
    def generate_pod_name(
        theatre_id: str,
        rating: str,
        section: str,
        aspect: str,
        start_date: str
    ) -> str:
        """
        Generate pod name in standard format
        
        Args:
            theatre_id: Theatre identifier (e.g., "T1042")
            rating: Content rating (G/PG/PG-13/R)
            section: Section (LPS/EPS)
            aspect: Aspect ratio (Flat/Scope)
            start_date: Start date in dd-mmm-yyyy format
            
        Returns:
            Pod name string (e.g., "T1042_PG13_LPS_FLAT_06-Feb-2026")
        """
        # Normalize rating (PG-13 → PG13)
        rating_normalized = rating.replace('-', '')
        
        # Ensure uppercase
        theatre_id = theatre_id.upper()
        rating_normalized = rating_normalized.upper()
        section = section.upper()
        aspect = aspect.upper()
        
        # Format: <THEATERID>_<RATING>_<SECTION>_<ASPECT>_<dd-mmm-yyyy>
        pod_name = f"{theatre_id}_{rating_normalized}_{section}_{aspect}_{start_date}"
        
        return pod_name
    
    @staticmethod
    def generate_pod_id(
        theatre_id: str,
        rating: str,
        section: str,
        aspect: str,
        start_date: str,
        cpl_uuids: List[str]
    ) -> str:
        """
        Generate deterministic pod ID from inputs
        
        The pod ID is a hash of all input parameters including the ordered
        list of CPL UUIDs. Same inputs always produce the same pod ID.
        
        Args:
            theatre_id: Theatre identifier
            rating: Content rating
            section: Section (LPS/EPS)
            aspect: Aspect ratio (Flat/Scope)
            start_date: Start date
            cpl_uuids: Ordered list of CPL UUIDs
            
        Returns:
            Deterministic pod ID (SHA-256 hash)
        """
        # Create deterministic input string
        components = [
            theatre_id.upper(),
            rating.upper().replace('-', ''),
            section.upper(),
            aspect.upper(),
            start_date,
            '|'.join(cpl_uuids)  # Ordered CPL UUIDs
        ]
        
        input_string = '||'.join(components)
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(input_string.encode('utf-8'))
        pod_id = hash_obj.hexdigest()
        
        return pod_id
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """
        Parse date string in dd-mmm-yyyy format
        
        Args:
            date_str: Date string (e.g., "06-Feb-2026")
            
        Returns:
            datetime object
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            return datetime.strptime(date_str, "%d-%b-%Y")
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{date_str}'. "
                "Expected format: dd-mmm-yyyy (e.g., 06-Feb-2026)"
            )
    
    @staticmethod
    def format_date(date_obj: datetime) -> str:
        """
        Format datetime to dd-mmm-yyyy string
        
        Args:
            date_obj: datetime object
            
        Returns:
            Formatted date string (e.g., "06-Feb-2026")
        """
        return date_obj.strftime("%d-%b-%Y")
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        Validate date string format
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            PodIdentity.parse_date(date_str)
            return True
        except ValueError:
            return False
