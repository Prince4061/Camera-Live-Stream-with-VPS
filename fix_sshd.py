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

cmd = '''
sed -i '/ClientAlive/d' /etc/ssh/sshd_config
sed -i '/StreamLocalBindUnlink/d' /etc/ssh/sshd_config
cat << 'EOF' >> /etc/ssh/sshd_config
StreamLocalBindUnlink yes
ClientAliveInterval 30
ClientAliveCountMax 10
TCPKeepAlive yes
EOF
systemctl restart sshd
sleep 1
echo 'SSHD RECONFIGURED'
'''

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
