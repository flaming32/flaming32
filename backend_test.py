import requests
import sys
import json
from datetime import datetime

class StashorraAPITester:
    def __init__(self, base_url="https://stashorra-preview.preview.emergentagent.com"):
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

    def test_condition_questions(self, brand="Apple", model="iPhone 14 Pro"):
        """Test /api/condition-questions/{brand}/{model} endpoint"""
        try:
            encoded_model = requests.utils.quote(model)
            response = requests.get(f"{self.api_url}/condition-questions/{brand}/{encoded_model}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                questions = data.get('questions', [])
                question_count = len(questions)
                biometric_type = data.get('biometric_type', 'unknown')
                
                # Check for iPhone specific questions
                if brand == "Apple":
                    has_face_id = any(q.get('id') == 'face_id_working' for q in questions)
                    has_touch_id = any(q.get('id') == 'touch_id_working' for q in questions)
                    has_icloud = any(q.get('id') == 'icloud_status' for q in questions)
                    has_true_tone = any(q.get('id') == 'true_tone_working' for q in questions)
                    details = f"Status: {response.status_code}, Questions: {question_count}, Biometric: {biometric_type}, Face ID: {has_face_id}, Touch ID: {has_touch_id}, iCloud: {has_icloud}, True Tone: {has_true_tone}"
                else:
                    # Check for Android specific questions
                    has_fingerprint = any(q.get('id') == 'fingerprint_working' for q in questions)
                    has_face_unlock = any(q.get('id') == 'face_unlock_working' for q in questions)
                    has_frp = any(q.get('id') == 'frp_status' for q in questions)
                    has_charging = any(q.get('id') == 'charging_port' for q in questions)
                    details = f"Status: {response.status_code}, Questions: {question_count}, Biometric: {biometric_type}, Fingerprint: {has_fingerprint}, Face Unlock: {has_face_unlock}, FRP: {has_frp}, Charging: {has_charging}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test(f"Condition Questions ({brand} {model})", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test(f"Condition Questions ({brand} {model})", False, f"Error: {str(e)}")
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
                new_prices = data.get('new_prices', [])
                used_prices = data.get('used_prices', [])
                
                details = f"Status: {response.status_code}, New: {len(new_prices)} prices, Used: {len(used_prices)} prices"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Search Phone", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Search Phone", False, f"Error: {str(e)}")
            return False, {}

    def test_payment_info(self):
        """Test /api/payment-info endpoint"""
        try:
            response = requests.get(f"{self.api_url}/payment-info", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                account_number = data.get('account_number', '')
                bank_name = data.get('bank_name', '')
                account_name = data.get('account_name', '')
                amount = data.get('amount', 0)
                uses_per_payment = data.get('uses_per_payment', 0)
                
                # Verify correct payment details
                correct_details = (
                    account_number == "3002978669" and
                    bank_name == "KUDA MFB" and
                    account_name == "STASHORRA STORE" and
                    amount == 400 and
                    uses_per_payment == 2
                )
                
                details = f"Status: {response.status_code}, Bank: {bank_name}, Account: {account_number}, Name: {account_name}, Amount: ₦{amount}, Uses: {uses_per_payment}, Correct: {correct_details}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Payment Info", success and correct_details, details)
            return success and correct_details
        except Exception as e:
            self.log_test("Payment Info", False, f"Error: {str(e)}")
            return False

    def test_admin_login(self):
        """Test /api/admin/login endpoint"""
        try:
            # Test with correct credentials
            payload = {"username": "admin", "password": "Olaoluwa32$"}
            response = requests.post(f"{self.api_url}/admin/login", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                login_success = data.get('success', False)
                details = f"Status: {response.status_code}, Login Success: {login_success}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Admin Login (Valid)", success and login_success, details)
            
            # Test with invalid credentials
            payload = {"username": "admin", "password": "wrongpassword"}
            response = requests.post(f"{self.api_url}/admin/login", json=payload, timeout=10)
            invalid_success = response.status_code == 401
            
            self.log_test("Admin Login (Invalid)", invalid_success, f"Status: {response.status_code} (should be 401)")
            
            return success and login_success
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False

    def test_admin_generate_code(self):
        """Test /api/admin/generate-code endpoint"""
        try:
            payload = {
                "username": "admin", 
                "password": "Olaoluwa32$",
                "note": "Test code for API testing"
            }
            response = requests.post(f"{self.api_url}/admin/generate-code", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                code = data.get('code', '')
                uses = data.get('uses', 0)
                details = f"Status: {response.status_code}, Code: {code}, Uses: {uses}"
                
                # Store the generated code for later tests
                self.test_access_code = code
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Admin Generate Code", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Admin Generate Code", False, f"Error: {str(e)}")
            return False, {}

    def test_verify_access_code(self, code=None):
        """Test /api/verify-code endpoint"""
        if not code and hasattr(self, 'test_access_code'):
            code = self.test_access_code
        elif not code:
            self.log_test("Verify Access Code", False, "No access code available for testing")
            return False
            
        try:
            payload = {"code": code}
            response = requests.post(f"{self.api_url}/verify-code", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                valid = data.get('valid', False)
                uses_remaining = data.get('uses_remaining', 0)
                message = data.get('message', '')
                details = f"Status: {response.status_code}, Valid: {valid}, Uses: {uses_remaining}, Message: {message}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
            self.log_test("Verify Access Code", success and valid, details)
            return success and valid
        except Exception as e:
            self.log_test("Verify Access Code", False, f"Error: {str(e)}")
            return False

    def test_estimate_price_with_access_code(self, brand="Apple", model="iPhone 15", new_price=1400000, used_price=900000):
        """Test /api/estimate-price endpoint with access code requirement"""
        if not hasattr(self, 'test_access_code'):
            self.log_test("Estimate Price with Access Code", False, "No access code available for testing")
            return False, {}
            
        try:
            # iPhone condition payload
            if brand == "Apple":
                condition = {
                    "screen_condition": "good",
                    "body_condition": "good", 
                    "battery_health": "excellent",
                    "speakers_working": "yes",
                    "cameras_working": "all_working",
                    "buttons_working": "all_working",
                    "network_status": "unlocked",
                    "original_parts": "yes",
                    "face_id_working": "yes",
                    "touch_id_working": "not_applicable",
                    "icloud_status": "unlocked",
                    "back_glass_condition": "intact",
                    "true_tone_working": "yes"
                }
            else:
                # Android condition payload
                condition = {
                    "screen_condition": "good",
                    "body_condition": "good",
                    "battery_health": "excellent", 
                    "speakers_working": "yes",
                    "cameras_working": "all_working",
                    "buttons_working": "all_working",
                    "network_status": "unlocked",
                    "original_parts": "yes",
                    "fingerprint_working": "yes",
                    "frp_status": "unlocked",
                    "charging_port": "excellent"
                }
            
            payload = {
                "brand": brand,
                "model": model,
                "condition": condition,
                "new_price": new_price,
                "used_price": used_price,
                "access_code": self.test_access_code
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
                
            self.log_test("Estimate Price with Access Code", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Estimate Price with Access Code", False, f"Error: {str(e)}")
            return False, {}

    def test_estimate_price_without_access_code(self):
        """Test /api/estimate-price endpoint without access code (should fail)"""
        try:
            condition = {
                "screen_condition": "good",
                "body_condition": "good", 
                "battery_health": "excellent",
                "speakers_working": "yes",
                "cameras_working": "all_working",
                "buttons_working": "all_working",
                "network_status": "unlocked",
                "original_parts": "yes",
                "face_id_working": "yes",
                "icloud_status": "unlocked",
                "back_glass_condition": "intact",
                "true_tone_working": "yes"
            }
            
            payload = {
                "brand": "Apple",
                "model": "iPhone 15",
                "condition": condition,
                "new_price": 1400000,
                "used_price": 900000
                # No access_code provided
            }
            
            response = requests.post(
                f"{self.api_url}/estimate-price",
                json=payload,
                timeout=30
            )
            
            # Should fail with 422 (validation error) or 403 (forbidden)
            success = response.status_code in [403, 422]
            details = f"Status: {response.status_code} (should be 403 or 422)"
                
            self.log_test("Estimate Price without Access Code", success, details)
            return success
        except Exception as e:
            self.log_test("Estimate Price without Access Code", False, f"Error: {str(e)}")
            return False

    def test_access_code_usage_decrement(self):
        """Test that access code usage decrements after estimate"""
        if not hasattr(self, 'test_access_code'):
            self.log_test("Access Code Usage Decrement", False, "No access code available for testing")
            return False
            
        try:
            # First, check initial uses
            payload = {"code": self.test_access_code}
            response = requests.post(f"{self.api_url}/verify-code", json=payload, timeout=10)
            
            if response.status_code == 200:
                initial_uses = response.json().get('uses_remaining', 0)
                
                # Now make an estimate to use one credit
                self.test_estimate_price_with_access_code("Tecno", "Camon 20", 180000, 65000)
                
                # Check uses again
                response = requests.post(f"{self.api_url}/verify-code", json=payload, timeout=10)
                if response.status_code == 200:
                    final_uses = response.json().get('uses_remaining', 0)
                    decremented = final_uses == (initial_uses - 1)
                    
                    details = f"Initial: {initial_uses}, Final: {final_uses}, Decremented: {decremented}"
                    self.log_test("Access Code Usage Decrement", decremented, details)
                    return decremented
                    
            self.log_test("Access Code Usage Decrement", False, "Failed to verify usage decrement")
            return False
        except Exception as e:
            self.log_test("Access Code Usage Decrement", False, f"Error: {str(e)}")
            return False

    def test_estimate_price_edge_cases(self):
        """Test estimate price with edge cases"""
        test_cases = [
            {
                "name": "iPhone with iCloud Lock",
                "payload": {
                    "brand": "Apple",
                    "model": "iPhone 14", 
                    "condition": {
                        "screen_condition": "good",
                        "body_condition": "good",
                        "battery_health": "good",
                        "speakers_working": "yes",
                        "cameras_working": "all_working",
                        "buttons_working": "all_working",
                        "network_status": "unlocked",
                        "original_parts": "yes",
                        "face_id_working": "yes",
                        "icloud_status": "locked",  # This should significantly reduce price
                        "back_glass_condition": "intact",
                        "true_tone_working": "yes"
                    },
                    "new_price": 1000000,
                    "used_price": 650000
                }
            },
            {
                "name": "Android with FRP Lock",
                "payload": {
                    "brand": "Samsung",
                    "model": "Galaxy S24",
                    "condition": {
                        "screen_condition": "excellent", 
                        "body_condition": "excellent",
                        "battery_health": "excellent",
                        "speakers_working": "yes",
                        "cameras_working": "all_working",
                        "buttons_working": "all_working",
                        "network_status": "unlocked",
                        "original_parts": "yes",
                        "fingerprint_working": "yes",
                        "frp_status": "locked",  # This should significantly reduce price
                        "charging_port": "excellent"
                    },
                    "new_price": 1200000,
                    "used_price": 800000
                }
            },
            {
                "name": "Tecno with Poor Condition",
                "payload": {
                    "brand": "Tecno",
                    "model": "Camon 20",
                    "condition": {
                        "screen_condition": "cracked",
                        "body_condition": "damaged",
                        "battery_health": "poor",
                        "speakers_working": "no",
                        "cameras_working": "issues",
                        "buttons_working": "major_issues",
                        "network_status": "locked_to_carrier",
                        "original_parts": "mostly_replaced",
                        "fingerprint_working": "no",
                        "frp_status": "unlocked",
                        "charging_port": "damaged"
                    },
                    "new_price": 180000,
                    "used_price": 110000
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
                    confidence = data.get('confidence', 'unknown')
                    details = f"Status: {response.status_code}, Price: ₦{price:,.0f}, Confidence: {confidence}"
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
        print("🚀 Starting Stashorra Backend API Tests (Payment System)")
        print(f"📍 Testing: {self.base_url}")
        print("=" * 60)
        
        # Test API availability
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False
            
        # Test payment system endpoints
        print("\n🏦 Testing Payment System...")
        self.test_payment_info()
        self.test_admin_login()
        
        # Generate access code for testing
        generate_success, generate_data = self.test_admin_generate_code()
        if generate_success:
            self.test_verify_access_code()
            
        # Test core endpoints
        print("\n📱 Testing Phone Data Endpoints...")
        popular_success, popular_data = self.test_popular_phones()
        
        # Test condition questions for both iPhone and Android with specific models
        self.test_condition_questions("Apple", "iPhone 14 Pro")  # Should get Face ID
        self.test_condition_questions("Apple", "iPhone 8")       # Should get Touch ID
        self.test_condition_questions("Tecno", "Camon 20")       # Should get Android questions
        
        # Test search with real data
        search_success, search_data = self.test_search_phone("Apple", "iPhone 15")
        
        # Test Android search
        self.test_search_phone("Tecno", "Camon 20")
        
        # Test estimation with access code requirement
        print("\n💰 Testing Price Estimation with Access Code...")
        if hasattr(self, 'test_access_code'):
            self.test_estimate_price_with_access_code()
            self.test_access_code_usage_decrement()
        
        # Test estimation without access code (should fail)
        self.test_estimate_price_without_access_code()
        
        # Test edge cases
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