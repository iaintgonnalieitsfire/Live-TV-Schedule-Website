import requests
import sys
from datetime import datetime, timedelta
import json

class TVScheduleAPITester:
    def __init__(self, base_url="https://f0b769b1-cb88-4aed-a7c4-9cf62239ee96.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, expected_data_checks=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=30)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            response_data = {}
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response received: {len(str(response_data))} characters")
                    
                    # Run additional data checks if provided
                    if expected_data_checks:
                        for check_name, check_func in expected_data_checks.items():
                            check_result = check_func(response_data)
                            if not check_result:
                                success = False
                                print(f"   ❌ Data check failed: {check_name}")
                            else:
                                print(f"   ✅ Data check passed: {check_name}")
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️  Response is not valid JSON")
                    response_data = {"raw_response": response.text[:500]}
            
            if success:
                self.tests_passed += 1
                print(f"✅ {name} - PASSED")
            else:
                print(f"❌ {name} - FAILED (Expected {expected_status}, got {response.status_code})")

            self.test_results.append({
                "name": name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_size": len(str(response_data))
            })

            return success, response_data

        except requests.exceptions.Timeout:
            print(f"❌ {name} - TIMEOUT (30 seconds)")
            self.test_results.append({"name": name, "success": False, "error": "Timeout"})
            return False, {}
        except Exception as e:
            print(f"❌ {name} - ERROR: {str(e)}")
            self.test_results.append({"name": name, "success": False, "error": str(e)})
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        def check_message(data):
            return "message" in data and "TV Schedule API" in data["message"]
        
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200,
            {"has_message": check_message}
        )

    def test_channels_endpoint(self):
        """Test the channels endpoint"""
        def check_channels_structure(data):
            if "channels" not in data:
                return False
            channels = data["channels"]
            if not isinstance(channels, list):
                return False
            if len(channels) < 40:  # Should have 47+ channels
                print(f"   ⚠️  Only {len(channels)} channels found, expected 47+")
                return False
            
            # Check first channel structure
            if channels:
                first_channel = channels[0]
                required_fields = ["id", "name", "url_name"]
                for field in required_fields:
                    if field not in first_channel:
                        print(f"   ⚠️  Missing field '{field}' in channel data")
                        return False
            
            print(f"   📊 Found {len(channels)} channels")
            return True
        
        def check_premium_channels(data):
            if "channels" not in data:
                return False
            
            channel_names = [ch["name"].lower() for ch in data["channels"]]
            premium_channels = ["hbo", "showtime", "starz", "cinemax"]
            
            found_premium = []
            for premium in premium_channels:
                if any(premium in name for name in channel_names):
                    found_premium.append(premium)
            
            print(f"   🎬 Premium channels found: {', '.join(found_premium)}")
            return len(found_premium) >= 3  # At least 3 premium channel families
        
        return self.run_test(
            "Channels Endpoint",
            "GET",
            "channels",
            200,
            {
                "channels_structure": check_channels_structure,
                "premium_channels": check_premium_channels
            }
        )

    def test_schedule_endpoint(self):
        """Test the main schedule endpoint"""
        def check_schedule_structure(data):
            required_fields = ["channels", "current_time", "timezone"]
            for field in required_fields:
                if field not in data:
                    print(f"   ⚠️  Missing field '{field}' in schedule data")
                    return False
            
            if not isinstance(data["channels"], list):
                return False
            
            if data["timezone"] != "America/New_York":
                print(f"   ⚠️  Unexpected timezone: {data['timezone']}")
                return False
            
            print(f"   📺 Schedule has {len(data['channels'])} channels")
            print(f"   🕐 Current time: {data['current_time']}")
            return True
        
        def check_shows_data(data):
            if "channels" not in data or not data["channels"]:
                return False
            
            total_shows = 0
            channels_with_shows = 0
            
            for channel in data["channels"]:
                if "shows" in channel and channel["shows"]:
                    channels_with_shows += 1
                    total_shows += len(channel["shows"])
                    
                    # Check first show structure
                    first_show = channel["shows"][0]
                    required_show_fields = ["title", "show_type", "start_time", "channel_id"]
                    for field in required_show_fields:
                        if field not in first_show:
                            print(f"   ⚠️  Missing field '{field}' in show data")
                            return False
            
            print(f"   📊 {channels_with_shows} channels have shows, {total_shows} total shows")
            return channels_with_shows > 0 and total_shows > 0
        
        return self.run_test(
            "Schedule Endpoint",
            "GET",
            "schedule",
            200,
            {
                "schedule_structure": check_schedule_structure,
                "shows_data": check_shows_data
            }
        )

    def test_specific_channel_schedule(self, channel_id="hbo"):
        """Test specific channel schedule endpoint"""
        def check_channel_schedule(data):
            required_fields = ["channel_id", "channel_name", "date", "shows"]
            for field in required_fields:
                if field not in data:
                    print(f"   ⚠️  Missing field '{field}' in channel schedule")
                    return False
            
            if data["channel_id"] != channel_id:
                print(f"   ⚠️  Channel ID mismatch: expected {channel_id}, got {data['channel_id']}")
                return False
            
            print(f"   📺 Channel: {data['channel_name']}")
            print(f"   📅 Date: {data['date']}")
            print(f"   📊 Shows: {len(data['shows']) if data['shows'] else 0}")
            
            return True
        
        def check_show_details(data):
            if not data.get("shows"):
                print(f"   ⚠️  No shows found for {channel_id}")
                return False
            
            show = data["shows"][0]
            show_fields = ["title", "show_type", "start_time", "channel_id"]
            
            for field in show_fields:
                if field not in show:
                    print(f"   ⚠️  Missing show field: {field}")
                    return False
            
            # Check time format (should be like "10:00 PM")
            time_str = show["start_time"]
            if not any(x in time_str.upper() for x in ["AM", "PM"]):
                print(f"   ⚠️  Invalid time format: {time_str}")
                return False
            
            print(f"   🎬 Sample show: {show['title']} at {show['start_time']}")
            return True
        
        return self.run_test(
            f"Channel Schedule ({channel_id.upper()})",
            "GET",
            f"schedule/{channel_id}",
            200,
            {
                "channel_schedule": check_channel_schedule,
                "show_details": check_show_details
            }
        )

    def test_refresh_endpoint(self):
        """Test the refresh endpoint"""
        def check_refresh_response(data):
            return "message" in data and "status" in data and data["status"] == "success"
        
        return self.run_test(
            "Refresh Endpoint",
            "GET",
            "refresh",
            200,
            {"refresh_response": check_refresh_response}
        )

    def test_invalid_channel(self):
        """Test invalid channel ID"""
        return self.run_test(
            "Invalid Channel ID",
            "GET",
            "schedule/invalid_channel_id",
            404
        )

def main():
    print("🚀 Starting TV Schedule API Tests")
    print("=" * 50)
    
    tester = TVScheduleAPITester()
    
    # Test all endpoints
    tests = [
        tester.test_root_endpoint,
        tester.test_channels_endpoint,
        tester.test_schedule_endpoint,
        lambda: tester.test_specific_channel_schedule("hbo"),
        lambda: tester.test_specific_channel_schedule("showtime"),
        lambda: tester.test_specific_channel_schedule("starz"),
        tester.test_refresh_endpoint,
        tester.test_invalid_channel
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for result in tester.test_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['name']}")
        if not result["success"] and "error" in result:
            print(f"      Error: {result['error']}")
    
    print(f"\n🎯 Overall: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())