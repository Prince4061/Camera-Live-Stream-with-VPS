"""
=============================================================================
  My Camera Management - Robust Tunnel Supervisor
  Maintains persistent high-speed reverse SSH tunnel to VPS
=============================================================================
"""

import os
import sys
import time
import subprocess

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VPS_HOST = os.getenv("VPS_HOST", os.getenv("VPS_IP", "87.232.72.64"))
VPS_USER = os.getenv("VPS_USER", "root")
REMOTE_PORT = int(os.getenv("REMOTE_BIND_PORT", "5554"))
LOCAL_CAMERA = f"{os.getenv('CAMERA_IP', '192.168.1.25')}:{os.getenv('CAMERA_RTSP_PORT', '554')}"
KEY_PATH = os.path.expanduser(os.getenv("SSH_KEY_PATH", "~/.ssh/id_ed25519"))

def main():
    print("=" * 60)
    print("  Zero-Lag Real-Time Camera Bridge Supervisor")
    print(f"  Camera : {LOCAL_CAMERA}")
    print(f"  Target : {VPS_HOST}:{REMOTE_PORT}")
    print(f"  Portal : http://{VPS_HOST}:8088")
    print("=" * 60)

    cmd = [
        "ssh",
        "-i", KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ServerAliveInterval=5",
        "-o", "ServerAliveCountMax=6",
        "-o", "ExitOnForwardFailure=yes",
        "-N",
        "-R", f"{REMOTE_PORT}:{LOCAL_CAMERA}",
        f"{VPS_USER}@{VPS_HOST}"
    ]

    reconnect_count = 0

    while True:
        try:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] Connecting high-speed stream tunnel to {VPS_HOST}...")
            
            proc = subprocess.Popen(cmd)
            proc.wait()
            
            reconnect_count += 1
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] Tunnel disconnected (code {proc.returncode}). Reconnecting in 3s (attempt #{reconnect_count})...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nStopping supervisor...")
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                pass
            print("Bridge stopped.")
            break
        except Exception as e:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] Unexpected error: {e}. Waiting 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
