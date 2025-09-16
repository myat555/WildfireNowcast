"""
Threat Assessment Tools for Wildfire Nowcast Agent

This module provides tools for analyzing wildfire threats to assets,
ranking fire threats, and calculating evacuation zones.
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from strands import tool
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class ThreatAssessmentEngine:
    """Engine for wildfire threat assessment and analysis"""
    
    def __init__(self):
        # Default asset types with their threat multipliers
        self.asset_types = {
            'residential': {'threat_multiplier': 1.0, 'evacuation_radius': 5.0},
            'commercial': {'threat_multiplier': 0.8, 'evacuation_radius': 3.0},
            'industrial': {'threat_multiplier': 1.2, 'evacuation_radius': 8.0},
            'critical_infrastructure': {'threat_multiplier': 2.0, 'evacuation_radius': 10.0},
            'healthcare': {'threat_multiplier': 1.5, 'evacuation_radius': 7.0},
            'school': {'threat_multiplier': 1.3, 'evacuation_radius': 6.0},
            'airport': {'threat_multiplier': 1.8, 'evacuation_radius': 12.0},
            'power_plant': {'threat_multiplier': 2.5, 'evacuation_radius': 15.0},
            'wildlife_refuge': {'threat_multiplier': 0.5, 'evacuation_radius': 2.0},
            'forest': {'threat_multiplier': 0.3, 'evacuation_radius': 1.0}
        }
        
        # Fire intensity levels
        self.fire_intensity_levels = {
            'low': {'spread_rate': 0.1, 'threat_multiplier': 0.5},
            'moderate': {'spread_rate': 0.3, 'threat_multiplier': 1.0},
            'high': {'spread_rate': 0.6, 'threat_multiplier': 1.5},
            'extreme': {'spread_rate': 1.0, 'threat_multiplier': 2.0}
        }
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def assess_fire_threat(self, fire_data: Dict, asset_data: Dict) -> Dict:
        """Assess threat level of a fire to a specific asset"""
        try:
            fire_lat = float(fire_data.get('latitude', 0))
            fire_lon = float(fire_data.get('longitude', 0))
            fire_confidence = fire_data.get('confidence', 'nominal')
            
            asset_lat = float(asset_data.get('latitude', 0))
            asset_lon = float(asset_data.get('longitude', 0))
            asset_type = asset_data.get('type', 'residential')
            asset_population = asset_data.get('population', 0)
            
            # Calculate distance
            distance = self.calculate_distance(fire_lat, fire_lon, asset_lat, asset_lon)
            
            # Get threat parameters
            asset_config = self.asset_types.get(asset_type, self.asset_types['residential'])
            fire_config = self.fire_intensity_levels.get(fire_confidence, self.fire_intensity_levels['moderate'])
            
            # Calculate threat score
            base_threat = 100.0 / max(distance, 0.1)  # Inverse distance relationship
            threat_score = (base_threat * 
                          asset_config['threat_multiplier'] * 
                          fire_config['threat_multiplier'] * 
                          (1 + asset_population / 1000))  # Population factor
            
            # Determine threat level
            if threat_score > 50:
                threat_level = 'CRITICAL'
            elif threat_score > 25:
                threat_level = 'HIGH'
            elif threat_score > 10:
                threat_level = 'MODERATE'
            else:
                threat_level = 'LOW'
            
            # Check if evacuation is needed
            evacuation_needed = distance <= asset_config['evacuation_radius']
            
            return {
                'asset_id': asset_data.get('id', 'unknown'),
                'asset_name': asset_data.get('name', 'Unknown Asset'),
                'asset_type': asset_type,
                'fire_id': fire_data.get('id', 'unknown'),
                'distance_km': round(distance, 2),
                'threat_score': round(threat_score, 2),
                'threat_level': threat_level,
                'evacuation_needed': evacuation_needed,
                'evacuation_radius_km': asset_config['evacuation_radius'],
                'fire_confidence': fire_confidence,
                'asset_population': asset_population
            }
            
        except Exception as e:
            logger.error(f"Error assessing fire threat: {e}")
            return {
                'error': str(e),
                'threat_level': 'UNKNOWN',
                'threat_score': 0
            }

@tool
def assess_asset_threats(
    hotspots_data: str,
    assets_data: str,
    max_distance_km: float = 50.0
) -> str:
    """
    Assess wildfire threats to critical assets and infrastructure.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        assets_data: JSON string containing asset locations and metadata
        max_distance_km: Maximum distance to consider for threat assessment
    
    Returns:
        JSON string containing threat assessment results
    """
    try:
        # Parse input data
        hotspots = json.loads(hotspots_data)
        assets = json.loads(assets_data)
        
        engine = ThreatAssessmentEngine()
        threat_assessments = []
        
        # Process each hotspot
        for hotspot in hotspots.get('hotspots', []):
            hotspot_lat = float(hotspot.get('latitude', 0))
            hotspot_lon = float(hotspot.get('longitude', 0))
            
            # Check threats to each asset
            for asset in assets.get('assets', []):
                asset_lat = float(asset.get('latitude', 0))
                asset_lon = float(asset.get('longitude', 0))
                
                # Calculate distance
                distance = engine.calculate_distance(
                    hotspot_lat, hotspot_lon, asset_lat, asset_lon
                )
                
                # Only assess if within maximum distance
                if distance <= max_distance_km:
                    assessment = engine.assess_fire_threat(hotspot, asset)
                    threat_assessments.append(assessment)
        
        # Sort by threat score (highest first)
        threat_assessments.sort(key=lambda x: x.get('threat_score', 0), reverse=True)
        
        # Generate summary statistics
        critical_count = sum(1 for t in threat_assessments if t.get('threat_level') == 'CRITICAL')
        high_count = sum(1 for t in threat_assessments if t.get('threat_level') == 'HIGH')
        evacuation_count = sum(1 for t in threat_assessments if t.get('evacuation_needed', False))
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'max_distance_km': max_distance_km,
            'total_assessments': len(threat_assessments),
            'summary': {
                'critical_threats': critical_count,
                'high_threats': high_count,
                'evacuation_needed': evacuation_count
            },
            'assessments': threat_assessments
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error assessing asset threats: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'total_assessments': 0,
            'assessments': []
        })

@tool
def rank_fire_threats(
    hotspots_data: str,
    criteria: str = "population_proximity"
) -> str:
    """
    Rank wildfire hotspots by threat level using various criteria.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        criteria: Ranking criteria ('population_proximity', 'fire_intensity', 'spread_potential')
    
    Returns:
        JSON string containing ranked fire threats
    """
    try:
        hotspots = json.loads(hotspots_data)
        engine = ThreatAssessmentEngine()
        
        ranked_fires = []
        
        for hotspot in hotspots.get('hotspots', []):
            fire_id = hotspot.get('id', f"fire_{len(ranked_fires)}")
            lat = float(hotspot.get('latitude', 0))
            lon = float(hotspot.get('longitude', 0))
            confidence = hotspot.get('confidence', 'nominal')
            brightness = float(hotspot.get('brightness', 0))
            
            # Calculate threat score based on criteria
            if criteria == 'population_proximity':
                # Simulate population density (in real implementation, use actual data)
                threat_score = brightness * 0.5 + np.random.uniform(0, 50)
            elif criteria == 'fire_intensity':
                threat_score = brightness * 0.8 + (100 if confidence == 'high' else 50)
            elif criteria == 'spread_potential':
                # Simulate spread potential based on brightness and confidence
                spread_rate = engine.fire_intensity_levels.get(confidence, {}).get('spread_rate', 0.3)
                threat_score = brightness * spread_rate * 100
            else:
                threat_score = brightness * 0.6
            
            # Determine threat level
            if threat_score > 80:
                threat_level = 'CRITICAL'
            elif threat_score > 60:
                threat_level = 'HIGH'
            elif threat_score > 40:
                threat_level = 'MODERATE'
            else:
                threat_level = 'LOW'
            
            ranked_fires.append({
                'fire_id': fire_id,
                'latitude': lat,
                'longitude': lon,
                'confidence': confidence,
                'brightness': brightness,
                'threat_score': round(threat_score, 2),
                'threat_level': threat_level,
                'ranking_criteria': criteria
            })
        
        # Sort by threat score
        ranked_fires.sort(key=lambda x: x['threat_score'], reverse=True)
        
        # Add ranking position
        for i, fire in enumerate(ranked_fires):
            fire['rank'] = i + 1
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'criteria': criteria,
            'total_fires': len(ranked_fires),
            'summary': {
                'critical': sum(1 for f in ranked_fires if f['threat_level'] == 'CRITICAL'),
                'high': sum(1 for f in ranked_fires if f['threat_level'] == 'HIGH'),
                'moderate': sum(1 for f in ranked_fires if f['threat_level'] == 'MODERATE'),
                'low': sum(1 for f in ranked_fires if f['threat_level'] == 'LOW')
            },
            'ranked_fires': ranked_fires
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error ranking fire threats: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'total_fires': 0,
            'ranked_fires': []
        })

@tool
def calculate_evacuation_zones(
    hotspots_data: str,
    assets_data: str,
    buffer_distance_km: float = 5.0
) -> str:
    """
    Calculate evacuation zones around wildfire hotspots.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        assets_data: JSON string containing asset locations
        buffer_distance_km: Buffer distance for evacuation zones
    
    Returns:
        JSON string containing evacuation zone information
    """
    try:
        hotspots = json.loads(hotspots_data)
        assets = json.loads(assets_data)
        
        engine = ThreatAssessmentEngine()
        evacuation_zones = []
        
        for hotspot in hotspots.get('hotspots', []):
            fire_id = hotspot.get('id', f"fire_{len(evacuation_zones)}")
            fire_lat = float(hotspot.get('latitude', 0))
            fire_lon = float(hotspot.get('longitude', 0))
            confidence = hotspot.get('confidence', 'nominal')
            
            # Get fire intensity configuration
            fire_config = engine.fire_intensity_levels.get(confidence, engine.fire_intensity_levels['moderate'])
            
            # Calculate evacuation radius based on fire intensity
            base_radius = buffer_distance_km
            intensity_multiplier = fire_config['threat_multiplier']
            evacuation_radius = base_radius * intensity_multiplier
            
            # Find assets within evacuation zone
            affected_assets = []
            for asset in assets.get('assets', []):
                asset_lat = float(asset.get('latitude', 0))
                asset_lon = float(asset.get('longitude', 0))
                
                distance = engine.calculate_distance(fire_lat, fire_lon, asset_lat, asset_lon)
                
                if distance <= evacuation_radius:
                    affected_assets.append({
                        'asset_id': asset.get('id', 'unknown'),
                        'asset_name': asset.get('name', 'Unknown Asset'),
                        'asset_type': asset.get('type', 'residential'),
                        'distance_km': round(distance, 2),
                        'population': asset.get('population', 0)
                    })
            
            # Sort affected assets by distance
            affected_assets.sort(key=lambda x: x['distance_km'])
            
            # Calculate evacuation statistics
            total_population = sum(asset['population'] for asset in affected_assets)
            asset_types = {}
            for asset in affected_assets:
                asset_type = asset['asset_type']
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
            
            evacuation_zones.append({
                'fire_id': fire_id,
                'fire_latitude': fire_lat,
                'fire_longitude': fire_lon,
                'fire_confidence': confidence,
                'evacuation_radius_km': round(evacuation_radius, 2),
                'affected_assets_count': len(affected_assets),
                'total_population': total_population,
                'asset_types': asset_types,
                'affected_assets': affected_assets
            })
        
        # Sort evacuation zones by total population affected
        evacuation_zones.sort(key=lambda x: x['total_population'], reverse=True)
        
        # Generate summary
        total_zones = len(evacuation_zones)
        total_affected_assets = sum(zone['affected_assets_count'] for zone in evacuation_zones)
        total_affected_population = sum(zone['total_population'] for zone in evacuation_zones)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'buffer_distance_km': buffer_distance_km,
            'summary': {
                'total_evacuation_zones': total_zones,
                'total_affected_assets': total_affected_assets,
                'total_affected_population': total_affected_population
            },
            'evacuation_zones': evacuation_zones
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error calculating evacuation zones: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'total_evacuation_zones': 0,
            'evacuation_zones': []
        })

@tool
def generate_threat_summary(
    hotspots_data: str,
    assets_data: str
) -> str:
    """
    Generate a comprehensive threat summary combining all threat assessments.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        assets_data: JSON string containing asset locations
    
    Returns:
        JSON string containing comprehensive threat summary
    """
    try:
        # Get threat assessments
        threat_assessments = json.loads(assess_asset_threats(hotspots_data, assets_data))
        ranked_fires = json.loads(rank_fire_threats(hotspots_data))
        evacuation_zones = json.loads(calculate_evacuation_zones(hotspots_data, assets_data))
        
        # Create comprehensive summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_hotspots': len(json.loads(hotspots_data).get('hotspots', [])),
                'total_assets': len(json.loads(assets_data).get('assets', [])),
                'critical_threats': threat_assessments['summary']['critical_threats'],
                'high_threats': threat_assessments['summary']['high_threats'],
                'evacuation_zones': evacuation_zones['summary']['total_evacuation_zones'],
                'affected_population': evacuation_zones['summary']['total_affected_population']
            },
            'threat_assessments': threat_assessments,
            'ranked_fires': ranked_fires,
            'evacuation_zones': evacuation_zones,
            'recommendations': {
                'immediate_actions': [],
                'monitoring_priorities': [],
                'resource_allocation': []
            }
        }
        
        # Generate recommendations based on threat levels
        if summary['overview']['critical_threats'] > 0:
            summary['recommendations']['immediate_actions'].append(
                "CRITICAL: Immediate evacuation and resource deployment required"
            )
        
        if summary['overview']['high_threats'] > 0:
            summary['recommendations']['immediate_actions'].append(
                "HIGH: Prepare evacuation plans and mobilize resources"
            )
        
        if summary['overview']['evacuation_zones'] > 0:
            summary['recommendations']['monitoring_priorities'].append(
                f"Monitor {summary['overview']['evacuation_zones']} evacuation zones"
            )
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating threat summary: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_hotspots': 0,
                'total_assets': 0,
                'critical_threats': 0,
                'high_threats': 0,
                'evacuation_zones': 0,
                'affected_population': 0
            }
        })
