"""
Test script for Wildfire Detection Lambda function
Tests all MCP tools with sample data
"""
import json
import logging
from lambda_function import lambda_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch_firms_hotspots():
    """Test fetching FIRMS hotspots"""
    print("\n" + "="*50)
    print("Testing: fetch_firms_hotspots")
    print("="*50)
    
    event = {
        "action_name": "fetch_firms_hotspots",
        "source": "VIIRS",
        "days": 1,
        "area": {
            "lat": 34.0522,
            "lon": -118.2437,
            "radius_km": 100
        }
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"Total Hotspots: {body.get('total_hotspots', 'N/A')}")
            print(f"New Hotspots Stored: {body.get('new_hotspots_stored', 'N/A')}")
            print(f"Source: {body.get('source', 'N/A')}")
            
            hotspots = body.get('hotspots', [])
            if hotspots:
                print(f"Sample hotspot: {hotspots[0]}")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_assess_threat_level():
    """Test threat level assessment"""
    print("\n" + "="*50)
    print("Testing: assess_threat_level")
    print("="*50)
    
    # Test with Los Angeles coordinates
    event = {
        "action_name": "assess_threat_level",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "confidence": 75
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"Location: {body.get('location', {})}")
            threat = body.get('threat_assessment', {})
            print(f"Threat Level: {threat.get('threat_level', 'N/A')}")
            print(f"Min Distance: {threat.get('min_distance_km', 'N/A')} km")
            print(f"Affected Areas: {len(threat.get('affected_areas', []))}")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_generate_fire_map():
    """Test fire map generation"""
    print("\n" + "="*50)
    print("Testing: generate_fire_map")
    print("="*50)
    
    event = {
        "action_name": "generate_fire_map",
        "center_lat": 37.7749,
        "center_lon": -122.4194,
        "zoom": 10,
        "include_hotspots": True
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            center = body.get('center', {})
            print(f"Map Center: {center.get('latitude', 'N/A')}, {center.get('longitude', 'N/A')}")
            print(f"Zoom Level: {body.get('zoom', 'N/A')}")
            print(f"Hotspots in View: {len(body.get('hotspots', []))}")
            print(f"Base Map URL: {body.get('base_map_url', 'N/A')[:100]}...")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_draft_ics_update():
    """Test ICS update generation"""
    print("\n" + "="*50)
    print("Testing: draft_ics_update")
    print("="*50)
    
    event = {
        "action_name": "draft_ics_update",
        "incident_id": "TEST-WF-001"
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"Incident ID: {body.get('incident_id', 'N/A')}")
            print(f"Generated At: {body.get('generated_at', 'N/A')}")
            print(f"Hotspot Count: {body.get('hotspot_count', 'N/A')}")
            
            ics_update = body.get('ics_update', '')
            if ics_update:
                print(f"ICS Update Preview: {ics_update[:200]}...")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_check_aoi_intersections():
    """Test AOI intersection checking"""
    print("\n" + "="*50)
    print("Testing: check_aoi_intersections")
    print("="*50)
    
    event = {
        "action_name": "check_aoi_intersections"
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            print(f"Total Intersections: {body.get('total_intersections', 'N/A')}")
            print(f"Analysis Timestamp: {body.get('analysis_timestamp', 'N/A')}")
            
            intersections = body.get('intersections', [])
            if intersections:
                print(f"Sample intersection: {intersections[0]}")
        else:
            print(f"Error: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def test_invalid_tool():
    """Test invalid tool name"""
    print("\n" + "="*50)
    print("Testing: invalid_tool (should fail)")
    print("="*50)
    
    event = {
        "action_name": "invalid_tool_name"
    }
    
    context = {}
    
    try:
        result = lambda_handler(event, context)
        print(f"Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 400:
            body = json.loads(result['body'])
            print(f"Error (expected): {body.get('error', 'N/A')}")
            print(f"Available Tools: {body.get('available_tools', [])}")
        else:
            print(f"Unexpected result: {result['body']}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

def main():
    """Run all tests"""
    print("WILDFIRE DETECTION LAMBDA FUNCTION TESTS")
    print("="*60)
    
    # Run all tests
    test_functions = [
        test_fetch_firms_hotspots,
        test_assess_threat_level,
        test_generate_fire_map,
        test_draft_ics_update,
        test_check_aoi_intersections,
        test_invalid_tool
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"Test {test_func.__name__} failed with error: {str(e)}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nNOTE: Some tests may show 'No active hotspots found' if NASA FIRMS")
    print("API is not accessible or returns no data for the test coordinates.")
    print("This is normal for testing purposes.")

if __name__ == "__main__":
    main()
