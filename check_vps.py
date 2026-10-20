import os
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

if not VPS_PASS:
    print("[X] Error: VPS_PASS not set. Please set it in .env or environment variable.")
    exit(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=10)

config = '''api: yes
apiAddress: :9997

rtsp: yes
rtspAddress: :8554

webrtc: yes
webrtcAddress: :8889
webrtcAdditionalHosts:
  - ''' + VPS_IP + '''

hls: yes
hlsAddress: :8888
hlsAlwaysRemux: yes
hlsSegmentCount: 7
hlsSegmentDuration: 1s
hlsPartDuration: 250ms

paths:
  camera:
    source: rtsp://127.0.0.1:5554/stream0
    rtspTransport: tcp
  all:
'''

sftp = ssh.open_sftp()
with sftp.file('/root/mediamtx/mediamtx.yml', 'w') as f:
    f.write(config)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('docker restart mediamtx && sleep 2 && docker ps --filter name=mediamtx')
print(stdout.read().decode())
ssh.close()
