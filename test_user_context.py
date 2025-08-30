#!/usr/bin/env python3
"""
Simple test script to verify user context integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from context.user_context import UserContext

def test_user_context():
    """Test user context loading and methods"""
    print("Testing User Context Integration...")
    
    # Initialize user context
    user_context = UserContext()
    
    # Test loading user info
    user_info = user_context.load_user_info()
    print(f"✓ User info loaded: {user_info['user']['name']}")
    
    # Test getting user name
    user_name = user_context.get_user_name()
    print(f"✓ User name: {user_name}")
    
    # Test getting user summary
    user_summary = user_context.get_user_summary()
    print(f"✓ User summary generated:")
    print(user_summary)
    
    print("\n✅ User context integration test passed!")

if __name__ == "__main__":
    test_user_context()
