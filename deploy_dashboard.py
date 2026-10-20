"""
=============================================================================
  Deploy the local dashboard (dashboard/index.html) to the VPS web container.

  The VPS serves /root/camera-web/index.html through the `camera-web` nginx
  container (bind-mounted, read-only inside the container). Updating the file
  is enough - nginx serves it immediately, no restart needed.

  Usage:  python deploy_dashboard.py
=============================================================================
"""

import hashlib
import os
import sys
import paramiko

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VPS_IP = os.getenv("VPS_IP", "YOUR_VPS_IP")
VPS_PORT = int(os.getenv("VPS_PORT", "22"))
VPS_USER = os.getenv("VPS_USER", "root")
VPS_PASS = os.getenv("VPS_PASS", "")
REMOTE_PATH = "/root/camera-web/index.html"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_PATH = os.path.join(BASE_DIR, "dashboard", "index.html")


def main():
    if not VPS_PASS:
        print("[X] Error: VPS_PASS not set. Please set it in .env or environment variable.")
        return 1

    if not os.path.exists(LOCAL_PATH):
        print(f"[X] Not found: {LOCAL_PATH}")
        return 1

    with open(LOCAL_PATH, "rb") as f:
        data = f.read()

    local_md5 = hashlib.md5(data).hexdigest()
    print(f"Local : {len(data)} bytes  md5 {local_md5}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

    sftp = ssh.open_sftp()
    with sftp.file(REMOTE_PATH, "wb") as rf:
        rf.write(data)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command(f"md5sum {REMOTE_PATH}", timeout=20)
    print("Remote:", stdout.read().decode(errors="replace").strip())

    err = stderr.read().decode(errors="replace").strip()
    if err:
        print("stderr:", err)
    ssh.close()

    print("[OK] Dashboard deployed.")
    print(f"     Open: http://{VPS_IP}:8088")
    return 0


if __name__ == "__main__":
    sys.exit(main())
