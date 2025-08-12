"""
Location extraction utility for transaction descriptions
Extracts and standardizes location information from merchant descriptions
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class LocationExtractor:
    """Extract location information from transaction descriptions"""
    
    def __init__(self):
        """Initialize with location patterns"""
        # Canadian provinces and territories
        self.ca_provinces = {
            'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba',
            'NB': 'New Brunswick', 'NL': 'Newfoundland and Labrador', 
            'NS': 'Nova Scotia', 'NT': 'Northwest Territories', 'NU': 'Nunavut',
            'ON': 'Ontario', 'PE': 'Prince Edward Island', 'QC': 'Quebec',
            'SK': 'Saskatchewan', 'YT': 'Yukon'
        }
        
        # US states (common ones in data)
        self.us_states = {
            'CA': 'California', 'NY': 'New York', 'FL': 'Florida',
            'TX': 'Texas', 'WA': 'Washington', 'IL': 'Illinois',
            'PA': 'Pennsylvania', 'OH': 'Ohio', 'MI': 'Michigan',
            'MA': 'Massachusetts', 'NJ': 'New Jersey', 'VA': 'Virginia'
        }
        
        # Countries
        self.countries = {
            'CAN': 'Canada', 'CA': 'Canada',
            'USA': 'United States', 'US': 'United States',
            'UK': 'United Kingdom', 'GB': 'United Kingdom',
            'FRA': 'France', 'DEU': 'Germany', 'NLD': 'Netherlands',
            'ESP': 'Spain', 'ITA': 'Italy', 'AUS': 'Australia'
        }
    
    def extract_location(self, description: str) -> Tuple[Optional[str], str]:
        """
        Extract location from description and return cleaned description
        
        Returns:
            Tuple of (location, cleaned_description)
        """
        if not description:
            return None, description
        
        original_desc = description
        location = None
        
        # Try different location patterns
        location = self._extract_canadian_location(description)
        if location:
            description = self._remove_location_from_description(description, location)
            return location, description.strip()
        
        location = self._extract_us_location(description)
        if location:
            description = self._remove_location_from_description(description, location)
            return location, description.strip()
        
        location = self._extract_international_location(description)
        if location:
            description = self._remove_location_from_description(description, location)
            return location, description.strip()
        
        # No location found
        return None, original_desc
    
    def _extract_canadian_location(self, description: str) -> Optional[str]:
        """Extract Canadian city/province from description"""
        
        # Multiple patterns to catch different formats
        patterns = [
            # Standard: CITY PROVINCE at end (e.g., "KINGSTON ON", "TORONTO ON")
            r'\b([A-Z][A-Z\s]+?)\s+([A-Z]{2})\s*$',
            # City at start, province at end with text in between (e.g., "CALGARY TRANSIT 123 AB")
            r'\b([A-Z]+)\s+.*\s+([A-Z]{2})\s*$',
            # Province code attached to city name (e.g., "VANCOUVBC", "TORONTOONT")
            r'\b([A-Z]{4,}?)([A-Z]{2})\s*$',
            # Mid-string: CITY PROVINCE (e.g., "RESTAURANT TORONTO ON 123")
            r'\b([A-Z][A-Z\s]+?)\s+([A-Z]{2})\b',
            # With separators: CITY, PROVINCE or CITY-PROVINCE  
            r'\b([A-Z][A-Z\s]+?)[,\-]\s*([A-Z]{2})\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description.upper())
            
            for match in matches:
                city_part, province_code = match.groups()
                
                if province_code in self.ca_provinces:
                    city = city_part.strip()
                    
                    # Clean up city name - remove numbers and special chars
                    city = re.sub(r'\d+[-\d]*', '', city)  # Remove phone numbers, addresses
                    city = re.sub(r'[#*\-_]+', ' ', city)  # Remove special chars
                    city = re.sub(r'\s+', ' ', city).strip()
                    
                    # For attached province codes, try to fix common city names
                    if len(city) > 6 and not ' ' in city:
                        # Check for known city patterns
                        city_fixes = {
                            'VANCOUV': 'VANCOUVER',
                            'TORONT': 'TORONTO',
                            'CALGAR': 'CALGARY',
                            'OTTAW': 'OTTAWA',
                            'MONTREA': 'MONTREAL',
                            'WINDSO': 'WINDSOR'
                        }
                        for partial, full in city_fixes.items():
                            if city.startswith(partial):
                                city = full
                                break
                    
                    # Skip if city is too short, all numbers, or looks like a merchant code
                    if (len(city) >= 3 and 
                        not re.match(r'^[A-Z]{1,4}$', city) and
                        not re.match(r'^\d+$', city) and
                        city not in ['HTTP', 'WWW', 'COM', 'NET', 'TMCANADA']):
                        
                        province = self.ca_provinces[province_code]
                        return f"{city.title()}, {province}, Canada"
        
        return None
    
    def _extract_us_location(self, description: str) -> Optional[str]:
        """Extract US city/state from description"""
        
        # Pattern: CITY STATE (e.g., "NEW YORK NY", "SAN FRANCISCO CA")
        pattern = r'\b([A-Z][A-Z\s]+?)\s+([A-Z]{2})\b'
        matches = re.finditer(pattern, description.upper())
        
        for match in matches:
            city_part, state_code = match.groups()
            
            if state_code in self.us_states:
                city = city_part.strip()
                state = self.us_states[state_code]
                
                # Clean up city name
                city = re.sub(r'\s+', ' ', city).strip()
                
                # Skip if city is too short or looks like a merchant code
                if len(city) >= 3 and not re.match(r'^[A-Z]{1,4}$', city):
                    return f"{city}, {state}, USA"
        
        return None
    
    def _extract_international_location(self, description: str) -> Optional[str]:
        """Extract international locations"""
        
        # Country codes at end of description
        pattern = r'\b([A-Z]{3}|[A-Z]{2})\s*$'
        match = re.search(pattern, description.upper())
        
        if match:
            country_code = match.group(1)
            if country_code in self.countries:
                return self.countries[country_code]
        
        # Known international cities/patterns
        international_patterns = [
            (r'\bLONDON\s+UK\b', 'London, United Kingdom'),
            (r'\bPARIS\s+FRA?\b', 'Paris, France'),
            (r'\bBERLIN\s+DEU?\b', 'Berlin, Germany'),
            (r'\bAMSTERDAM\s+NLD?\b', 'Amsterdam, Netherlands'),
            (r'\bMADRID\s+ESP?\b', 'Madrid, Spain'),
            (r'\bROME\s+ITA?\b', 'Rome, Italy'),
            (r'\bSYDNEY\s+AUS?\b', 'Sydney, Australia'),
            (r'\bMUNICH\s+DEU?\b', 'Munich, Germany'),
            (r'\bVIENNA\s+AUT?\b', 'Vienna, Austria'),
            (r'\bZURICH\s+CHE?\b', 'Zurich, Switzerland'),
        ]
        
        for pattern, location in international_patterns:
            if re.search(pattern, description.upper()):
                return location
        
        return None
    
    def _remove_location_from_description(self, description: str, location: str) -> str:
        """Remove location information from description"""
        
        # Extract components for removal
        if ', Canada' in location:
            city_province = location.replace(', Canada', '')
            city = city_province.split(', ')[0]
            
            # Remove Canadian patterns
            desc = re.sub(rf'\b{re.escape(city.upper())}\s+[A-Z]{{2}}\b', '', description.upper())
            desc = re.sub(rf'\b{re.escape(city)}\s+[A-Z]{{2}}\b', '', description, flags=re.IGNORECASE)
            
        elif ', USA' in location:
            city_state = location.replace(', USA', '')
            city = city_state.split(', ')[0]
            
            # Remove US patterns
            desc = re.sub(rf'\b{re.escape(city.upper())}\s+[A-Z]{{2}}\b', '', description.upper())
            desc = re.sub(rf'\b{re.escape(city)}\s+[A-Z]{{2}}\b', '', description, flags=re.IGNORECASE)
            
        else:
            # Remove country codes
            desc = re.sub(r'\b[A-Z]{2,3}\s*$', '', description)
        
        # Clean up extra spaces and common location artifacts
        desc = re.sub(r'\s+', ' ', desc or description)
        desc = desc.strip()
        
        return desc if desc else description
    
    def standardize_location(self, location: str) -> str:
        """Standardize location format"""
        if not location:
            return location
        
        # Already standardized if it has commas
        if ', ' in location:
            return location
        
        # Try to standardize common formats
        location = location.upper().strip()
        
        # Canadian provinces
        for code, name in self.ca_provinces.items():
            if location.endswith(f' {code}'):
                city = location[:-3].strip()
                return f"{city.title()}, {name}, Canada"
        
        # US states  
        for code, name in self.us_states.items():
            if location.endswith(f' {code}'):
                city = location[:-3].strip()
                return f"{city.title()}, {name}, USA"
        
        return location.title()
    
    def get_city(self, location: str) -> Optional[str]:
        """Extract just the city from a location string"""
        if not location:
            return None
        
        if ', ' in location:
            return location.split(', ')[0]
        
        return location
    
    def get_province_state(self, location: str) -> Optional[str]:
        """Extract province/state from location string"""
        if not location:
            return None
        
        parts = location.split(', ')
        if len(parts) >= 2:
            return parts[1]
        
        return None
    
    def get_country(self, location: str) -> Optional[str]:
        """Extract country from location string"""
        if not location:
            return None
        
        parts = location.split(', ')
        if len(parts) >= 3:
            return parts[2]
        elif 'Canada' in location or 'USA' in location:
            return parts[-1]
        
        return None