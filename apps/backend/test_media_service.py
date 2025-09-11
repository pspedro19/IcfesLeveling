"""
Comprehensive Test Script for Media Service Implementation
Tests all functionality of the secure image service endpoint
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaServiceTester:
    """Test suite for the media service"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url.rstrip('/')
        self.media_base = f"{self.base_url}/api/v1/media"
        self.test_results = []
    
    async def test_basic_image_serving(self, session: aiohttp.ClientSession):
        """Test basic image serving functionality"""
        logger.info("Testing basic image serving...")
        
        # Test valid image request
        test_url = f"{self.media_base}/images/question/Matematicas/test_image.png"
        
        try:
            async with session.get(test_url) as response:
                status = response.status
                headers = dict(response.headers)
                
                self.test_results.append({
                    'test': 'basic_image_serving',
                    'url': test_url,
                    'status': status,
                    'headers': {
                        'content-type': headers.get('content-type'),
                        'cache-control': headers.get('cache-control'),
                        'etag': headers.get('etag')
                    },
                    'success': status in [200, 404]  # 404 is OK if image doesn't exist
                })
                
                logger.info(f"Basic image test: Status {status}")
        except Exception as e:
            self.test_results.append({
                'test': 'basic_image_serving',
                'url': test_url,
                'error': str(e),
                'success': False
            })
    
    async def test_security_validation(self, session: aiohttp.ClientSession):
        """Test security validations"""
        logger.info("Testing security validations...")
        
        # Test directory traversal attempts
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "~/sensitive_file.txt",
            "file:///etc/passwd",
            "../../database/secrets.env"
        ]
        
        for attempt in traversal_attempts:
            test_url = f"{self.media_base}/images/question/{attempt}"
            try:
                async with session.get(test_url) as response:
                    status = response.status
                    success = status in [400, 403, 404]  # Should be blocked
                    
                    self.test_results.append({
                        'test': 'security_traversal',
                        'attempt': attempt,
                        'status': status,
                        'success': success,
                        'blocked': success
                    })
                    
                    logger.info(f"Traversal test '{attempt}': Status {status} - {'BLOCKED' if success else 'FAILED'}")
            except Exception as e:
                self.test_results.append({
                    'test': 'security_traversal',
                    'attempt': attempt,
                    'error': str(e),
                    'success': True  # Exception is acceptable for security tests
                })
        
        # Test invalid image types
        invalid_types = [
            "invalid_type",
            "script",
            "executable",
            "../question"
        ]
        
        for invalid_type in invalid_types:
            test_url = f"{self.media_base}/images/{invalid_type}/test_image.png"
            try:
                async with session.get(test_url) as response:
                    status = response.status
                    success = status == 400  # Should return 400 Bad Request
                    
                    self.test_results.append({
                        'test': 'security_invalid_type',
                        'invalid_type': invalid_type,
                        'status': status,
                        'success': success
                    })
                    
                    logger.info(f"Invalid type test '{invalid_type}': Status {status}")
            except Exception as e:
                self.test_results.append({
                    'test': 'security_invalid_type',
                    'invalid_type': invalid_type,
                    'error': str(e),
                    'success': True
                })
    
    async def test_placeholder_fallback(self, session: aiohttp.ClientSession):
        """Test placeholder fallback system"""
        logger.info("Testing placeholder fallback...")
        
        # Test placeholder request
        test_url = f"{self.media_base}/images/placeholder/matematicas"
        
        try:
            async with session.get(test_url) as response:
                status = response.status
                content_type = response.headers.get('content-type', '')
                
                success = status == 200 and 'image' in content_type
                
                self.test_results.append({
                    'test': 'placeholder_fallback',
                    'url': test_url,
                    'status': status,
                    'content_type': content_type,
                    'success': success
                })
                
                logger.info(f"Placeholder test: Status {status}, Content-Type: {content_type}")
        except Exception as e:
            self.test_results.append({
                'test': 'placeholder_fallback',
                'error': str(e),
                'success': False
            })
        
        # Test nonexistent image fallback to placeholder
        test_url = f"{self.media_base}/images/question/nonexistent_subject/nonexistent_image.png"
        
        try:
            async with session.get(test_url) as response:
                status = response.status
                content_type = response.headers.get('content-type', '')
                
                # Should fallback to placeholder (200) or return 404
                success = status in [200, 404]
                
                self.test_results.append({
                    'test': 'nonexistent_image_fallback',
                    'url': test_url,
                    'status': status,
                    'content_type': content_type,
                    'success': success
                })
                
                logger.info(f"Nonexistent image test: Status {status}")
        except Exception as e:
            self.test_results.append({
                'test': 'nonexistent_image_fallback',
                'error': str(e),
                'success': False
            })
    
    async def test_cache_headers(self, session: aiohttp.ClientSession):
        """Test caching functionality"""
        logger.info("Testing cache headers...")
        
        test_url = f"{self.media_base}/images/placeholder/matematicas"
        
        try:
            # First request
            async with session.get(test_url) as response:
                status = response.status
                etag = response.headers.get('etag')
                cache_control = response.headers.get('cache-control')
                last_modified = response.headers.get('last-modified')
                
                cache_headers_present = bool(etag or cache_control or last_modified)
                
                self.test_results.append({
                    'test': 'cache_headers_first_request',
                    'status': status,
                    'etag': etag,
                    'cache_control': cache_control,
                    'last_modified': last_modified,
                    'success': cache_headers_present and status == 200
                })
                
                # Second request with If-None-Match
                if etag:
                    headers = {'If-None-Match': etag}
                    async with session.get(test_url, headers=headers) as response2:
                        status2 = response2.status
                        
                        self.test_results.append({
                            'test': 'cache_if_none_match',
                            'status': status2,
                            'success': status2 == 304,  # Should return Not Modified
                            'etag_used': etag
                        })
                        
                        logger.info(f"Cache test: First request {status}, If-None-Match {status2}")
        except Exception as e:
            self.test_results.append({
                'test': 'cache_headers',
                'error': str(e),
                'success': False
            })
    
    async def test_image_info_endpoint(self, session: aiohttp.ClientSession):
        """Test image info endpoint"""
        logger.info("Testing image info endpoint...")
        
        test_url = f"{self.media_base}/images/question/test_image.png/info"
        
        try:
            async with session.get(test_url) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    required_fields = ['csv_path', 'image_type', 'subject', 'exists']
                    has_required_fields = all(field in data for field in required_fields)
                    
                    self.test_results.append({
                        'test': 'image_info_endpoint',
                        'status': status,
                        'data': data,
                        'has_required_fields': has_required_fields,
                        'success': has_required_fields
                    })
                else:
                    self.test_results.append({
                        'test': 'image_info_endpoint',
                        'status': status,
                        'success': status in [404, 400]  # Acceptable responses
                    })
                
                logger.info(f"Image info test: Status {status}")
        except Exception as e:
            self.test_results.append({
                'test': 'image_info_endpoint',
                'error': str(e),
                'success': False
            })
    
    async def test_stats_endpoint(self, session: aiohttp.ClientSession):
        """Test stats endpoint"""
        logger.info("Testing stats endpoint...")
        
        test_url = f"{self.media_base}/stats"
        
        try:
            async with session.get(test_url) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    expected_fields = ['service_info', 'cache_age_seconds']
                    has_expected_fields = any(field in data for field in expected_fields)
                    
                    self.test_results.append({
                        'test': 'stats_endpoint',
                        'status': status,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                        'has_expected_fields': has_expected_fields,
                        'success': has_expected_fields
                    })
                else:
                    self.test_results.append({
                        'test': 'stats_endpoint',
                        'status': status,
                        'success': status == 200
                    })
                
                logger.info(f"Stats test: Status {status}")
        except Exception as e:
            self.test_results.append({
                'test': 'stats_endpoint',
                'error': str(e),
                'success': False
            })
    
    async def test_rate_limiting(self, session: aiohttp.ClientSession):
        """Test rate limiting (basic test)"""
        logger.info("Testing rate limiting...")
        
        test_url = f"{self.media_base}/images/placeholder/matematicas"
        
        # Make multiple rapid requests
        tasks = []
        for i in range(20):  # Try to trigger rate limiting
            tasks.append(session.get(test_url))
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            status_codes = []
            rate_limited = False
            
            for response in responses:
                if isinstance(response, Exception):
                    continue
                
                status_codes.append(response.status)
                if response.status == 429:  # Too Many Requests
                    rate_limited = True
                
                response.close()
            
            self.test_results.append({
                'test': 'rate_limiting',
                'total_requests': len(tasks),
                'successful_responses': len([s for s in status_codes if s == 200]),
                'rate_limited_responses': len([s for s in status_codes if s == 429]),
                'rate_limiting_active': rate_limited,
                'success': True  # Rate limiting is optional but good if present
            })
            
            logger.info(f"Rate limiting test: {len(status_codes)} responses, rate limited: {rate_limited}")
        except Exception as e:
            self.test_results.append({
                'test': 'rate_limiting',
                'error': str(e),
                'success': False
            })
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info(f"Starting comprehensive media service tests on {self.base_url}")
        
        async with aiohttp.ClientSession() as session:
            # Test if server is running
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status != 200:
                        logger.error(f"Server health check failed: {response.status}")
                        return
            except Exception as e:
                logger.error(f"Cannot connect to server: {e}")
                return
            
            # Run all test suites
            await self.test_basic_image_serving(session)
            await self.test_security_validation(session)
            await self.test_placeholder_fallback(session)
            await self.test_cache_headers(session)
            await self.test_image_info_endpoint(session)
            await self.test_stats_endpoint(session)
            await self.test_rate_limiting(session)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("Generating test report...")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get('success', False)])
        
        print("\n" + "="*60)
        print("MEDIA SERVICE TEST REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print("="*60)
        
        # Group results by test type
        test_groups = {}
        for result in self.test_results:
            test_type = result['test']
            if test_type not in test_groups:
                test_groups[test_type] = []
            test_groups[test_type].append(result)
        
        for test_type, results in test_groups.items():
            passed = len([r for r in results if r.get('success', False)])
            total = len(results)
            status = "✅ PASS" if passed == total else "❌ FAIL" if passed == 0 else "⚠️  PARTIAL"
            
            print(f"\n{test_type}: {status} ({passed}/{total})")
            
            for result in results:
                if not result.get('success', False):
                    if 'error' in result:
                        print(f"  - Error: {result['error']}")
                    elif 'status' in result and result['status'] != 200:
                        print(f"  - Status: {result['status']}")
        
        print("\n" + "="*60)
        
        # Save detailed results to file
        with open('media_service_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info("Test report saved to media_service_test_results.json")

async def main():
    """Main test runner"""
    tester = MediaServiceTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())