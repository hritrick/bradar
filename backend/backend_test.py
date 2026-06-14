"""
Business Radar AI - Backend API Test Suite
Tests all endpoints with proper authentication and RBAC
"""
import requests
import sys
import json
from datetime import datetime
import time

BASE_URL = "https://ai-insights-hub-48.preview.emergentagent.com/api"

class APITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.admin_token = None
        self.analyst_token = None
        self.subscriber_token = None
        self.test_business_id = None
        self.test_user_id = None
        self.failed_tests = []
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test(self, name, method, endpoint, expected_status, token=None, data=None, files=None, params=None):
        """Run a single API test"""
        url = f"{BASE_URL}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        self.tests_run += 1
        self.log(f"Test #{self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                self.log(f"❌ Unknown method: {method}", "ERROR")
                self.tests_failed += 1
                return False, {}
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
            else:
                self.tests_failed += 1
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text[:200]}", "ERROR")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
            
            try:
                return success, response.json() if response.text else {}
            except:
                return success, {"raw": response.text}
                
        except Exception as e:
            self.tests_failed += 1
            self.log(f"❌ FAILED - Exception: {str(e)}", "ERROR")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("=" * 80)
        self.log("BUSINESS RADAR AI - BACKEND API TEST SUITE")
        self.log("=" * 80)
        
        # 1. Health Check
        self.log("\n### 1. HEALTH CHECK ###")
        self.test("API Health", "GET", "", 200)
        
        # 2. Authentication Tests
        self.log("\n### 2. AUTHENTICATION TESTS ###")
        
        # Login as Admin
        success, response = self.test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.admin@businessradar.ai", "password": "RadarTest@2025"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log(f"   Admin token obtained: {self.admin_token[:20]}...")
        
        # Login as Analyst
        success, response = self.test(
            "Analyst Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.analyst@businessradar.ai", "password": "AnalystTest@2025"}
        )
        if success and 'access_token' in response:
            self.analyst_token = response['access_token']
            self.log(f"   Analyst token obtained: {self.analyst_token[:20]}...")
        
        # Login as Subscriber
        success, response = self.test(
            "Subscriber Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.subscriber@businessradar.ai", "password": "SubTest@2025"}
        )
        if success and 'access_token' in response:
            self.subscriber_token = response['access_token']
            self.log(f"   Subscriber token obtained: {self.subscriber_token[:20]}...")
        
        # Test bad credentials
        self.test(
            "Login with bad credentials",
            "POST",
            "auth/login",
            401,
            data={"email": "test.admin@businessradar.ai", "password": "WrongPassword"}
        )
        
        # Get current user
        if self.admin_token:
            self.test("Get current user (Admin)", "GET", "auth/me", 200, token=self.admin_token)
        
        # Google OAuth status
        self.test("Google OAuth status", "GET", "auth/google/status", 200)
        
        # 3. Dashboard Tests
        self.log("\n### 3. DASHBOARD TESTS ###")
        if self.admin_token:
            self.test("Get Dashboard KPIs", "GET", "dashboard", 200, token=self.admin_token)
        
        # 4. Users CRUD (Admin only)
        self.log("\n### 4. USERS CRUD (ADMIN ONLY) ###")
        if self.admin_token:
            # List users
            success, response = self.test("List Users (Admin)", "GET", "users", 200, token=self.admin_token)
            
            # Create user
            success, response = self.test(
                "Create User (Admin)",
                "POST",
                "users",
                201,
                token=self.admin_token,
                data={
                    "email": f"test.user.{int(time.time())}@businessradar.ai",
                    "name": "Test User",
                    "role": "Analyst"
                }
            )
            if success and 'id' in response:
                self.test_user_id = response['id']
                self.log(f"   Created user ID: {self.test_user_id}")
            
            # Update user (if created)
            if self.test_user_id:
                self.test(
                    "Update User (Admin)",
                    "PATCH",
                    f"users/{self.test_user_id}",
                    200,
                    token=self.admin_token,
                    data={"role": "Subscriber"}
                )
            
            # Test RBAC - Analyst cannot access users
            if self.analyst_token:
                self.test("List Users (Analyst - should fail)", "GET", "users", 403, token=self.analyst_token)
        
        # 5. Businesses CRUD
        self.log("\n### 5. BUSINESSES CRUD ###")
        if self.admin_token:
            # List businesses
            success, response = self.test("List Businesses", "GET", "businesses", 200, token=self.admin_token)
            
            # Get distinct values
            self.test("Get Distinct Cities/States", "GET", "businesses/distinct", 200, token=self.admin_token)
            
            # Create business (this will trigger AI enrichment - may take 6-10 seconds)
            self.log("   Creating business (AI enrichment may take 6-10 seconds)...")
            success, response = self.test(
                "Create Business",
                "POST",
                "businesses",
                201,
                token=self.admin_token,
                data={
                    "business_name": f"Test Business {int(time.time())}",
                    "registration_date": "2025-01-15",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001",
                    "category": "Technology",
                    "source": "manual"
                }
            )
            if success and 'id' in response:
                self.test_business_id = response['id']
                self.log(f"   Created business ID: {self.test_business_id}")
            
            # Get business detail
            if self.test_business_id:
                self.test("Get Business Detail", "GET", f"businesses/{self.test_business_id}", 200, token=self.admin_token)
                
                # Update business
                self.test(
                    "Update Business",
                    "PATCH",
                    f"businesses/{self.test_business_id}",
                    200,
                    token=self.admin_token,
                    data={"notes": "Updated via test"}
                )
                
                # Re-run AI enrichment
                self.log("   Re-running AI enrichment (may take 6-10 seconds)...")
                self.test(
                    "Re-run AI Enrichment",
                    "POST",
                    f"businesses/{self.test_business_id}/enrich",
                    200,
                    token=self.admin_token
                )
            
            # Test filters
            self.test("Filter Businesses by City", "GET", "businesses", 200, token=self.admin_token, params={"city": "Mumbai"})
            
            # Test RBAC - Subscriber cannot create
            if self.subscriber_token:
                self.test(
                    "Create Business (Subscriber - should fail)",
                    "POST",
                    "businesses",
                    403,
                    token=self.subscriber_token,
                    data={"business_name": "Test", "city": "Mumbai"}
                )
        
        # 6. Discovery Tests
        self.log("\n### 6. DISCOVERY TESTS ###")
        if self.admin_token:
            # List connectors
            self.test("List Discovery Connectors", "GET", "discovery/connectors", 200, token=self.admin_token)
            
            # Run sample_seed discovery (may take time due to AI)
            self.log("   Running sample_seed discovery (may take 20-30 seconds for 3 businesses)...")
            self.test(
                "Run Sample Seed Discovery",
                "POST",
                "discovery/run",
                200,
                token=self.admin_token,
                data={"source": "sample_seed", "limit": 3}
            )
        
        # 7. Reports Tests
        self.log("\n### 7. REPORTS TESTS ###")
        if self.admin_token:
            # List reports
            self.test("List Reports", "GET", "reports", 200, token=self.admin_token)
            
            # Get today's report
            self.test("Get Today's Report", "GET", "reports/today", 200, token=self.admin_token)
            
            # Generate report
            self.log("   Generating report (may take a few seconds)...")
            success, response = self.test("Generate Report", "POST", "reports/generate", 200, token=self.admin_token, data={})
            
            # Get report detail
            if success and 'id' in response:
                report_id = response['id']
                self.test("Get Report Detail", "GET", f"reports/{report_id}", 200, token=self.admin_token)
        
        # 8. Settings (Admin only)
        self.log("\n### 8. SETTINGS (ADMIN ONLY) ###")
        if self.admin_token:
            # Get settings
            self.test("Get Settings (Admin)", "GET", "settings", 200, token=self.admin_token)
            
            # Update settings
            self.test(
                "Update Settings (Admin)",
                "PATCH",
                "settings",
                200,
                token=self.admin_token,
                data={"settings": {"sender_name": "Business Radar AI Test"}}
            )
            
            # Test RBAC
            if self.analyst_token:
                self.test("Get Settings (Analyst - should fail)", "GET", "settings", 403, token=self.analyst_token)
        
        # 9. Audit Logs (Admin only)
        self.log("\n### 9. AUDIT LOGS (ADMIN ONLY) ###")
        if self.admin_token:
            self.test("Get Audit Logs (Admin)", "GET", "audit-logs", 200, token=self.admin_token)
            
            # Filter by action
            self.test("Filter Audit Logs by Action", "GET", "audit-logs", 200, token=self.admin_token, params={"action": "login"})
            
            # Test RBAC
            if self.analyst_token:
                self.test("Get Audit Logs (Analyst - should fail)", "GET", "audit-logs", 403, token=self.analyst_token)
        
        # 10. Preferences
        self.log("\n### 10. PREFERENCES ###")
        if self.admin_token:
            # Get preferences
            self.test("Get Preferences", "GET", "preferences", 200, token=self.admin_token)
            
            # Update preferences
            self.test(
                "Update Preferences",
                "PATCH",
                "preferences",
                200,
                token=self.admin_token,
                data={"daily_report_enabled": True, "weekly_report_enabled": False}
            )
        
        # 11. Scheduler (Admin only)
        self.log("\n### 11. SCHEDULER (ADMIN ONLY) ###")
        if self.admin_token:
            # Get scheduler status
            self.test("Get Scheduler Status (Admin)", "GET", "scheduler/status", 200, token=self.admin_token)
            
            # Run scheduler now
            self.log("   Running scheduler job now (may take a few seconds)...")
            self.test("Run Scheduler Now (Admin)", "POST", "scheduler/run-now", 200, token=self.admin_token)
            
            # Test RBAC
            if self.analyst_token:
                self.test("Get Scheduler Status (Analyst - should fail)", "GET", "scheduler/status", 403, token=self.analyst_token)
        
        # 12. CSV Upload Test
        self.log("\n### 12. CSV UPLOAD TEST ###")
        if self.admin_token:
            # Create a small test CSV
            csv_content = """business_name,city,state,category,registration_date,pincode
Test CSV Business 1,Mumbai,Maharashtra,Technology,2025-01-10,400001
Test CSV Business 2,Thane,Maharashtra,Retail,2025-01-11,400601
Test CSV Business 1,Mumbai,Maharashtra,Technology,2025-01-10,400001"""
            
            # Preview CSV
            self.log("   Testing CSV preview...")
            success, response = self.test(
                "CSV Upload Preview",
                "POST",
                "businesses/upload-csv",
                200,
                token=self.admin_token,
                data={"preview": "true"},
                files={"file": ("test.csv", csv_content, "text/csv")}
            )
            
            # Upload CSV (actual ingestion)
            self.log("   Testing CSV ingestion (may take time for AI enrichment)...")
            success, response = self.test(
                "CSV Upload Ingestion",
                "POST",
                "businesses/upload-csv",
                200,
                token=self.admin_token,
                data={"preview": "false"},
                files={"file": ("test.csv", csv_content, "text/csv")}
            )
        
        # 13. Password Reset Test
        self.log("\n### 13. PASSWORD RESET TEST ###")
        if self.analyst_token:
            # Test password reset with correct current password
            self.test(
                "Password Reset (Analyst)",
                "POST",
                "auth/reset-password",
                200,
                token=self.analyst_token,
                data={
                    "current_password": "AnalystTest@2025",
                    "new_password": "NewAnalystPass@2025"
                }
            )
            
            # Reset back to original password
            self.test(
                "Password Reset Back (Analyst)",
                "POST",
                "auth/reset-password",
                200,
                token=self.analyst_token,
                data={
                    "current_password": "NewAnalystPass@2025",
                    "new_password": "AnalystTest@2025"
                }
            )
            
            # Test with wrong current password
            self.test(
                "Password Reset Wrong Password (should fail)",
                "POST",
                "auth/reset-password",
                400,
                token=self.analyst_token,
                data={
                    "current_password": "WrongPassword",
                    "new_password": "NewPass@2025"
                }
            )
        
        # 14. Cleanup - Delete test user
        if self.admin_token and self.test_user_id:
            self.log("\n### 14. CLEANUP ###")
            self.test("Delete Test User", "DELETE", f"users/{self.test_user_id}", 200, token=self.admin_token)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "=" * 80)
        self.log("TEST SUMMARY")
        self.log("=" * 80)
        self.log(f"Total Tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed} ✅")
        self.log(f"Failed: {self.tests_failed} ❌")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            self.log("\n" + "=" * 80)
            self.log("FAILED TESTS DETAILS")
            self.log("=" * 80)
            for i, failure in enumerate(self.failed_tests, 1):
                self.log(f"\n{i}. {failure.get('test', 'Unknown')}")
                if 'error' in failure:
                    self.log(f"   Error: {failure['error']}")
                else:
                    self.log(f"   Expected: {failure.get('expected')}, Got: {failure.get('actual')}")
                    self.log(f"   Response: {failure.get('response', 'N/A')}")
        
        self.log("\n" + "=" * 80)
        return 0 if self.tests_failed == 0 else 1


if __name__ == "__main__":
    tester = APITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
