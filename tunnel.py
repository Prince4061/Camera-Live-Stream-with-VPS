"""
=============================================================================
  My Camera Management - High-Speed Zero-Lag SSH Stream Tunnel
  Directly bridges Local IP Camera to VPS
  Benefits:
    - 0% CPU usage (No FFmpeg re-encoding)
    - Zero timestamp distortion
    - Ultra-low latency real-time streaming
    - Automatic infinite reconnect watchdog
=============================================================================
"""

import socket
import select
import threading
import time
import sys
import os
import paramiko

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure UTF-8 console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VPS_IP = os.getenv("VPS_IP", "YOUR_VPS_IP")
VPS_PORT = int(os.getenv("VPS_PORT", "22"))
VPS_USER = os.getenv("VPS_USER", "root")
VPS_PASS = os.getenv("VPS_PASS", "")

REMOTE_BIND_PORT = int(os.getenv("REMOTE_BIND_PORT", "5554"))
CAMERA_IP = os.getenv("CAMERA_IP", "192.168.1.25")
CAMERA_PORT = int(os.getenv("CAMERA_RTSP_PORT", "554"))

stop_event = threading.Event()

def handle_channel(chan, cam_host, cam_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        sock.connect((cam_host, cam_port))
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Camera connect failed: {e}")
        chan.close()
        return

    try:
        while not stop_event.is_set():
            r, w, x = select.select([sock, chan], [], [], 1.0)
            if sock in r:
                data = sock.recv(32768)
                if not data:
                    break
                chan.sendall(data)
            if chan in r:
                data = chan.recv(32768)
                if not data:
                    break
                sock.sendall(data)
    except Exception:
        pass
    finally:
        sock.close()
        chan.close()

def run_tunnel():
    if not VPS_PASS:
        print("[X] Error: VPS_PASS not set. Please set it in .env or environment variable.")
        return

    print("=" * 65)
    print("  [ZERO-LAG] HIGH SPEED CAMERA TUNNEL")
    print("=" * 65)
    print(f"  Local Camera : {CAMERA_IP}:{CAMERA_PORT}")
    print(f"  VPS Bridge   : {VPS_IP}:{REMOTE_BIND_PORT}")
    print(f"  Web Portal   : http://{VPS_IP}:8088")
    print("=" * 65)

    reconnect_attempts = 0

    while not stop_event.is_set():
        client = None
        try:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] Connecting secure tunnel to {VPS_IP}...")

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                VPS_IP,
                port=VPS_PORT,
                username=VPS_USER,
                password=VPS_PASS,
                timeout=10,
                banner_timeout=15,
                look_for_keys=False,
                allow_agent=False
            )

            transport = client.get_transport()
            transport.set_keepalive(10)
            transport.request_port_forward("127.0.0.1", REMOTE_BIND_PORT)
            print(f"[{time.strftime('%H:%M:%S')}] Tunnel Active! Camera stream is now LIVE on VPS.")
            reconnect_attempts = 0

            while not stop_event.is_set() and transport.is_active():
                chan = transport.accept(1.0)
                if chan is None:
                    continue
                t = threading.Thread(target=handle_channel, args=(chan, CAMERA_IP, CAMERA_PORT), daemon=True)
                t.start()

        except KeyboardInterrupt:
            print("\nStopping tunnel...")
            stop_event.set()
            break
        except Exception as e:
            if stop_event.is_set():
                break
            reconnect_attempts += 1
            print(f"[{time.strftime('%H:%M:%S')}] Tunnel disconnected: {e}. Reconnecting in 3s...")
            time.sleep(3)
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

if __name__ == "__main__":
    run_tunnel()
