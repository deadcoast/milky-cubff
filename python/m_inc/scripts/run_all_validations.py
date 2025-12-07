#!/usr/bin/env python3
"""
Master validation script that runs all integration validation tests.
"""

import sys
import subprocess
from pathlib import Path


def run_validation_script(script_name: str, description: str) -> bool:
    """Run a validation script and return success status."""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✓ {description} PASSED")
        else:
            print(f"\n✗ {description} FAILED")
        
        return success
        
    except Exception as e:
        print(f"\n✗ {description} ERROR: {e}")
        return False


def main():
    """Run all validation tests."""
    print("="*70)
    print("M|inc Integration Validation Suite")
    print("="*70)
    print("\nRunning all validation tests...")
    
    results = {}
    
    # Test 1: Integration validation (17.1)
    results['integration'] = run_validation_script(
        'validate_integration.py',
        'Integration Validation (Task 17.1)'
    )
    
    # Test 2: Determinism validation (17.2)
    results['determinism'] = run_validation_script(
        'validate_determinism.py',
        'Determinism Validation (Task 17.2)'
    )
    
    # Test 3: Performance validation (17.3)
    results['performance'] = run_validation_script(
        'validate_performance.py',
        'Performance Validation (Task 17.3)'
    )
    
    # Test 4: Spec compliance validation (17.4)
    results['spec_compliance'] = run_validation_script(
        'validate_spec_compliance.py',
        'Spec Compliance Validation (Task 17.4)'
    )
    
    # Print final summary
    print("\n" + "="*70)
    print("FINAL VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} validation suites passed")
    print("="*70)
    
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
