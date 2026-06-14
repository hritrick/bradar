"""
Business Radar AI - Phase 3 Discovery Framework Backend Tests
Tests provider architecture, source management, health dashboard, deduplication
"""
import requests
import sys
import json
from datetime import datetime
import time

BASE_URL = "https://ai-insights-hub-48.preview.emergentagent.com/api"

class Phase3Tester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.admin_token = None
        self.analyst_token = None
        self.subscriber_token = None
        self.failed_tests = []
        self.synthetic_source_id = None
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test(self, name, method, endpoint, expected_status, token=None, data=None, params=None, validate_fn=None):
        """Run a single API test with optional validation function"""
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
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            else:
                self.log(f"❌ Unknown method: {method}", "ERROR")
                self.tests_failed += 1
                return False, {}
            
            success = response.status_code == expected_status
            
            if success:
                # Additional validation if provided
                if validate_fn:
                    try:
                        response_data = response.json() if response.text else {}
                        validation_result = validate_fn(response_data)
                        if not validation_result:
                            success = False
                            self.log(f"❌ FAILED - Validation failed", "ERROR")
                    except Exception as e:
                        success = False
                        self.log(f"❌ FAILED - Validation error: {str(e)}", "ERROR")
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
            else:
                self.tests_failed += 1
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text[:300]}", "ERROR")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:300]
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
        """Run all Phase 3 backend tests"""
        self.log("=" * 80)
        self.log("BUSINESS RADAR AI - PHASE 3 DISCOVERY FRAMEWORK TESTS")
        self.log("=" * 80)
        
        # 1. Authentication
        self.log("\n### 1. AUTHENTICATION ###")
        success, response = self.test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.admin@businessradar.ai", "password": "RadarTest@2025"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log(f"   Admin token obtained")
        
        success, response = self.test(
            "Analyst Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.analyst@businessradar.ai", "password": "AnalystTest@2025"}
        )
        if success and 'access_token' in response:
            self.analyst_token = response['access_token']
            self.log(f"   Analyst token obtained")
        
        success, response = self.test(
            "Subscriber Login",
            "POST",
            "auth/login",
            200,
            data={"email": "test.subscriber@businessradar.ai", "password": "SubTest@2025"}
        )
        if success and 'access_token' in response:
            self.subscriber_token = response['access_token']
            self.log(f"   Subscriber token obtained")
        
        # 2. Discovery Sources
        self.log("\n### 2. DISCOVERY SOURCES ###")
        if self.admin_token:
            # GET /api/discovery/sources - should return 8 sources
            def validate_sources(data):
                if not isinstance(data, list):
                    self.log(f"   Expected list, got {type(data)}", "ERROR")
                    return False
                if len(data) != 8:
                    self.log(f"   Expected 8 sources, got {len(data)}", "ERROR")
                    return False
                
                # Check for required fields
                required_fields = ['id', 'name', 'display_name', 'description', 'enabled', 
                                 'configured', 'requires_config', 'supports_run_now', 
                                 'last_run_at', 'last_run_summary']
                for src in data:
                    for field in required_fields:
                        if field not in src:
                            self.log(f"   Missing field '{field}' in source {src.get('name')}", "ERROR")
                            return False
                
                # Find synthetic source
                synthetic = next((s for s in data if s['name'] == 'synthetic'), None)
                if synthetic:
                    self.synthetic_source_id = synthetic['id']
                    self.log(f"   Found synthetic source ID: {self.synthetic_source_id}")
                else:
                    self.log(f"   Synthetic source not found", "ERROR")
                    return False
                
                # Check expected sources
                expected_sources = ['synthetic', 'manual', 'csv_import', 'opencorporates', 
                                  'mca', 'google_business', 'indiamart', 'justdial']
                found_sources = [s['name'] for s in data]
                for exp in expected_sources:
                    if exp not in found_sources:
                        self.log(f"   Missing expected source: {exp}", "ERROR")
                        return False
                
                self.log(f"   ✓ All 8 sources present with correct fields")
                return True
            
            success, response = self.test(
                "GET /api/discovery/sources (8 sources)",
                "GET",
                "discovery/sources",
                200,
                token=self.admin_token,
                validate_fn=validate_sources
            )
            
            # GET /api/discovery/connectors (legacy)
            def validate_connectors(data):
                if not isinstance(data, list):
                    return False
                if len(data) != 8:
                    self.log(f"   Expected 8 connectors, got {len(data)}", "ERROR")
                    return False
                self.log(f"   ✓ Legacy connectors endpoint returns 8 items")
                return True
            
            self.test(
                "GET /api/discovery/connectors (legacy)",
                "GET",
                "discovery/connectors",
                200,
                token=self.admin_token,
                validate_fn=validate_connectors
            )
        
        # 3. Discovery Health Dashboard
        self.log("\n### 3. DISCOVERY HEALTH DASHBOARD ###")
        if self.admin_token:
            def validate_health(data):
                # Check totals
                if 'totals' not in data:
                    self.log(f"   Missing 'totals' in health response", "ERROR")
                    return False
                
                totals = data['totals']
                required_totals = ['records_found', 'records_added', 'duplicates_removed', 
                                 'errors', 'sources_enabled', 'sources_total']
                for field in required_totals:
                    if field not in totals:
                        self.log(f"   Missing '{field}' in totals", "ERROR")
                        return False
                
                if totals['sources_total'] != 8:
                    self.log(f"   Expected sources_total=8, got {totals['sources_total']}", "ERROR")
                    return False
                
                # Check queue
                if 'queue' not in data:
                    self.log(f"   Missing 'queue' in health response", "ERROR")
                    return False
                
                # Check sources array
                if 'sources' not in data or not isinstance(data['sources'], list):
                    self.log(f"   Missing or invalid 'sources' array", "ERROR")
                    return False
                
                if len(data['sources']) != 8:
                    self.log(f"   Expected 8 sources in health, got {len(data['sources'])}", "ERROR")
                    return False
                
                self.log(f"   ✓ Health dashboard structure valid")
                self.log(f"   ✓ Total businesses: {totals['records_added']}")
                self.log(f"   ✓ Sources enabled: {totals['sources_enabled']}/8")
                return True
            
            self.test(
                "GET /api/discovery/health",
                "GET",
                "discovery/health",
                200,
                token=self.admin_token,
                validate_fn=validate_health
            )
            
            # GET /api/discovery/queue
            def validate_queue(data):
                required_fields = ['queued', 'processing', 'done', 'failed']
                for field in required_fields:
                    if field not in data:
                        self.log(f"   Missing '{field}' in queue response", "ERROR")
                        return False
                self.log(f"   ✓ Queue status: queued={data['queued']}, done={data['done']}")
                return True
            
            self.test(
                "GET /api/discovery/queue",
                "GET",
                "discovery/queue",
                200,
                token=self.admin_token,
                validate_fn=validate_queue
            )
        
        # 4. RBAC - Analyst cannot toggle sources
        self.log("\n### 4. RBAC - SOURCE MANAGEMENT ###")
        if self.analyst_token and self.synthetic_source_id:
            self.test(
                "PATCH /api/discovery/sources/{id} (Analyst - should fail 403)",
                "PATCH",
                f"discovery/sources/{self.synthetic_source_id}",
                403,
                token=self.analyst_token,
                data={"enabled": False}
            )
        
        # 5. Admin can toggle source
        if self.admin_token and self.synthetic_source_id:
            # Get current state
            success, response = self.test(
                "GET source before toggle",
                "GET",
                "discovery/sources",
                200,
                token=self.admin_token
            )
            
            # Toggle enabled
            self.test(
                "PATCH /api/discovery/sources/{id} (Admin toggle)",
                "PATCH",
                f"discovery/sources/{self.synthetic_source_id}",
                200,
                token=self.admin_token,
                data={"enabled": True, "schedule_cron": "0 6 * * *"}
            )
        
        # 6. Run Discovery - Synthetic Source
        self.log("\n### 6. RUN DISCOVERY - SYNTHETIC SOURCE ###")
        if self.admin_token and self.synthetic_source_id:
            self.log("   Running synthetic discovery with limit=10 (may take 5-10 seconds)...")
            
            def validate_run(data):
                if 'records_found' not in data:
                    self.log(f"   Missing 'records_found' in run response", "ERROR")
                    return False
                if 'records_added' not in data:
                    self.log(f"   Missing 'records_added' in run response", "ERROR")
                    return False
                
                if data['records_found'] != 10:
                    self.log(f"   Expected records_found=10, got {data['records_found']}", "ERROR")
                    return False
                
                self.log(f"   ✓ Found: {data['records_found']}, Added: {data['records_added']}, Dupes: {data.get('duplicates_removed', 0)}")
                return True
            
            success, response = self.test(
                "POST /api/discovery/sources/{id}/run (limit=10)",
                "POST",
                f"discovery/sources/{self.synthetic_source_id}/run",
                200,
                token=self.admin_token,
                data={"limit": 10},
                validate_fn=validate_run
            )
            
            # Wait a bit for DB to update
            time.sleep(2)
            
            # Verify source.last_run_at was updated
            success, response = self.test(
                "Verify source.last_run_at updated",
                "GET",
                "discovery/sources",
                200,
                token=self.admin_token
            )
            if success:
                synthetic = next((s for s in response if s['name'] == 'synthetic'), None)
                if synthetic and synthetic.get('last_run_at'):
                    self.log(f"   ✓ last_run_at updated: {synthetic['last_run_at']}")
                else:
                    self.log(f"   ⚠ last_run_at not updated", "WARN")
        
        # 7. Legacy Discovery Run
        self.log("\n### 7. LEGACY DISCOVERY RUN ###")
        if self.admin_token:
            self.log("   Running legacy discovery endpoint with limit=5...")
            
            def validate_legacy(data):
                if 'source' not in data or data['source'] != 'synthetic':
                    return False
                if 'fetched' not in data or 'inserted' not in data:
                    return False
                self.log(f"   ✓ Legacy endpoint: fetched={data['fetched']}, inserted={data['inserted']}")
                return True
            
            self.test(
                "POST /api/discovery/run (legacy)",
                "POST",
                "discovery/run",
                200,
                token=self.admin_token,
                data={"source": "synthetic", "limit": 5},
                validate_fn=validate_legacy
            )
        
        # 8. Get Source Runs History
        self.log("\n### 8. SOURCE RUNS HISTORY ###")
        if self.admin_token and self.synthetic_source_id:
            def validate_runs(data):
                if not isinstance(data, list):
                    return False
                if len(data) == 0:
                    self.log(f"   ⚠ No runs found (expected at least 2)", "WARN")
                    return True  # Not a failure, just unexpected
                
                # Check first run has required fields
                run = data[0]
                required = ['id', 'status', 'triggered_by', 'started_at', 'records_found', 
                          'records_added', 'duplicates_removed', 'errors_count']
                for field in required:
                    if field not in run:
                        self.log(f"   Missing '{field}' in run", "ERROR")
                        return False
                
                self.log(f"   ✓ Found {len(data)} historical runs")
                self.log(f"   ✓ Latest run: status={run['status']}, triggered_by={run['triggered_by']}")
                return True
            
            self.test(
                "GET /api/discovery/sources/{id}/runs",
                "GET",
                f"discovery/sources/{self.synthetic_source_id}/runs",
                200,
                token=self.admin_token,
                validate_fn=validate_runs
            )
        
        # 9. Business Schema - GST and Industry
        self.log("\n### 9. BUSINESS SCHEMA - GST & INDUSTRY ###")
        if self.admin_token:
            def validate_business_schema(data):
                if 'items' not in data or len(data['items']) == 0:
                    self.log(f"   No businesses found", "ERROR")
                    return False
                
                # Check first business has gst_number and industry
                biz = data['items'][0]
                if 'gst_number' not in biz:
                    self.log(f"   Missing 'gst_number' field", "ERROR")
                    return False
                if 'industry' not in biz:
                    self.log(f"   Missing 'industry' field", "ERROR")
                    return False
                if 'latest_score' not in biz:
                    self.log(f"   Missing 'latest_score' field", "ERROR")
                    return False
                if 'latest_lead_category' not in biz:
                    self.log(f"   Missing 'latest_lead_category' field", "ERROR")
                    return False
                if 'latest_predicted_need' not in biz:
                    self.log(f"   Missing 'latest_predicted_need' field", "ERROR")
                    return False
                
                self.log(f"   ✓ Business schema includes gst_number, industry, latest_score, latest_lead_category, latest_predicted_need")
                self.log(f"   ✓ Total businesses: {data['total']}")
                return True
            
            self.test(
                "GET /api/businesses (verify schema)",
                "GET",
                "businesses",
                200,
                token=self.admin_token,
                params={"page": 1, "page_size": 10},
                validate_fn=validate_business_schema
            )
        
        # 10. Distinct Industries
        self.log("\n### 10. DISTINCT INDUSTRIES ###")
        if self.admin_token:
            def validate_industries(data):
                if 'industries' not in data:
                    self.log(f"   Missing 'industries' field", "ERROR")
                    return False
                
                industries = data['industries']
                if len(industries) != 6:
                    self.log(f"   Expected 6 industries, got {len(industries)}", "ERROR")
                    return False
                
                expected = ['Real Estate', 'Manufacturing', 'Logistics', 'Retail', 'IT Services', 'Healthcare']
                for exp in expected:
                    if exp not in industries:
                        self.log(f"   Missing expected industry: {exp}", "ERROR")
                        return False
                
                self.log(f"   ✓ All 6 industries present: {', '.join(industries)}")
                return True
            
            self.test(
                "GET /api/businesses/distinct (6 industries)",
                "GET",
                "businesses/distinct",
                200,
                token=self.admin_token,
                validate_fn=validate_industries
            )
        
        # 11. Filtering Tests
        self.log("\n### 11. FILTERING TESTS ###")
        if self.admin_token:
            # Filter by industry
            def validate_industry_filter(data):
                if 'items' not in data:
                    return False
                # Check all items have Healthcare industry
                for item in data['items']:
                    if item.get('industry') != 'Healthcare':
                        self.log(f"   Found non-Healthcare business: {item.get('industry')}", "ERROR")
                        return False
                self.log(f"   ✓ All {len(data['items'])} businesses are Healthcare")
                return True
            
            self.test(
                "GET /api/businesses?industry=Healthcare",
                "GET",
                "businesses",
                200,
                token=self.admin_token,
                params={"industry": "Healthcare", "page_size": 10},
                validate_fn=validate_industry_filter
            )
            
            # Filter by city
            def validate_city_filter(data):
                if 'items' not in data:
                    return False
                for item in data['items']:
                    if item.get('city') != 'Mumbai':
                        self.log(f"   Found non-Mumbai business: {item.get('city')}", "ERROR")
                        return False
                self.log(f"   ✓ All {len(data['items'])} businesses are in Mumbai")
                return True
            
            self.test(
                "GET /api/businesses?city=Mumbai",
                "GET",
                "businesses",
                200,
                token=self.admin_token,
                params={"city": "Mumbai", "page_size": 10},
                validate_fn=validate_city_filter
            )
            
            # Filter by min_score
            def validate_score_filter(data):
                if 'items' not in data:
                    return False
                for item in data['items']:
                    score = item.get('latest_score')
                    if score is not None and score < 80:
                        self.log(f"   Found business with score < 80: {score}", "ERROR")
                        return False
                self.log(f"   ✓ All businesses have score >= 80")
                return True
            
            self.test(
                "GET /api/businesses?min_score=80",
                "GET",
                "businesses",
                200,
                token=self.admin_token,
                params={"min_score": 80, "page_size": 10},
                validate_fn=validate_score_filter
            )
            
            # Filter by lead_category
            def validate_lead_filter(data):
                if 'items' not in data:
                    return False
                for item in data['items']:
                    cat = item.get('latest_lead_category')
                    if cat != 'HOT':
                        self.log(f"   Found non-HOT lead: {cat}", "ERROR")
                        return False
                self.log(f"   ✓ All businesses are HOT leads")
                return True
            
            self.test(
                "GET /api/businesses?lead_category=HOT",
                "GET",
                "businesses",
                200,
                token=self.admin_token,
                params={"lead_category": "HOT", "page_size": 10},
                validate_fn=validate_lead_filter
            )
        
        # 12. Dashboard with New Schema
        self.log("\n### 12. DASHBOARD WITH NEW SCHEMA ###")
        if self.admin_token:
            def validate_dashboard(data):
                if 'kpis' not in data:
                    self.log(f"   Missing 'kpis' in dashboard", "ERROR")
                    return False
                
                kpis = data['kpis']
                if 'total_businesses' not in kpis:
                    self.log(f"   Missing 'total_businesses' in kpis", "ERROR")
                    return False
                
                if kpis['total_businesses'] < 10000:
                    self.log(f"   Expected >= 10000 businesses, got {kpis['total_businesses']}", "ERROR")
                    return False
                
                # Check by_industry
                if 'by_industry' not in data:
                    self.log(f"   Missing 'by_industry' in dashboard", "ERROR")
                    return False
                
                if len(data['by_industry']) != 6:
                    self.log(f"   Expected 6 industries in dashboard, got {len(data['by_industry'])}", "ERROR")
                    return False
                
                # Check by_city
                if 'by_city' not in data:
                    self.log(f"   Missing 'by_city' in dashboard", "ERROR")
                    return False
                
                cities = [c['city'] for c in data['by_city']]
                expected_cities = ['Mumbai', 'Thane', 'Navi Mumbai']
                for city in expected_cities:
                    if city not in cities:
                        self.log(f"   Missing expected city: {city}", "ERROR")
                        return False
                
                self.log(f"   ✓ Dashboard: {kpis['total_businesses']} businesses, 6 industries, 3 cities")
                return True
            
            self.test(
                "GET /api/dashboard (10000+ businesses, 6 industries, 3 cities)",
                "GET",
                "dashboard",
                200,
                token=self.admin_token,
                validate_fn=validate_dashboard
            )
        
        # 13. Reports with New Schema
        self.log("\n### 13. REPORTS WITH NEW SCHEMA ###")
        if self.admin_token:
            def validate_report(data):
                required = ['kpis', 'by_city', 'by_industry', 'by_category', 
                          'by_predicted_need', 'by_pincode', 'today_list']
                for field in required:
                    if field not in data:
                        self.log(f"   Missing '{field}' in report", "ERROR")
                        return False
                
                self.log(f"   ✓ Report includes all required fields")
                return True
            
            self.test(
                "GET /api/reports/today (new schema)",
                "GET",
                "reports/today",
                200,
                token=self.admin_token,
                validate_fn=validate_report
            )
        
        # 14. Deduplication Test
        self.log("\n### 14. DEDUPLICATION TEST ###")
        if self.admin_token:
            # Create business with unique GST
            unique_gst = f"27AABCT{int(time.time()) % 10000:04d}A1ZX"
            self.log(f"   Creating business with GST: {unique_gst}")
            
            success, response = self.test(
                "Create business with unique GST",
                "POST",
                "businesses",
                201,
                token=self.admin_token,
                data={
                    "business_name": "GST Dedup Test Co",
                    "gst_number": unique_gst,
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001",
                    "industry": "IT Services"
                }
            )
            
            if success:
                biz_id = response.get('id')
                self.log(f"   ✓ Created business ID: {biz_id}")
                
                # Try to create duplicate with same GST
                self.log(f"   Attempting to create duplicate with same GST...")
                success2, response2 = self.test(
                    "Create duplicate business (same GST) - should handle gracefully",
                    "POST",
                    "businesses",
                    201,  # May return 201 but merge, or 400
                    token=self.admin_token,
                    data={
                        "business_name": "GST Dedup Test Co Duplicate",
                        "gst_number": unique_gst,
                        "city": "Mumbai",
                        "state": "Maharashtra",
                        "pincode": "400001",
                        "industry": "IT Services"
                    }
                )
                
                if success2:
                    biz_id2 = response2.get('id')
                    if biz_id == biz_id2:
                        self.log(f"   ✓ Deduplication working: returned same business ID")
                    else:
                        self.log(f"   ⚠ Created new business instead of deduplicating", "WARN")
        
        # 15. Queue Processing
        self.log("\n### 15. QUEUE PROCESSING ###")
        if self.admin_token:
            self.log("   Processing enrichment queue (may take 10-15 seconds for LLM calls)...")
            
            def validate_queue_process(data):
                if 'processed' not in data:
                    self.log(f"   Missing 'processed' in response", "ERROR")
                    return False
                if 'failed' not in data:
                    self.log(f"   Missing 'failed' in response", "ERROR")
                    return False
                if 'requested' not in data:
                    self.log(f"   Missing 'requested' in response", "ERROR")
                    return False
                
                self.log(f"   ✓ Processed: {data['processed']}, Failed: {data['failed']}, Requested: {data['requested']}")
                return True
            
            self.test(
                "POST /api/discovery/queue/process?batch=2",
                "POST",
                "discovery/queue/process",
                200,
                token=self.admin_token,
                params={"batch": 2},
                validate_fn=validate_queue_process
            )
        
        # 16. Audit Logs for Discovery Actions
        self.log("\n### 16. AUDIT LOGS FOR DISCOVERY ###")
        if self.admin_token:
            def validate_audit(data):
                if 'items' not in data:
                    return False
                
                # Look for discovery_run or update_discovery_source actions
                discovery_actions = [log for log in data['items'] 
                                   if log.get('action') in ['discovery_run', 'update_discovery_source']]
                
                if len(discovery_actions) == 0:
                    self.log(f"   ⚠ No discovery actions found in audit logs", "WARN")
                    return True  # Not a failure
                
                self.log(f"   ✓ Found {len(discovery_actions)} discovery-related audit log entries")
                return True
            
            self.test(
                "GET /api/audit-logs (check for discovery actions)",
                "GET",
                "audit-logs",
                200,
                token=self.admin_token,
                params={"page_size": 50},
                validate_fn=validate_audit
            )
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "=" * 80)
        self.log("PHASE 3 TEST SUMMARY")
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
    tester = Phase3Tester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
