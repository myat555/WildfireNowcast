"""
Test script for Wildfire Nowcast Agent

This script tests the wildfire agent functionality with sample queries.
"""

import json
import logging
import time
from datetime import datetime
from wildfire_nowcast_agent import wildfire_nowcast_agent_local

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_query(query: str, description: str):
    """Test a single agent query"""
    logger.info(f"\n🧪 Testing: {description}")
    logger.info(f"Query: {query}")
    logger.info("-" * 50)
    
    try:
        start_time = time.time()
        response = wildfire_nowcast_agent_local({"prompt": query})
        end_time = time.time()
        
        logger.info(f"Response ({end_time - start_time:.2f}s):")
        logger.info(response)
        logger.info("✅ Test completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

def test_nasa_data_integration():
    """Test NASA data integration functionality"""
    logger.info("\n🛰️ Testing NASA Data Integration")
    
    # Test FIRMS hotspot data
    test_agent_query(
        "Check for new wildfire hotspots in California",
        "FIRMS Hotspot Detection"
    )
    
    # Test EONET events
    test_agent_query(
        "Get recent wildfire events from NASA EONET",
        "EONET Event Retrieval"
    )
    
    # Test data summary
    test_agent_query(
        "Provide a summary of NASA wildfire data for the USA",
        "NASA Data Summary"
    )

def test_threat_assessment():
    """Test threat assessment functionality"""
    logger.info("\n🎯 Testing Threat Assessment")
    
    # Test threat assessment
    test_agent_query(
        "Assess wildfire threats to critical infrastructure in California",
        "Asset Threat Assessment"
    )
    
    # Test fire ranking
    test_agent_query(
        "Rank current fires by threat level",
        "Fire Threat Ranking"
    )
    
    # Test evacuation zones
    test_agent_query(
        "Calculate evacuation zones for active fires",
        "Evacuation Zone Calculation"
    )

def test_mapping_visualization():
    """Test mapping and visualization functionality"""
    logger.info("\n🗺️ Testing Mapping & Visualization")
    
    # Test fire map generation
    test_agent_query(
        "Generate a live map of current fire activity",
        "Fire Map Generation"
    )
    
    # Test evacuation map
    test_agent_query(
        "Create an evacuation zone map for active fires",
        "Evacuation Map Creation"
    )
    
    # Test progression map
    test_agent_query(
        "Show fire progression over the last 24 hours",
        "Fire Progression Visualization"
    )

def test_ics_reporting():
    """Test ICS reporting functionality"""
    logger.info("\n📋 Testing ICS Reporting")
    
    # Test situation report
    test_agent_query(
        "Draft an ICS situation report for current fires",
        "ICS Situation Report"
    )
    
    # Test resource recommendations
    test_agent_query(
        "Recommend resource allocation for current threats",
        "Resource Recommendations"
    )
    
    # Test incident briefing
    test_agent_query(
        "Generate an incident briefing for command staff",
        "Command Staff Briefing"
    )

def test_memory_functionality():
    """Test memory and incident tracking functionality"""
    logger.info("\n🧠 Testing Memory & Incident Tracking")
    
    # Test incident tracking
    test_agent_query(
        "Track the current wildfire incident",
        "Incident Tracking"
    )
    
    # Test incident history
    test_agent_query(
        "Retrieve incident history and patterns",
        "Incident History Retrieval"
    )
    
    # Test status update
    test_agent_query(
        "Update incident status with current threat assessment",
        "Incident Status Update"
    )

def test_comprehensive_workflow():
    """Test comprehensive wildfire monitoring workflow"""
    logger.info("\n🔄 Testing Comprehensive Workflow")
    
    # Test complete workflow
    test_agent_query(
        "Monitor wildfire activity in the Pacific Northwest, assess threats to populated areas, generate evacuation maps, and draft an ICS situation report",
        "Complete Wildfire Monitoring Workflow"
    )

def run_all_tests():
    """Run all agent tests"""
    logger.info("🚀 Starting Wildfire Nowcast Agent Tests")
    logger.info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test individual components
        test_nasa_data_integration()
        test_threat_assessment()
        test_mapping_visualization()
        test_ics_reporting()
        test_memory_functionality()
        
        # Test comprehensive workflow
        test_comprehensive_workflow()
        
        logger.info("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"\n❌ Test suite failed: {e}")
        raise

def run_specific_test(test_type: str):
    """Run a specific test type"""
    test_functions = {
        'nasa': test_nasa_data_integration,
        'threat': test_threat_assessment,
        'mapping': test_mapping_visualization,
        'ics': test_ics_reporting,
        'memory': test_memory_functionality,
        'workflow': test_comprehensive_workflow
    }
    
    if test_type in test_functions:
        logger.info(f"🧪 Running {test_type} tests only")
        test_functions[test_type]()
    else:
        logger.error(f"Unknown test type: {test_type}")
        logger.info("Available test types: nasa, threat, mapping, ics, memory, workflow")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Wildfire Nowcast Agent')
    parser.add_argument('--test-type', choices=['nasa', 'threat', 'mapping', 'ics', 'memory', 'workflow'],
                       help='Run specific test type only')
    parser.add_argument('--query', help='Test a specific query')
    
    args = parser.parse_args()
    
    if args.query:
        test_agent_query(args.query, "Custom Query Test")
    elif args.test_type:
        run_specific_test(args.test_type)
    else:
        run_all_tests()

if __name__ == "__main__":
    main()
