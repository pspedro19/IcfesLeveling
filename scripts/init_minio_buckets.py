#!/usr/bin/env python3
"""
MinIO Bucket Initialization Script

This script initializes MinIO with the required buckets and policies
for the student file storage system.
"""

import os
import sys
import time
import logging
from minio import Minio
from minio.error import S3Error
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinIOInitializer:
    """Initialize MinIO for student file storage"""
    
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9001')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'icfes_admin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'icfes_secure_password_2024')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        
        self.buckets = [
            'student-data',
            'study-plans', 
            'educational-content',
            'backups',
            'archives'
        ]
        
        self.client = None
    
    def connect(self, max_retries=10, retry_delay=5):
        """Connect to MinIO with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MinIO at {self.endpoint} (attempt {attempt + 1}/{max_retries})")
                
                self.client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
                
                # Test connection
                list(self.client.list_buckets())
                logger.info("✅ Successfully connected to MinIO")
                return True
                
            except Exception as e:
                logger.warning(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ Failed to connect to MinIO after all retries")
                    return False
        
        return False
    
    def create_buckets(self):
        """Create required buckets"""
        if not self.client:
            logger.error("❌ Not connected to MinIO")
            return False
        
        created_buckets = []
        
        for bucket_name in self.buckets:
            try:
                # Check if bucket exists
                if self.client.bucket_exists(bucket_name):
                    logger.info(f"✅ Bucket '{bucket_name}' already exists")
                else:
                    # Create bucket
                    self.client.make_bucket(bucket_name)
                    logger.info(f"✅ Created bucket '{bucket_name}'")
                    created_buckets.append(bucket_name)
                    
            except S3Error as e:
                logger.error(f"❌ Failed to create bucket '{bucket_name}': {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected error creating bucket '{bucket_name}': {e}")
                return False
        
        logger.info(f"✅ Bucket initialization completed. Created {len(created_buckets)} new buckets.")
        return True
    
    def set_bucket_policies(self):
        """Set bucket policies for security"""
        if not self.client:
            logger.error("❌ Not connected to MinIO")
            return False
        
        # Define policies for different bucket types
        policies = {
            'student-data': {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": "arn:aws:s3:::student-data/public/*"
                    }
                ]
            },
            'study-plans': {
                "Version": "2012-10-17", 
                "Statement": [
                    {
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:*",
                        "Resource": ["arn:aws:s3:::study-plans/*"],
                        "Condition": {
                            "StringNotEquals": {
                                "s3:authType": "REST-HEADER"
                            }
                        }
                    }
                ]
            }
        }
        
        for bucket_name, policy in policies.items():
            try:
                if self.client.bucket_exists(bucket_name):
                    policy_json = json.dumps(policy)
                    self.client.set_bucket_policy(bucket_name, policy_json)
                    logger.info(f"✅ Set policy for bucket '{bucket_name}'")
                else:
                    logger.warning(f"⚠️ Bucket '{bucket_name}' does not exist, skipping policy")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to set policy for bucket '{bucket_name}': {e}")
                # Don't fail the whole process for policy errors
                continue
        
        return True
    
    def create_sample_directory_structure(self):
        """Create sample directory structure in buckets"""
        if not self.client:
            logger.error("❌ Not connected to MinIO")
            return False
        
        # Sample directory structures
        sample_dirs = {
            'student-data': [
                'user-123/progress/2024/01/',
                'user-123/assessments/2024/01/',
                'user-123/certificates/',
                'user-456/progress/2024/01/'
            ],
            'study-plans': [
                'user-123/study-plans/2024/01/',
                'user-456/study-plans/2024/01/',
                'templates/mathematics/',
                'templates/science/'
            ],
            'educational-content': [
                'videos/mathematics/',
                'documents/science/',
                'interactive/programming/'
            ],
            'backups': [
                'daily/2024/01/',
                'weekly/2024/01/',
                'user-backups/user-123/'
            ]
        }
        
        for bucket_name, directories in sample_dirs.items():
            if not self.client.bucket_exists(bucket_name):
                logger.warning(f"⚠️ Bucket '{bucket_name}' does not exist, skipping directory creation")
                continue
                
            for directory in directories:
                try:
                    # Create a placeholder file to establish directory structure
                    placeholder_content = f"# Directory placeholder for {directory}\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    self.client.put_object(
                        bucket_name,
                        f"{directory}.gitkeep",
                        data=placeholder_content.encode('utf-8'),
                        length=len(placeholder_content.encode('utf-8')),
                        content_type='text/plain'
                    )
                    
                    logger.info(f"✅ Created directory structure: {bucket_name}/{directory}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create directory {bucket_name}/{directory}: {e}")
                    continue
        
        return True
    
    def verify_setup(self):
        """Verify the MinIO setup is working correctly"""
        if not self.client:
            logger.error("❌ Not connected to MinIO")
            return False
        
        verification_results = {
            'buckets_exist': True,
            'can_upload': True,
            'can_download': True,
            'total_buckets': 0,
            'accessible_buckets': []
        }
        
        try:
            # List buckets
            buckets = list(self.client.list_buckets())
            verification_results['total_buckets'] = len(buckets)
            
            # Check each required bucket
            for bucket_name in self.buckets:
                if self.client.bucket_exists(bucket_name):
                    verification_results['accessible_buckets'].append(bucket_name)
                else:
                    verification_results['buckets_exist'] = False
                    logger.error(f"❌ Required bucket '{bucket_name}' not found")
            
            # Test upload/download with a small test file
            test_bucket = 'student-data'
            test_object = 'test/verification.txt'
            test_content = f"MinIO verification test - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                # Upload test file
                self.client.put_object(
                    test_bucket,
                    test_object,
                    data=test_content.encode('utf-8'),
                    length=len(test_content.encode('utf-8')),
                    content_type='text/plain'
                )
                
                # Download test file
                response = self.client.get_object(test_bucket, test_object)
                downloaded_content = response.read().decode('utf-8')
                
                if downloaded_content == test_content:
                    logger.info("✅ Upload/download verification successful")
                else:
                    verification_results['can_download'] = False
                    logger.error("❌ Downloaded content doesn't match uploaded content")
                
                # Cleanup test file
                self.client.remove_object(test_bucket, test_object)
                
            except Exception as e:
                verification_results['can_upload'] = False
                verification_results['can_download'] = False
                logger.error(f"❌ Upload/download test failed: {e}")
            
            # Log verification summary
            logger.info("📊 MinIO Verification Summary:")
            logger.info(f"   Total buckets: {verification_results['total_buckets']}")
            logger.info(f"   Required buckets accessible: {len(verification_results['accessible_buckets'])}/{len(self.buckets)}")
            logger.info(f"   Upload capability: {'✅' if verification_results['can_upload'] else '❌'}")
            logger.info(f"   Download capability: {'✅' if verification_results['can_download'] else '❌'}")
            
            # Overall success
            all_good = (
                verification_results['buckets_exist'] and
                verification_results['can_upload'] and
                verification_results['can_download']
            )
            
            if all_good:
                logger.info("✅ MinIO setup verification completed successfully")
            else:
                logger.error("❌ MinIO setup verification failed")
            
            return all_good
            
        except Exception as e:
            logger.error(f"❌ Verification failed with exception: {e}")
            return False
    
    def initialize_complete_setup(self):
        """Run complete MinIO initialization"""
        logger.info("🚀 Starting MinIO initialization for student file storage...")
        
        # Step 1: Connect
        if not self.connect():
            return False
        
        # Step 2: Create buckets
        if not self.create_buckets():
            return False
        
        # Step 3: Set policies
        if not self.set_bucket_policies():
            logger.warning("⚠️ Policy setup had issues, but continuing...")
        
        # Step 4: Create directory structure
        if not self.create_sample_directory_structure():
            logger.warning("⚠️ Directory structure creation had issues, but continuing...")
        
        # Step 5: Verify setup
        if not self.verify_setup():
            return False
        
        logger.info("🎉 MinIO initialization completed successfully!")
        logger.info("📋 Next steps:")
        logger.info("   1. Start your application backend")
        logger.info("   2. Test file upload/download via API")
        logger.info("   3. Access MinIO console at http://localhost:9002")
        logger.info(f"   4. Login with: {self.access_key} / {self.secret_key}")
        
        return True

def main():
    """Main initialization function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize MinIO for student file storage')
    parser.add_argument('--endpoint', help='MinIO endpoint (default: localhost:9001)')
    parser.add_argument('--access-key', help='MinIO access key')
    parser.add_argument('--secret-key', help='MinIO secret key')
    parser.add_argument('--wait', type=int, default=30, help='Wait time for MinIO startup (seconds)')
    
    args = parser.parse_args()
    
    # Override defaults with command line args
    if args.endpoint:
        os.environ['MINIO_ENDPOINT'] = args.endpoint
    if args.access_key:
        os.environ['MINIO_ACCESS_KEY'] = args.access_key
    if args.secret_key:
        os.environ['MINIO_SECRET_KEY'] = args.secret_key
    
    # Wait for MinIO to start if requested
    if args.wait > 0:
        logger.info(f"⏳ Waiting {args.wait} seconds for MinIO to start...")
        time.sleep(args.wait)
    
    # Initialize MinIO
    initializer = MinIOInitializer()
    success = initializer.initialize_complete_setup()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()