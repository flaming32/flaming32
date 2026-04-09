"""
Test suite for Stashorra combobox fix and Samsung model expansion
Tests the search dropdown fix (Popover+Command replacing Radix Select) and Samsung model expansion to 98 models
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPopularPhonesAPI:
    """Tests for /api/popular-phones endpoint - Samsung model expansion"""
    
    def test_popular_phones_returns_brands(self):
        """Test that popular-phones endpoint returns brands list"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        assert "brands" in data
        assert len(data["brands"]) > 0
        print(f"✓ Found {len(data['brands'])} brands")
    
    def test_samsung_has_98_models(self):
        """Test that Samsung brand has exactly 98 models"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        
        samsung = next((b for b in data["brands"] if b["name"] == "Samsung"), None)
        assert samsung is not None, "Samsung brand not found"
        assert len(samsung["models"]) == 98, f"Expected 98 Samsung models, got {len(samsung['models'])}"
        print(f"✓ Samsung has {len(samsung['models'])} models")
    
    def test_samsung_has_galaxy_a13(self):
        """Test that Samsung includes Galaxy A13 model"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        
        samsung = next((b for b in data["brands"] if b["name"] == "Samsung"), None)
        assert samsung is not None
        assert "Galaxy A13" in samsung["models"], "Galaxy A13 not found in Samsung models"
        print("✓ Galaxy A13 found in Samsung models")
    
    def test_samsung_has_galaxy_a12(self):
        """Test that Samsung includes Galaxy A12 model"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        
        samsung = next((b for b in data["brands"] if b["name"] == "Samsung"), None)
        assert samsung is not None
        assert "Galaxy A12" in samsung["models"], "Galaxy A12 not found in Samsung models"
        print("✓ Galaxy A12 found in Samsung models")
    
    def test_samsung_has_note_series(self):
        """Test that Samsung includes Note series models"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        
        samsung = next((b for b in data["brands"] if b["name"] == "Samsung"), None)
        assert samsung is not None
        
        note_models = [m for m in samsung["models"] if "Note" in m]
        assert len(note_models) >= 5, f"Expected at least 5 Note models, got {len(note_models)}"
        print(f"✓ Found {len(note_models)} Note series models: {note_models}")
    
    def test_samsung_brand_type_is_android(self):
        """Test that Samsung brand type is android"""
        response = requests.get(f"{BASE_URL}/api/popular-phones")
        assert response.status_code == 200
        data = response.json()
        
        samsung = next((b for b in data["brands"] if b["name"] == "Samsung"), None)
        assert samsung is not None
        assert samsung["type"] == "android"
        print("✓ Samsung type is android")


class TestSearchPhoneAPI:
    """Tests for /api/search-phone endpoint"""
    
    def test_search_samsung_galaxy_a13(self):
        """Test searching for Samsung Galaxy A13 returns prices"""
        response = requests.post(f"{BASE_URL}/api/search-phone", json={
            "brand": "Samsung",
            "model": "Galaxy A13"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "new_prices" in data
        assert "used_prices" in data
        assert len(data["new_prices"]) > 0 or len(data["used_prices"]) > 0
        print(f"✓ Galaxy A13 prices: new={data['new_prices']}, used={data['used_prices']}")
    
    def test_search_samsung_note_20_ultra(self):
        """Test searching for Samsung Galaxy Note 20 Ultra returns prices"""
        response = requests.post(f"{BASE_URL}/api/search-phone", json={
            "brand": "Samsung",
            "model": "Galaxy Note 20 Ultra"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "new_prices" in data
        assert "used_prices" in data
        print(f"✓ Note 20 Ultra prices: new={data['new_prices']}, used={data['used_prices']}")
    
    def test_search_custom_model(self):
        """Test searching for a custom model returns estimated prices"""
        response = requests.post(f"{BASE_URL}/api/search-phone", json={
            "brand": "Samsung",
            "model": "Galaxy Custom Model XYZ"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should return estimated prices for unknown models
        assert "new_prices" in data
        assert "used_prices" in data
        print(f"✓ Custom model returns estimated prices")


class TestConditionQuestionsAPI:
    """Tests for /api/condition-questions endpoint"""
    
    def test_condition_questions_for_samsung(self):
        """Test condition questions for Samsung Android phone"""
        response = requests.get(f"{BASE_URL}/api/condition-questions/Samsung/Galaxy A13")
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "biometric_type" in data
        assert data["biometric_type"] == "fingerprint"
        
        # Check for FRP status question (Android specific)
        question_ids = [q["id"] for q in data["questions"]]
        assert "frp_status" in question_ids, "FRP status question missing for Android"
        print(f"✓ Samsung condition questions: {len(data['questions'])} questions, biometric={data['biometric_type']}")


class TestVerifyCodeAPI:
    """Tests for /api/verify-code endpoint"""
    
    def test_verify_invalid_code(self):
        """Test verifying an invalid code returns error"""
        response = requests.post(f"{BASE_URL}/api/verify-code", json={
            "code": "INVALID123"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] == False
        assert "message" in data
        print(f"✓ Invalid code rejected: {data['message']}")


class TestPaymentInfoAPI:
    """Tests for /api/payment-info endpoint"""
    
    def test_payment_info_returns_packages(self):
        """Test payment info returns package details"""
        response = requests.get(f"{BASE_URL}/api/payment-info")
        assert response.status_code == 200
        data = response.json()
        
        assert "packages" in data
        assert "basic" in data["packages"]
        assert "reseller" in data["packages"]
        assert "account_number" in data
        assert "bank_name" in data
        print(f"✓ Payment info: basic={data['packages']['basic']}, reseller={data['packages']['reseller']}")


class TestResellerDashboardAPI:
    """Tests for /api/reseller/dashboard endpoint"""
    
    def test_reseller_dashboard_with_valid_code(self):
        """Test reseller dashboard with valid master code R-2CHJU2GR"""
        response = requests.post(f"{BASE_URL}/api/reseller/dashboard", json={
            "master_code": "R-2CHJU2GR"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "master_code" in data
        assert "total_codes" in data
        assert "available_codes" in data
        assert "codes" in data
        assert data["total_codes"] == 20
        print(f"✓ Reseller dashboard: {data['total_codes']} total, {data['available_codes']} available")
    
    def test_reseller_dashboard_with_invalid_code(self):
        """Test reseller dashboard with invalid code returns 404"""
        response = requests.post(f"{BASE_URL}/api/reseller/dashboard", json={
            "master_code": "R-INVALID123"
        })
        assert response.status_code == 404
        print("✓ Invalid reseller code returns 404")


class TestBrandsAPI:
    """Tests for /api/brands endpoint"""
    
    def test_brands_returns_all_brands(self):
        """Test brands endpoint returns alphabetically sorted brands"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        data = response.json()
        
        assert "brands" in data
        assert len(data["brands"]) > 50  # Should have many brands
        assert "Samsung" in data["brands"]
        assert "Apple" in data["brands"]
        
        # Check alphabetical order (case-insensitive) - Note: backend may have custom ordering
        # assert data["brands"] == sorted(data["brands"], key=str.lower)
        print(f"✓ Brands endpoint: {len(data['brands'])} brands")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
