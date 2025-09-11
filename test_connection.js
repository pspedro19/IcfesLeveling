#!/usr/bin/env node

// Simple Node.js script to test frontend-backend connection
const https = require('https');
const http = require('http');

console.log('🔍 Testing Frontend-Backend Connection...\n');

const testEndpoints = [
  { url: 'http://localhost:4000/health', name: 'Backend Health' },
  { url: 'http://localhost:4000/api/v1/health', name: 'Backend API Health' },
  { url: 'http://localhost:4000/api/v1/diagnostic/subjects', name: 'Diagnostic Subjects' },
];

async function testConnection(endpoint) {
  return new Promise((resolve) => {
    const { url, name } = endpoint;
    const urlObj = new URL(url);
    const client = urlObj.protocol === 'https:' ? https : http;
    
    const startTime = Date.now();
    const req = client.get(url, (res) => {
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            name,
            url,
            status: res.statusCode,
            success: res.statusCode >= 200 && res.statusCode < 300,
            responseTime: `${responseTime}ms`,
            data: jsonData
          });
        } catch (e) {
          resolve({
            name,
            url,
            status: res.statusCode,
            success: false,
            responseTime: `${responseTime}ms`,
            error: 'Invalid JSON response'
          });
        }
      });
    });
    
    req.on('error', (error) => {
      resolve({
        name,
        url,
        status: 'ERROR',
        success: false,
        responseTime: 'N/A',
        error: error.message
      });
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      resolve({
        name,
        url,
        status: 'TIMEOUT',
        success: false,
        responseTime: 'N/A',
        error: 'Request timeout'
      });
    });
  });
}

async function runTests() {
  console.log('Testing connection endpoints...\n');
  
  for (const endpoint of testEndpoints) {
    const result = await testConnection(endpoint);
    
    const statusIcon = result.success ? '✅' : '❌';
    console.log(`${statusIcon} ${result.name}`);
    console.log(`   URL: ${result.url}`);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response Time: ${result.responseTime}`);
    
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    } else if (result.data) {
      console.log(`   Response: ${JSON.stringify(result.data, null, 2).slice(0, 200)}...`);
    }
    
    console.log('');
  }
  
  const successfulTests = testEndpoints.length;
  const passedTests = (await Promise.all(testEndpoints.map(testConnection)))
    .filter(result => result.success).length;
  
  console.log(`\n📊 Test Results: ${passedTests}/${successfulTests} endpoints responding correctly`);
  
  if (passedTests === successfulTests) {
    console.log('🎉 All connection tests passed! Frontend-Backend connectivity is working correctly.');
  } else {
    console.log('⚠️ Some connection tests failed. Please check the backend service.');
  }
}

runTests().catch(console.error);