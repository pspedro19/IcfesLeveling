#!/usr/bin/env python3
"""
Test script to validate ICFES competency fields import
"""

import sys
import os
sys.path.append('apps/backend')

from apps.backend.app.core.database import get_db
from apps.backend.app.import_icfes_excel import ICFESExcelImporter

def test_icfes_import():
    """Test ICFES Excel import functionality"""
    
    print("Testing ICFES competency fields import...")
    print("="*60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize importer
        importer = ICFESExcelImporter(db)
        
        # Test Excel file path
        excel_file = "database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
        
        if not os.path.exists(excel_file):
            print(f"❌ Excel file not found: {excel_file}")
            return
            
        print(f"📁 Testing import from: {excel_file}")
        
        # Run validation-only import
        print("🔍 Running validation check...")
        result = importer.import_excel(excel_file, validate_only=True)
        
        print(f"\n📊 VALIDATION RESULTS:")
        print(f"   ✅ Questions processed: {result['imported_questions']}")
        print(f"   ❌ Errors found: {len(result['errors'])}")
        print(f"   ⚠️  Warnings: {len(result['warnings'])}")
        
        if result['errors']:
            print(f"\n❌ Sample Errors (first 3):")
            for i, error in enumerate(result['errors'][:3]):
                print(f"   {i+1}. {error}")
                
        if result['warnings']:
            print(f"\n⚠️  Sample Warnings (first 3):")
            for i, warning in enumerate(result['warnings'][:3]):
                print(f"   {i+1}. {warning}")
        
        # Test a small import to check ICFES fields
        print(f"\n🧪 Testing actual import (first 5 questions)...")
        
        # Import just a few questions to test
        import pandas as pd
        df = pd.read_excel(excel_file)
        sample_df = df.head(5)
        
        # Save sample to temporary file
        temp_file = "temp_icfes_sample.xlsx"
        sample_df.to_excel(temp_file, index=False)
        
        # Import the sample
        sample_result = importer.import_excel(temp_file, validate_only=False)
        
        print(f"📊 SAMPLE IMPORT RESULTS:")
        print(f"   ✅ Questions imported: {sample_result['imported_questions']}")
        print(f"   ❌ Errors: {len(sample_result['errors'])}")
        
        if sample_result['errors']:
            print(f"   Errors: {sample_result['errors']}")
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_icfes_import()