"""
Mapping and Visualization Tools for Wildfire Nowcast Agent

This module provides tools for creating interactive maps, visualizing fire data,
and generating evacuation zone maps using Folium and other mapping libraries.
"""

import json
import logging
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from strands import tool
import folium
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class MapGenerator:
    """Generator for wildfire maps and visualizations"""
    
    def __init__(self):
        # Color schemes for different threat levels
        self.threat_colors = {
            'CRITICAL': '#FF0000',  # Red
            'HIGH': '#FF6600',      # Orange
            'MODERATE': '#FFCC00',  # Yellow
            'LOW': '#00CC00',       # Green
            'UNKNOWN': '#666666'    # Gray
        }
        
        # Asset type icons
        self.asset_icons = {
            'residential': '🏠',
            'commercial': '🏢',
            'industrial': '🏭',
            'critical_infrastructure': '⚡',
            'healthcare': '🏥',
            'school': '🏫',
            'airport': '✈️',
            'power_plant': '⚡',
            'wildlife_refuge': '🌲',
            'forest': '🌳'
        }
    
    def create_base_map(self, center_lat: float = 39.8283, center_lon: float = -98.5795, zoom: int = 6) -> folium.Map:
        """Create a base map with appropriate styling"""
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add satellite imagery layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite Imagery',
            overlay=False,
            control=True
        ).add_to(m)
        
        return m
    
    def add_hotspot_markers(self, map_obj: folium.Map, hotspots_data: Dict) -> folium.Map:
        """Add wildfire hotspot markers to the map"""
        hotspots = hotspots_data.get('hotspots', [])
        
        for hotspot in hotspots:
            lat = float(hotspot.get('latitude', 0))
            lon = float(hotspot.get('longitude', 0))
            confidence = hotspot.get('confidence', 'nominal')
            brightness = hotspot.get('brightness', 0)
            
            # Determine marker color based on confidence
            if confidence == 'high':
                color = 'red'
                size = 12
            elif confidence == 'nominal':
                color = 'orange'
                size = 10
            else:
                color = 'yellow'
                size = 8
            
            # Create popup content
            popup_content = f"""
            <b>Wildfire Hotspot</b><br>
            Confidence: {confidence}<br>
            Brightness: {brightness}<br>
            Coordinates: {lat:.4f}, {lon:.4f}<br>
            Detected: {hotspot.get('acq_date', 'Unknown')}
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=size,
                popup=folium.Popup(popup_content, max_width=200),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(map_obj)
        
        return map_obj
    
    def add_asset_markers(self, map_obj: folium.Map, assets_data: Dict) -> folium.Map:
        """Add asset markers to the map"""
        assets = assets_data.get('assets', [])
        
        for asset in assets:
            lat = float(asset.get('latitude', 0))
            lon = float(asset.get('longitude', 0))
            asset_type = asset.get('type', 'residential')
            asset_name = asset.get('name', 'Unknown Asset')
            population = asset.get('population', 0)
            
            # Get icon for asset type
            icon = self.asset_icons.get(asset_type, '📍')
            
            # Create popup content
            popup_content = f"""
            <b>{asset_name}</b><br>
            Type: {asset_type}<br>
            Population: {population}<br>
            Coordinates: {lat:.4f}, {lon:.4f}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=200),
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 20px;">{icon}</div>',
                    icon_size=(20, 20),
                    icon_anchor=(10, 10)
                )
            ).add_to(map_obj)
        
        return map_obj
    
    def add_evacuation_zones(self, map_obj: folium.Map, evacuation_data: Dict) -> folium.Map:
        """Add evacuation zones to the map"""
        zones = evacuation_data.get('evacuation_zones', [])
        
        for zone in zones:
            fire_lat = zone.get('fire_latitude', 0)
            fire_lon = zone.get('fire_longitude', 0)
            radius_km = zone.get('evacuation_radius_km', 5.0)
            affected_population = zone.get('total_population', 0)
            
            # Create evacuation zone circle
            folium.Circle(
                location=[fire_lat, fire_lon],
                radius=radius_km * 1000,  # Convert km to meters
                popup=f"Evacuation Zone<br>Radius: {radius_km} km<br>Population: {affected_population}",
                color='red',
                weight=3,
                fillColor='red',
                fillOpacity=0.2
            ).add_to(map_obj)
        
        return map_obj

@tool
def generate_fire_map(
    hotspots_data: str,
    assets_data: str = None,
    map_center: str = "39.8283,-98.5795",
    zoom_level: int = 6,
    include_assets: bool = True
) -> str:
    """
    Generate an interactive fire map showing hotspots and assets.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        assets_data: JSON string containing asset locations (optional)
        map_center: Map center coordinates as "lat,lon"
        zoom_level: Initial zoom level (1-18)
        include_assets: Whether to include asset markers
    
    Returns:
        JSON string containing map HTML and metadata
    """
    try:
        # Parse input data
        hotspots = json.loads(hotspots_data)
        assets = json.loads(assets_data) if assets_data else {"assets": []}
        
        # Parse map center
        center_lat, center_lon = map(float, map_center.split(','))
        
        # Create map generator
        generator = MapGenerator()
        
        # Create base map
        m = generator.create_base_map(center_lat, center_lon, zoom_level)
        
        # Add hotspot markers
        m = generator.add_hotspot_markers(m, hotspots)
        
        # Add asset markers if requested
        if include_assets and assets.get('assets'):
            m = generator.add_asset_markers(m, assets)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Generate map HTML
        map_html = m._repr_html_()
        
        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'map_center': map_center,
            'zoom_level': zoom_level,
            'hotspot_count': len(hotspots.get('hotspots', [])),
            'asset_count': len(assets.get('assets', [])) if include_assets else 0,
            'map_type': 'fire_hotspots',
            'include_assets': include_assets
        }
        
        result = {
            'map_html': map_html,
            'metadata': metadata,
            'status': 'success'
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating fire map: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'map_html': '',
            'metadata': {}
        })

@tool
def render_evacuation_map(
    hotspots_data: str,
    assets_data: str,
    evacuation_data: str,
    map_center: str = "39.8283,-98.5795",
    zoom_level: int = 6
) -> str:
    """
    Generate an evacuation zone map showing fire hotspots and evacuation areas.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        assets_data: JSON string containing asset locations
        evacuation_data: JSON string containing evacuation zone data
        map_center: Map center coordinates as "lat,lon"
        zoom_level: Initial zoom level (1-18)
    
    Returns:
        JSON string containing evacuation map HTML and metadata
    """
    try:
        # Parse input data
        hotspots = json.loads(hotspots_data)
        assets = json.loads(assets_data)
        evacuation = json.loads(evacuation_data)
        
        # Parse map center
        center_lat, center_lon = map(float, map_center.split(','))
        
        # Create map generator
        generator = MapGenerator()
        
        # Create base map
        m = generator.create_base_map(center_lat, center_lon, zoom_level)
        
        # Add evacuation zones first (so they appear behind other markers)
        m = generator.add_evacuation_zones(m, evacuation)
        
        # Add hotspot markers
        m = generator.add_hotspot_markers(m, hotspots)
        
        # Add asset markers
        m = generator.add_asset_markers(m, assets)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Map Legend</b></p>
        <p><span style="color:red">●</span> High Confidence Fire</p>
        <p><span style="color:orange">●</span> Nominal Confidence Fire</p>
        <p><span style="color:yellow">●</span> Low Confidence Fire</p>
        <p><span style="color:red; opacity:0.3">●</span> Evacuation Zone</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Generate map HTML
        map_html = m._repr_html_()
        
        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'map_center': map_center,
            'zoom_level': zoom_level,
            'hotspot_count': len(hotspots.get('hotspots', [])),
            'asset_count': len(assets.get('assets', [])),
            'evacuation_zones': len(evacuation.get('evacuation_zones', [])),
            'map_type': 'evacuation_zones',
            'total_affected_population': evacuation.get('summary', {}).get('total_affected_population', 0)
        }
        
        result = {
            'map_html': map_html,
            'metadata': metadata,
            'status': 'success'
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error rendering evacuation map: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'map_html': '',
            'metadata': {}
        })

@tool
def create_progression_map(
    hotspots_data: str,
    time_range_hours: int = 24,
    map_center: str = "39.8283,-98.5795",
    zoom_level: int = 6
) -> str:
    """
    Create a fire progression map showing fire spread over time.
    
    Args:
        hotspots_data: JSON string containing FIRMS hotspot data
        time_range_hours: Time range to analyze in hours
        map_center: Map center coordinates as "lat,lon"
        zoom_level: Initial zoom level (1-18)
    
    Returns:
        JSON string containing progression map HTML and metadata
    """
    try:
        # Parse input data
        hotspots = json.loads(hotspots_data)
        
        # Parse map center
        center_lat, center_lon = map(float, map_center.split(','))
        
        # Create map generator
        generator = MapGenerator()
        
        # Create base map
        m = generator.create_base_map(center_lat, center_lon, zoom_level)
        
        # Group hotspots by time (simulate progression)
        hotspot_list = hotspots.get('hotspots', [])
        
        # Sort by brightness (simulate time progression)
        hotspot_list.sort(key=lambda x: float(x.get('brightness', 0)), reverse=True)
        
        # Add hotspots with different colors based on "time"
        colors = ['red', 'orange', 'yellow', 'lightgreen']
        for i, hotspot in enumerate(hotspot_list):
            lat = float(hotspot.get('latitude', 0))
            lon = float(hotspot.get('longitude', 0))
            brightness = hotspot.get('brightness', 0)
            
            # Assign color based on progression
            color = colors[i % len(colors)]
            
            # Create popup content
            popup_content = f"""
            <b>Fire Progression Point</b><br>
            Brightness: {brightness}<br>
            Coordinates: {lat:.4f}, {lon:.4f}<br>
            Progression Stage: {i + 1}
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_content, max_width=200),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
        
        # Add progression legend
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 150px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Fire Progression</b></p>
        <p><span style="color:red">●</span> Stage 1 (Most Recent)</p>
        <p><span style="color:orange">●</span> Stage 2</p>
        <p><span style="color:yellow">●</span> Stage 3</p>
        <p><span style="color:lightgreen">●</span> Stage 4 (Earliest)</p>
        <p>Time Range: {time_range_hours} hours</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Generate map HTML
        map_html = m._repr_html_()
        
        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'map_center': map_center,
            'zoom_level': zoom_level,
            'hotspot_count': len(hotspot_list),
            'time_range_hours': time_range_hours,
            'map_type': 'fire_progression'
        }
        
        result = {
            'map_html': map_html,
            'metadata': metadata,
            'status': 'success'
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating progression map: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'map_html': '',
            'metadata': {}
        })

@tool
def generate_threat_visualization(
    threat_data: str,
    visualization_type: str = "threat_levels"
) -> str:
    """
    Generate data visualizations for threat assessment data.
    
    Args:
        threat_data: JSON string containing threat assessment data
        visualization_type: Type of visualization ('threat_levels', 'asset_types', 'distance_analysis')
    
    Returns:
        JSON string containing visualization data and metadata
    """
    try:
        threat_info = json.loads(threat_data)
        assessments = threat_info.get('assessments', [])
        
        if not assessments:
            return json.dumps({
                'error': 'No threat assessment data available',
                'timestamp': datetime.now().isoformat(),
                'visualization_data': {}
            })
        
        # Create DataFrame for analysis
        df = pd.DataFrame(assessments)
        
        if visualization_type == 'threat_levels':
            # Threat level distribution
            threat_counts = df['threat_level'].value_counts()
            
            # Create pie chart data
            visualization_data = {
                'type': 'pie_chart',
                'title': 'Threat Level Distribution',
                'data': {
                    'labels': threat_counts.index.tolist(),
                    'values': threat_counts.values.tolist(),
                    'colors': [generator.threat_colors.get(level, '#666666') for level in threat_counts.index]
                }
            }
            
        elif visualization_type == 'asset_types':
            # Asset type analysis
            asset_counts = df['asset_type'].value_counts()
            
            visualization_data = {
                'type': 'bar_chart',
                'title': 'Threats by Asset Type',
                'data': {
                    'labels': asset_counts.index.tolist(),
                    'values': asset_counts.values.tolist()
                }
            }
            
        elif visualization_type == 'distance_analysis':
            # Distance vs threat score analysis
            distances = df['distance_km'].tolist()
            threat_scores = df['threat_score'].tolist()
            
            visualization_data = {
                'type': 'scatter_plot',
                'title': 'Distance vs Threat Score',
                'data': {
                    'x': distances,
                    'y': threat_scores,
                    'x_label': 'Distance (km)',
                    'y_label': 'Threat Score'
                }
            }
            
        else:
            return json.dumps({
                'error': f'Unknown visualization type: {visualization_type}',
                'timestamp': datetime.now().isoformat(),
                'visualization_data': {}
            })
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'visualization_type': visualization_type,
            'visualization_data': visualization_data,
            'summary': {
                'total_assessments': len(assessments),
                'critical_threats': len(df[df['threat_level'] == 'CRITICAL']),
                'high_threats': len(df[df['threat_level'] == 'HIGH']),
                'moderate_threats': len(df[df['threat_level'] == 'MODERATE']),
                'low_threats': len(df[df['threat_level'] == 'LOW'])
            },
            'status': 'success'
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating threat visualization: {e}")
        return json.dumps({
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'visualization_data': {}
        })
