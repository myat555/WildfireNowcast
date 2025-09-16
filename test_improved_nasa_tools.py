#!/usr/bin/env python3
"""
Test script for improved NASA tools

This script tests the enhanced NASA data integration tools to ensure they work correctly
with the official NASA APIs.
"""

import json
import os
from tools.improved_nasa_tools import (
    fetch_firms_hotspots_enhanced,
    get_gibs_capabilities,
    get_gibs_layer_info,
    fetch_eonet_events_enhanced,
    get_eonet_categories,
    get_eonet_sources
)

def test_firms_hotspots():
    """Test FIRMS hotspot retrieval"""
    print("🔥 Testing FIRMS Hotspots...")
    try:
        result = fetch_firms_hotspots_enhanced(
            area="usa",
            days_back=1,
            satellite="both",
            format="json"
        )
        data = json.loads(result)
        print(f"✅ FIRMS: Found {data.get('hotspot_count', 0)} hotspots")
        print(f"   Data source: {data.get('data_source', 'Unknown')}")
        print(f"   API version: {data.get('api_version', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ FIRMS test failed: {e}")
        return False

def test_gibs_capabilities():
    """Test GIBS capabilities"""
    print("\n🛰️ Testing GIBS Capabilities...")
    try:
        result = get_gibs_capabilities("epsg4326")
        data = json.loads(result)
        layers = data.get('capabilities', {}).get('layers', [])
        print(f"✅ GIBS: Found {len(layers)} available layers")
        print(f"   Projection: {data.get('projection', 'Unknown')}")
        print(f"   Service type: {data.get('service_type', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ GIBS capabilities test failed: {e}")
        return False

def test_gibs_layer_info():
    """Test GIBS layer information"""
    print("\n🗺️ Testing GIBS Layer Info...")
    try:
        result = get_gibs_layer_info("MODIS_Terra_CorrectedReflectance_TrueColor", "epsg4326")
        data = json.loads(result)
        layer_info = data.get('layer_info', {})
        print(f"✅ GIBS Layer: {layer_info.get('name', 'Unknown')}")
        print(f"   Title: {layer_info.get('title', 'Unknown')}")
        print(f"   Projection: {data.get('projection', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ GIBS layer info test failed: {e}")
        return False

def test_eonet_events():
    """Test EONET events"""
    print("\n🌍 Testing EONET Events...")
    try:
        result = fetch_eonet_events_enhanced(
            category="wildfires",
            days_back=30,
            status="open",
            limit=10
        )
        data = json.loads(result)
        events = data.get('events', [])
        print(f"✅ EONET: Found {len(events)} wildfire events")
        print(f"   Data source: {data.get('data_source', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ EONET events test failed: {e}")
        return False

def test_eonet_categories():
    """Test EONET categories"""
    print("\n📋 Testing EONET Categories...")
    try:
        result = get_eonet_categories()
        data = json.loads(result)
        categories = data.get('categories', [])
        print(f"✅ EONET Categories: Found {len(categories)} categories")
        print(f"   Data source: {data.get('data_source', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ EONET categories test failed: {e}")
        return False

def test_eonet_sources():
    """Test EONET sources"""
    print("\n📡 Testing EONET Sources...")
    try:
        result = get_eonet_sources()
        data = json.loads(result)
        sources = data.get('sources', [])
        print(f"✅ EONET Sources: Found {len(sources)} data sources")
        print(f"   Data source: {data.get('data_source', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ EONET sources test failed: {e}")
        return False

def main():
    """Run all NASA tool tests"""
    print("🚀 Testing Improved NASA Tools")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Some tests may fail without NASA API keys.")
        print("   Create .env file with NASA_FIRMS_API_KEY for full testing.")
        print()
    
    tests = [
        test_firms_hotspots,
        test_gibs_capabilities,
        test_gibs_layer_info,
        test_eonet_events,
        test_eonet_categories,
        test_eonet_sources
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All NASA tools are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
