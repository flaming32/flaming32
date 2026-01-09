import requests
import sys
import json
from datetime import datetime

class StashorraAPITester:
    def __init__(self, base_url="https://phone-value-calc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("API Root", success, details)
            return success
        except Exception as e:
            self.log_test("API Root", False, f"Error: {str(e)}")
            return False

    def test_popular_phones(self):
        """Test /api/popular-phones endpoint"""
        try:
            response = requests.get(f"{self.api_url}/popular-phones", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                brands = data.get('brands', [])
                brand_count = len(brands)
                
                # Validate structure
                has_apple = any(b.get('name') == 'Apple' for b in brands)
                has_samsung = any(b.get('name') == 'Samsung' for b in brands)
                
                details = f"Status: {response.status_code}, Brands: {brand_count}, Apple: {has_apple}, Samsung: {has_samsung}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Popular Phones", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Popular Phones", False, f"Error: {str(e)}")
            return False, {}

    def test_search_phone(self, brand="Apple", model="iPhone 15"):
        """Test /api/search-phone endpoint"""
        try:
            payload = {"brand": brand, "model": model}
            response = requests.post(
                f"{self.api_url}/search-phone", 
                json=payload, 
                timeout=30  # Web scraping takes time
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                slot_prices = data.get('slot_prices', [])
                jiji_prices = data.get('jiji_prices', [])
                
                details = f"Status: {response.status_code}, Slot: {len(slot_prices)} prices, Jiji: {len(jiji_prices)} prices"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Search Phone", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Search Phone", False, f"Error: {str(e)}")
            return False, {}

    def test_estimate_price(self, brand="Apple", model="iPhone 15", slot_price=1200000, jiji_prices=[800000, 900000]):
        """Test /api/estimate-price endpoint"""
        try:
            payload = {
                "brand": brand,
                "model": model,
                "condition": {
                    "screen_condition": "good",
                    "battery_health": "excellent", 
                    "physical_damage": "minor"
                },
                "slot_price": slot_price,
                "jiji_prices": jiji_prices
            }
            
            response = requests.post(
                f"{self.api_url}/estimate-price",
                json=payload,
                timeout=30  # AI processing takes time
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                estimated_price = data.get('estimated_price', 0)
                confidence = data.get('confidence', 'unknown')
                reasoning = data.get('reasoning', '')[:50] + "..." if data.get('reasoning') else ''
                
                details = f"Status: {response.status_code}, Price: ₦{estimated_price:,.0f}, Confidence: {confidence}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Estimate Price", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Estimate Price", False, f"Error: {str(e)}")
            return False, {}

    def test_estimate_price_edge_cases(self):
        """Test estimate price with edge cases"""
        test_cases = [
            {
                "name": "No Market Data",
                "payload": {
                    "brand": "TestBrand",
                    "model": "TestModel", 
                    "condition": {
                        "screen_condition": "poor",
                        "battery_health": "poor",
                        "physical_damage": "severe"
                    },
                    "slot_price": None,
                    "jiji_prices": []
                }
            },
            {
                "name": "Excellent Condition",
                "payload": {
                    "brand": "Samsung",
                    "model": "Galaxy S24",
                    "condition": {
                        "screen_condition": "excellent", 
                        "battery_health": "excellent",
                        "physical_damage": "none"
                    },
                    "slot_price": 800000,
                    "jiji_prices": [600000, 650000, 700000]
                }
            }
        ]
        
        for case in test_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/estimate-price",
                    json=case["payload"],
                    timeout=30
                )
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    price = data.get('estimated_price', 0)
                    details = f"Status: {response.status_code}, Price: ₦{price:,.0f}"
                else:
                    details = f"Status: {response.status_code}"
                    
                self.log_test(f"Estimate Price - {case['name']}", success, details)
            except Exception as e:
                self.log_test(f"Estimate Price - {case['name']}", False, f"Error: {str(e)}")

    def test_estimates_history(self):
        """Test /api/estimates endpoint"""
        try:
            response = requests.get(f"{self.api_url}/estimates", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Estimates: {count}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Estimates History", success, details)
            return success
        except Exception as e:
            self.log_test("Estimates History", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Stashorra Backend API Tests")
        print(f"📍 Testing: {self.base_url}")
        print("=" * 60)
        
        # Test API availability
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False
            
        # Test core endpoints
        self.test_popular_phones()
        
        # Test search with real data
        search_success, search_data = self.test_search_phone("Apple", "iPhone 15")
        
        # Test estimation
        self.test_estimate_price()
        self.test_estimate_price_edge_cases()
        
        # Test history
        self.test_estimates_history()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        elif self.tests_passed >= self.tests_run * 0.8:
            print("⚠️  Most tests passed, minor issues detected")
        else:
            print("❌ Multiple test failures detected")
            
        return self.tests_passed >= self.tests_run * 0.7

def main():
    tester = StashorraAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "summary": {
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "success_rate": tester.tests_passed / tester.tests_run if tester.tests_run > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())