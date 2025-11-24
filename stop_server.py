"""Stop any Flask server running on port 5000."""

import subprocess
import sys
import os

def stop_server():
    """Find and kill any process using port 5000."""
    print("="*60)
    print("Stopping Server on Port 5000")
    print("="*60)
    print()
    
    if os.name == 'nt':  # Windows
        try:
            # Find processes using port 5000
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            
            pids = []
            for line in result.stdout.split('\n'):
                if ':5000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        pids.append(pid)
            
            if not pids:
                print("[OK] No server found running on port 5000")
                return True
            
            print(f"Found {len(pids)} process(es) using port 5000:")
            for pid in pids:
                print(f"  - PID: {pid}")
            
            print("\nAttempting to stop processes...")
            for pid in pids:
                try:
                    subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                 capture_output=True, check=True)
                    print(f"  [OK] Stopped process {pid}")
                except subprocess.CalledProcessError as e:
                    print(f"  [ERROR] Failed to stop process {pid}: {e}")
            
            print("\n[SUCCESS] Server stopped")
            return True
            
        except Exception as e:
            print(f"[ERROR] {e}")
            print("\nManual steps:")
            print("1. Open Task Manager")
            print("2. Find Python processes")
            print("3. End the process running the Flask server")
            return False
    else:  # Linux/Mac
        try:
            result = subprocess.run(
                ['lsof', '-ti:5000'],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print("[OK] No server found running on port 5000")
                return True
            
            pids = result.stdout.strip().split('\n')
            print(f"Found {len(pids)} process(es) using port 5000")
            
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"  [OK] Stopped process {pid}")
                except Exception as e:
                    print(f"  [ERROR] Failed to stop process {pid}: {e}")
            
            print("\n[SUCCESS] Server stopped")
            return True
            
        except Exception as e:
            print(f"[ERROR] {e}")
            return False

if __name__ == "__main__":
    success = stop_server()
    print("\n" + "="*60)
    if success:
        print("You can now start the server with: python run_backend.py")
    print("="*60)

