"""
=============================================================================
  My Camera Management - Real-Time Cloud Camera Streamer  (v2, fixed)
  Local IP Camera  ->  Cloud VPS MediaMTX  ->  WebRTC / HLS / Mobile

  What changed vs v1 (why the old stream never worked properly):
    1. Stream choice is explicit and honest: the sub-stream (stream1) by
       default, because this connection uploads at ~0.6 Mbps and the 4 MP
       main stream needs ~1.2 Mbps. Publishing more than the link can carry
       is what caused the stutter. Use --hd on a fast connection.
    2. Removed -use_wallclock_as_timestamps, which rewrote the camera's
       timestamps and caused slow-motion / drifting playback.
    3. Dropped the audio transcode (this camera has no audio track), so there
       is no AAC re-encode and no aresample stall.
    4. Added a stall watchdog: if no new media is muxed for STALL_TIMEOUT
       seconds, ffmpeg is killed and restarted. A frozen TCP stream can no
       longer leave the live view dead forever.
    5. Added a single-instance lock so autostart can never spawn two
       publishers fighting over the same path.
    6. Logs to streamer.log, so background (pythonw) runs are diagnosable.
=============================================================================
"""

import os
import sys
import time
import socket
import threading
import subprocess

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
CAMERA_IP = os.getenv("CAMERA_IP", "192.168.1.25")
CAMERA_RTSP_PORT = int(os.getenv("CAMERA_RTSP_PORT", "554"))

# The camera has exactly two streams:
#   stream0 = main , 2304x1296 @ 20 fps, ~1.2 Mbps
#   stream1 = sub  ,  352x288  @ 25 fps, ~0.27 Mbps
#
# This connection uploads at roughly 0.6 Mbps, so the 1.2 Mbps main stream
# physically cannot get through - the relay only ever received about half its
# frames, which is what made the picture stutter. The sub-stream fits with
# headroom, so it is the default and the feed is truly real-time.
#
# On a faster internet connection, run with --hd to publish the main stream.
HD_MODE = "--hd" in sys.argv
STREAM = "stream0" if HD_MODE else "stream1"
CAMERA_SOURCE = f"rtsp://{CAMERA_IP}:{CAMERA_RTSP_PORT}/{STREAM}"

VPS_IP = os.getenv("VPS_IP", "87.232.72.64")
VPS_RTSP_PORT = int(os.getenv("VPS_RTSP_PORT", "8554"))
PUBLISH_PATH = os.getenv("PUBLISH_PATH", "camera")
TARGET_URL = f"rtsp://{VPS_IP}:{VPS_RTSP_PORT}/{PUBLISH_PATH}"

STALL_TIMEOUT = 15       # seconds without new media -> restart
BACKOFF_MIN = 2
BACKOFF_MAX = 15
LOCK_PORT = 47991        # loopback lock: guarantees one publisher per PC

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "streamer.log")
LOG_MAX_BYTES = 5 * 1024 * 1024

FFMPEG_PATHS = [
    r"C:\Users\user\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe",
    "ffmpeg.exe",
    "ffmpeg",
]

_log_lock = threading.Lock()


def log(message):
    """Print + append to streamer.log (pythonw has no console)."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    with _log_lock:
        try:
            print(line, flush=True)
        except Exception:
            pass
        try:
            if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > LOG_MAX_BYTES:
                os.replace(LOG_PATH, LOG_PATH + ".1")
            with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
                f.write(line + "\n")
        except Exception:
            pass


def find_ffmpeg():
    for p in FFMPEG_PATHS:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def acquire_single_instance():
    """Bind a loopback port; released automatically when the process dies."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    except Exception:
        pass
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return s
    except OSError:
        try:
            s.close()
        except Exception:
            pass
        return None


def build_command(ffmpeg_bin):
    return [
        ffmpeg_bin,
        "-hide_banner",
        "-nostdin",
        "-loglevel", "warning",
        "-nostats",
        "-progress", "pipe:1",
        # ---- input: camera RTSP over TCP ----
        "-rtsp_transport", "tcp",
        "-fflags", "+genpts",
        "-i", CAMERA_SOURCE,
        # ---- video: pass H.264 through untouched (0% CPU, no quality loss) ----
        "-map", "0:v:0",
        "-c:v", "copy",
        "-an",
        # ---- output: publish to the cloud relay ----
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        "-muxdelay", "0",
        # Keep RTP payloads below the path MTU, otherwise MediaMTX logs
        # "RTP packets are too big" and re-fragments every packet.
        "-pkt_size", "1200",
        TARGET_URL,
    ]


NOISE = (
    "Timestamps are unset",
    "Broken pipe",
    "Connection reset",
    "Immediate exit requested",
)


def run_once(ffmpeg_bin):
    """Run one ffmpeg session. Returns (exit_code, uptime_seconds)."""
    cmd = build_command(ffmpeg_bin)
    log(f"Publishing {CAMERA_SOURCE} -> {TARGET_URL}")

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )

    last_media = [time.time()]
    started = time.time()

    def read_progress():
        try:
            for line in proc.stdout:
                line = line.strip()
                if line.startswith(("out_time_us=", "out_time_ms=", "frame=")):
                    val = line.split("=", 1)[1]
                    if val.isdigit() and int(val) > 0:
                        last_media[0] = time.time()
        except Exception:
            pass

    def read_errors():
        try:
            for line in proc.stderr:
                l = line.strip()
                if l and not any(n in l for n in NOISE):
                    log(f"ffmpeg: {l}")
        except Exception:
            pass

    threading.Thread(target=read_progress, daemon=True).start()
    threading.Thread(target=read_errors, daemon=True).start()

    try:
        while proc.poll() is None:
            time.sleep(1)
            if time.time() - last_media[0] > STALL_TIMEOUT:
                log(f"Stall detected: no media for {STALL_TIMEOUT}s -> restarting")
                try:
                    proc.kill()
                except Exception:
                    pass
                break
    except KeyboardInterrupt:
        log("Stopping streamer (Ctrl+C)...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        raise

    try:
        code = proc.wait(timeout=5)
    except Exception:
        code = -1

    return code, time.time() - started


def main():
    ffmpeg_bin = find_ffmpeg()

    lock = acquire_single_instance()
    if lock is None:
        log("Another streamer instance is already running. Exiting.")
        return 0

    log("=" * 65)
    log("  LIVE CAMERA STREAMER v2")
    log(f"  Camera : {CAMERA_SOURCE}")
    log(f"  VPS    : {TARGET_URL}")
    log(f"  Watch  : http://{VPS_IP}:8088")
    log(f"  ffmpeg : {ffmpeg_bin}")
    log("=" * 65)

    backoff = BACKOFF_MIN

    while True:
        try:
            code, uptime = run_once(ffmpeg_bin)
            if uptime >= 30:
                backoff = BACKOFF_MIN          # healthy session -> reset backoff
            log(f"Stream ended (code {code}, uptime {uptime:.0f}s). "
                f"Reconnecting in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX)

        except KeyboardInterrupt:
            log("Streamer stopped.")
            return 0
        except Exception as e:
            log(f"Unexpected error: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX)


if __name__ == "__main__":
    sys.exit(main())
