"""
Accessible Route Optimizer - Accessibility Filtering Logic
Handles all accessibility-related filtering and validation
"""

from typing import Dict, List, Set
from enum import Enum


class AccessibilityRequirement(Enum):
    """Enumeration of supported accessibility requirements"""
    WHEELCHAIR_ACCESSIBLE = "wheelchair_accessible"
    NO_STAIRS = "no_stairs"
    WORKING_ELEVATOR = "working_elevator"
    LOW_FLOOR_VEHICLE = "low_floor_vehicle"
    AUDIO_ANNOUNCEMENTS = "audio_announcements"
    VISUAL_DISPLAYS = "visual_displays"
    TACTILE_GUIDANCE = "tactile_guidance"
    WIDE_DOORS = "wide_doors"
    LEVEL_BOARDING = "level_boarding"


class AccessibilityFilter:
    """
    Handles filtering of transit network based on accessibility requirements
    """
    
    def __init__(self, accessibility_data: Dict):
        """
        Initialize the accessibility filter
        
        Args:
            accessibility_data: Dictionary containing accessibility metadata for stops
        """
        self.accessibility_data = accessibility_data
        self.requirement_checkers = {
            'wheelchair_accessible': self._check_wheelchair_accessible,
            'no_stairs': self._check_no_stairs,
            'working_elevator': self._check_working_elevator,
            'low_floor_vehicle': self._check_low_floor_vehicle,
            'audio_announcements': self._check_audio_announcements,
            'visual_displays': self._check_visual_displays,
            'tactile_guidance': self._check_tactile_guidance,
            'wide_doors': self._check_wide_doors,
            'level_boarding': self._check_level_boarding
        }
    
    def meets_requirements(self, stop: str, requirements: List[str]) -> bool:
        """
        Check if a stop meets all specified accessibility requirements
        
        Args:
            stop: Stop name to check
            requirements: List of accessibility requirement strings
            
        Returns:
            True if stop meets all requirements, False otherwise
        """
        stop_data = self.accessibility_data.get(stop, {})
        
        for requirement in requirements:
            if requirement in self.requirement_checkers:
                if not self.requirement_checkers[requirement](stop_data):
                    return False
            else:
                # Unknown requirement - assume not met
                return False
        
        return True
    
    def edge_meets_requirements(self, from_stop: str, to_stop: str, 
                              edge_data: Dict, requirements: List[str]) -> bool:
        """
        Check if an edge (route segment) meets accessibility requirements
        
        Args:
            from_stop: Starting stop name
            to_stop: Destination stop name
            edge_data: Edge attributes from the graph
            requirements: List of accessibility requirement strings
            
        Returns:
            True if edge meets all requirements, False otherwise
        """
        # Check if both stops meet requirements
        if not (self.meets_requirements(from_stop, requirements) and 
                self.meets_requirements(to_stop, requirements)):
            return False
        
        # Check edge-specific requirements
        for requirement in requirements:
            if requirement == 'wheelchair_accessible':
                if not edge_data.get('wheelchair_accessible', False):
                    return False
            elif requirement == 'low_floor_vehicle':
                if not edge_data.get('low_floor', False):
                    return False
            elif requirement == 'wide_doors':
                if not edge_data.get('wide_doors', False):
                    return False
        
        return True
    
    def _check_wheelchair_accessible(self, stop_data: Dict) -> bool:
        """Check if stop is wheelchair accessible"""
        return stop_data.get('wheelchair_accessible', False)
    
    def _check_no_stairs(self, stop_data: Dict) -> bool:
        """Check if stop can be accessed without stairs"""
        has_stairs = stop_data.get('has_stairs', True)
        has_alternative = stop_data.get('has_elevator', False) or stop_data.get('has_ramp', False)
        
        # Either no stairs at all, or alternative access available
        return not has_stairs or has_alternative
    
    def _check_working_elevator(self, stop_data: Dict) -> bool:
        """Check if stop has a working elevator"""
        has_elevator = stop_data.get('has_elevator', False)
        elevator_working = stop_data.get('elevator_working', True)
        return has_elevator and elevator_working
    
    def _check_low_floor_vehicle(self, stop_data: Dict) -> bool:
        """Check if stop serves low-floor vehicles"""
        return stop_data.get('low_floor_service', False)
    
    def _check_audio_announcements(self, stop_data: Dict) -> bool:
        """Check if stop has audio announcements"""
        return stop_data.get('audio_announcements', False)
    
    def _check_visual_displays(self, stop_data: Dict) -> bool:
        """Check if stop has visual displays"""
        return stop_data.get('visual_displays', False)
    
    def _check_tactile_guidance(self, stop_data: Dict) -> bool:
        """Check if stop has tactile guidance systems"""
        return stop_data.get('tactile_guidance', False)
    
    def _check_wide_doors(self, stop_data: Dict) -> bool:
        """Check if stop has wide doors for accessibility"""
        return stop_data.get('wide_doors', False)
    
    def _check_level_boarding(self, stop_data: Dict) -> bool:
        """Check if stop supports level boarding"""
        return stop_data.get('level_boarding', False)
    
    def get_accessibility_score(self, stop: str) -> float:
        """
        Calculate an accessibility score for a stop (0.0 to 1.0)
        
        Args:
            stop: Stop name to evaluate
            
        Returns:
            Accessibility score between 0.0 (not accessible) and 1.0 (fully accessible)
        """
        stop_data = self.accessibility_data.get(stop, {})
        
        # Define weighted accessibility features
        features = {
            'wheelchair_accessible': 0.25,
            'has_elevator': 0.15,
            'elevator_working': 0.10,
            'has_ramp': 0.10,
            'audio_announcements': 0.10,
            'visual_displays': 0.10,
            'tactile_guidance': 0.05,
            'wide_doors': 0.05,
            'level_boarding': 0.05,
            'low_floor_service': 0.05
        }
        
        score = 0.0
        for feature, weight in features.items():
            if stop_data.get(feature, False):
                score += weight
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_accessibility_summary(self, stop: str) -> Dict:
        """
        Get a comprehensive accessibility summary for a stop
        
        Args:
            stop: Stop name
            
        Returns:
            Dictionary with accessibility information and recommendations
        """
        stop_data = self.accessibility_data.get(stop, {})
        score = self.get_accessibility_score(stop)
        
        # Categorize accessibility level
        if score >= 0.8:
            level = "Excellent"
        elif score >= 0.6:
            level = "Good"
        elif score >= 0.4:
            level = "Fair"
        elif score >= 0.2:
            level = "Limited"
        else:
            level = "Poor"
        
        # Generate recommendations
        recommendations = []
        if not stop_data.get('wheelchair_accessible', False):
            recommendations.append("Add wheelchair accessibility")
        if not stop_data.get('has_elevator', False) and stop_data.get('has_stairs', True):
            recommendations.append("Install elevator or ramp")
        if not stop_data.get('audio_announcements', False):
            recommendations.append("Add audio announcements for visually impaired")
        if not stop_data.get('visual_displays', False):
            recommendations.append("Install visual displays for hearing impaired")
        
        return {
            'stop': stop,
            'accessibility_score': score,
            'accessibility_level': level,
            'features': stop_data,
            'recommendations': recommendations
        }
    
    def filter_stops_by_requirements(self, stops: List[str], requirements: List[str]) -> List[str]:
        """
        Filter a list of stops by accessibility requirements
        
        Args:
            stops: List of stop names to filter
            requirements: List of accessibility requirements
            
        Returns:
            Filtered list of stops that meet all requirements
        """
        return [stop for stop in stops if self.meets_requirements(stop, requirements)]
    
    def get_supported_requirements(self) -> List[str]:
        """
        Get list of all supported accessibility requirements
        
        Returns:
            List of requirement strings
        """
        return list(self.requirement_checkers.keys())
    
    def validate_requirements(self, requirements: List[str]) -> Dict:
        """
        Validate a list of accessibility requirements
        
        Args:
            requirements: List of requirement strings to validate
            
        Returns:
            Dictionary with validation results
        """
        supported = self.get_supported_requirements()
        valid_requirements = []
        invalid_requirements = []
        
        for req in requirements:
            if req in supported:
                valid_requirements.append(req)
            else:
                invalid_requirements.append(req)
        
        return {
            'valid': valid_requirements,
            'invalid': invalid_requirements,
            'all_valid': len(invalid_requirements) == 0
        }
