#!/usr/bin/env python3
"""
gpt-image-2 generator with intelligent multi-endpoint failover.

Strategy:
1. First request: Try primary endpoint first
2. If primary fails: Switch to backup and remember it
3. Subsequent requests: Continue using the working endpoint
4. Only retry primary if explicitly requested

Environment variables:
  BANANA_API_URL - Primary API base URL
  BANANA_API_KEY - Primary API key
  BANANA_API_URL_BACKUP - Backup API base URL (optional)
  BANANA_API_KEY_BACKUP - Backup API key (optional)
  BANANA_ENABLE_FAILOVER - Enable failover (default: true)
  BANANA_MAX_RETRIES - Max retries per endpoint (default: 2)
  BANANA_RETRY_DELAY - Delay between retries in seconds (default: 1.0)
  BANANA_FORCE_PRIMARY - Force use primary endpoint (default: false)
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Get script directory
SCRIPT_DIR = Path(__file__).parent.absolute()
ORIGINAL_SCRIPT = SCRIPT_DIR / 'generate.py'
STATE_FILE = Path.home() / '.openclaw' / '.gpt_image_failover_state.json'

# Read environment
API_URL_PRIMARY = os.getenv('BANANA_API_URL', 'https://n.lconai.com')
API_KEY_PRIMARY = os.getenv('BANANA_API_KEY', '')
API_URL_BACKUP = os.getenv('BANANA_API_URL_BACKUP', '')
API_KEY_BACKUP = os.getenv('BANANA_API_KEY_BACKUP', '')
ENABLE_FAILOVER = os.getenv('BANANA_ENABLE_FAILOVER', 'true').lower() == 'true'
FORCE_PRIMARY = os.getenv('BANANA_FORCE_PRIMARY', 'false').lower() == 'true'
MAX_RETRIES = int(os.getenv('BANANA_MAX_RETRIES', '2'))
RETRY_DELAY = float(os.getenv('BANANA_RETRY_DELAY', '1.0'))


def load_state():
    """Load failover state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'current_endpoint': 'primary', 'last_success': None}


def save_state(state):
    """Save failover state to file."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except:
        pass


def get_endpoints():
    """Get available endpoints."""
    endpoints = {
        'primary': (API_URL_PRIMARY, API_KEY_PRIMARY),
    }
    
    if ENABLE_FAILOVER and API_URL_BACKUP and API_KEY_BACKUP:
        endpoints['backup'] = (API_URL_BACKUP, API_KEY_BACKUP)
    
    return endpoints


def run_with_endpoint(endpoint_name, api_url, api_key, max_retries=2):
    """Run the original script with specified endpoint."""
    env = os.environ.copy()
    env['BANANA_API_URL'] = api_url
    env['BANANA_API_KEY'] = api_key
    
    print(f"\n🔄 Using endpoint: {endpoint_name}")
    print(f"   URL: {api_url}")
    
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"   Retrying ({attempt + 1}/{max_retries})...")
            time.sleep(RETRY_DELAY)
        
        result = subprocess.run(
            [sys.executable, str(ORIGINAL_SCRIPT)] + sys.argv[1:],
            env=env,
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"   ✅ {endpoint_name} succeeded!")
            return True, endpoint_name
        else:
            # Check if it's a network error (exit code 1 with proxy/connection errors)
            # The original script already printed the error
            pass
    
    print(f"   ❌ {endpoint_name} failed after {max_retries} attempts")
    return False, endpoint_name


def main():
    """Main failover logic with smart endpoint selection."""
    
    # Validate primary config
    if not API_KEY_PRIMARY:
        print("❌ Error: BANANA_API_KEY not set")
        sys.exit(1)
    
    # Get available endpoints
    endpoints = get_endpoints()
    
    # Load previous state
    state = load_state()
    
    # Determine which endpoint to try first
    if FORCE_PRIMARY:
        # Force use primary
        try_order = ['primary']
        print("⚠️  Forced to use primary endpoint (BANANA_FORCE_PRIMARY=true)")
    elif 'backup' in endpoints and state.get('current_endpoint') == 'backup':
        # Previous request used backup successfully, try it first
        try_order = ['backup', 'primary']
        print("ℹ️  Continuing with backup endpoint (last successful)")
    else:
        # Default: try primary first
        try_order = ['primary']
        if 'backup' in endpoints:
            try_order.append('backup')
    
    # Try endpoints in order
    last_error = None
    for endpoint_name in try_order:
        if endpoint_name not in endpoints:
            continue
            
        api_url, api_key = endpoints[endpoint_name]
        
        success, used_endpoint = run_with_endpoint(
            endpoint_name, api_url, api_key, MAX_RETRIES
        )
        
        if success:
            # Save state: remember which endpoint worked
            if used_endpoint != state.get('current_endpoint'):
                state['current_endpoint'] = used_endpoint
                state['last_success'] = time.time()
                save_state(state)
                print(f"\n💾 Switched to {used_endpoint} endpoint for future requests")
            sys.exit(0)
        else:
            last_error = f"{endpoint_name} failed"
            
            # If primary failed and backup is available, try backup
            if endpoint_name == 'primary' and 'backup' in try_order:
                print(f"\n⚠️  Primary endpoint failed, trying backup...")
            elif endpoint_name == 'backup':
                print(f"\n⚠️  Backup endpoint also failed")
    
    # All endpoints failed
    print("\n❌ All endpoints failed. Please check:")
    print("   1. Your network connection")
    print("   2. API keys are valid")
    print("   3. Backup endpoint is configured (BANANA_API_URL_BACKUP)")
    print(f"\n   Last error: {last_error}")
    
    # Reset state on complete failure
    state['current_endpoint'] = 'primary'
    save_state(state)
    
    sys.exit(1)


if __name__ == '__main__':
    main()
