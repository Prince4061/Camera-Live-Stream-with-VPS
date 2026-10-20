# 🎥 My Camera Management — Cloud Live Streaming

Aapka local IP camera (`192.168.1.25`) ab cloud VPS (`87.232.72.64`) ke through
**duniya me kahin se bhi** live dekh sakte hain — mobile, laptop, kisi bhi
browser se.

---

## ✅ Pehle yeh karein (ek hi baar) — sabse zaroori step

**`install_autostart.bat` par double-click karein.**

Yeh ek hi click me:
1. Streaming ko **abhi turant** start kar deta hai (background me, koi window nahi),
2. Aur Windows me **auto-start** laga deta hai — aapka PC on hone par streaming
   khud chalu ho jayegi.

Iske baad yeh link kholein:

### 👉 [http://87.232.72.64:8088](http://87.232.72.64:8088)

PIN: `1234` (details `camera_pin.txt` me).

> Autostart ek baar lagane ke baad dobara ki zaroorat nahi. PC restart karne par
> bhi streaming apne aap chalu rahegi.

---

## 🌐 Live Links

| Kaam | Link | Latency |
| :--- | :--- | :--- |
| 🖥️ **Main dashboard** (recommended) | [http://87.232.72.64:8088](http://87.232.72.64:8088) | ~0.2–0.5 s |
| ⚡ **WebRTC** (sabse fast) | `http://87.232.72.64:8889/camera` | ~0.2–0.5 s |
| 📱 **HLS** (iPhone / slow network fallback) | `http://87.232.72.64:8888/camera` | ~3–6 s |
| 🔧 Raw RTSP (VLC) | `rtsp://87.232.72.64:8554/camera` | ~0.2 s |

Dashboard me **WebRTC** aur **HLS** ke beech switch karne ke buttons hain,
fullscreen hai, aur LIVE/OFFLINE status asli stream ke hisaab se update hota hai.

---

## 🔧 Kya kharab tha, aur kya fix hua

| # | Problem | Fix |
| :-- | :--- | :--- |
| 1 | **Koi publisher chal hi nahi raha tha** — PC par `streamer.py` / ffmpeg kuch bhi running nahi tha, isliye VPS par path `camera` khaali tha (HLS 404, "no stream is available") | Streamer chalu + autostart install |
| 2 | **Autostart kabhi install hua hi nahi tha** — PC restart hote hi stream band | `setup_autostart.ps1` se pakka autostart |
| 3 | **Galat stream** — purana script `stream1` bhejta tha par VPS config main stream maang raha tha; audio AAC transcode bekaar chal raha tha | Stream choice explicit, audio transcode hata diya |
| 4 | **`-use_wallclock_as_timestamps`** camera ke timestamps bigaad raha tha (slow-motion / drift) | Hata diya — camera ke asli timestamps use hote hain |
| 5 | **HLS me frame drop** — segment 1s the par camera ka keyframe 3s par, isliye MediaMTX `#EXT-X-GAP` bhar raha tha (aadhe frames gayab) | HLS segment = 3s (GOP ke barabar), ab 0 gaps |
| 6 | **RTP packets MTU se bade** (1460 > 1440) → relay har packet re-fragment kar raha tha | Publisher `-pkt_size 1200` |
| 7 | **Dashboard jhoot bolta tha** — stream band hone par bhi "LIVE" dikhata tha, aur ek baar tootne par wapas connect nahi hota tha | Naya player: asli status + auto-reconnect + error message |
| 8 | **Stream band ho jaye to freeze** — koi stall detection nahi tha | Watchdog: 15s tak naya data nahi → auto restart |
| 9 | Autostart se **do streamer** chal sakte the | Loopback lock (port 47991) — sirf ek instance |

---

## ⚠️ Ek important sach — internet upload speed

Aapke connection ki **upload speed sirf ~0.6 Mbps** hai (measure kiya gaya).

| Stream | Resolution | Bitrate | Upload me fit? |
| :--- | :--- | :--- | :--- |
| Main (`stream0`) | 2304×1296 | ~1.2 Mbps | ❌ Nahi — aadhe frames drop |
| **Sub (`stream1`) — default** | **352×288** | **~0.27 Mbps** | ✅ Haan, aaram se |

Isliye default **sub-stream** hai. Purana setup main stream bhej raha tha jo
link me fit nahi hota tha — isi wajah se picture stutter karti thi. Ab stream
smooth hai, lekin **resolution kam (352×288)** hai. Yeh camera/upload ki
limitation hai, code ki nahi.

Aapke paas 3 upgrade raste hain (jo bhi chahein, bata dein):

1. **Internet plan upgrade** (upload ≥ 2–3 Mbps) → phir `--hd` mode se full
   2304×1296 stream chalega.
2. **Camera ki sub-stream ka resolution badhana** (camera ke web UI se,
   352×288 → 640×480 / 704×576). Bitrate thoda badhega par upload me fit
   rahega — picture kaafi behtar ho jayegi.
3. **PC par transcode** — is PC par possible nahi hai: 4 MP decode hi
   realtime se slow hai (test: 1.05x), isliye transcode stutter karega.

---

## 🚀 Roz ke commands

| File | Kaam |
| :--- | :--- |
| **`install_autostart.bat`** | **(Ek baar)** Autostart install + abhi start |
| `start_background.vbs` | Silent start (koi window nahi) |
| `start_stream.bat` | Start with visible window (status dekhne ke liye) |
| `stop_stream.bat` | Streaming band karein (autostart laga rahega) |
| `camera_pin.txt` | Portal PIN + security notes |

Full quality (sirf tez internet par):

```bat
python streamer.py --hd
```

Logs: **`streamer.log`** (isi folder me). Kuch galat lage to sabse pehle yeh
file dekhein.

---

## 🩺 Problem aaye to (Troubleshooting)

**1. Dashboard par "Camera is offline" aa raha hai**
- PC on hai? `start_background.vbs` double-click karein.
- `streamer.log` dekhein — "Publishing … stream1" line dikhni chahiye.
- Camera ka bijli/Wi-Fi check karein.

**2. Camera ka IP badal gaya hai (router restart ke baad)**
- `streamer.py` me sabse upar `CAMERA_IP` badal dein.

**3. Video chal raha hai par ruk-ruk kar**
- Yeh upload bandwidth ka issue hai — `README` ka "important sach" section
  dekhein. Sub-stream pe pehle se hi hai; aur kam karne ke liye camera ki
  sub-stream bitrate kam karein.

**4. Mobile par sirf HLS chalta hai**
- Dashboard me "HLS" button dabayein. iPhone/Safari par WebRTC purane
  versions me nahi chalta — HLS fallback usi ke liye hai.

**5. Sab kuch band, jaldi fix chahiye**
```bat
stop_stream.bat
start_stream.bat
```
Window me error dikhega — wahi error bata dein.

---

## ⚙️ Technical Details

- **Camera:** `192.168.1.25:554` — RTSP. Streams: `stream0` (main 2304×1296@20),
  `stream1` (sub 352×288@25).
- **Local publisher:** `streamer.py` — ffmpeg, H.264 **copy** (0% CPU, no
  quality loss), TCP, `-pkt_size 1200`, stall-watchdog + auto-reconnect.
- **Cloud VPS:** `87.232.72.64`
  - MediaMTX (Docker `mediamtx`, host network) — RTSP `:8554`, WebRTC `:8889`,
    HLS `:8888`, API `:9997` (localhost only)
  - HLS config: `fmp4`, 7 × 3s segments (camera GOP ke barabar)
  - Nginx (`camera-web`) — dashboard on `:8088`
- **Config file on VPS:** `/root/mediamtx/mediamtx.yml`
- **Dashboard on VPS:** `/root/camera-web/index.html`
  (local copy: `dashboard/index.html`). Edit locally, then run
  `python deploy_dashboard.py` to push it live.
- **WebRTC transport:** UDP `:8189` + TCP `:8189` (ICE over TCP fallback, taaki
  jin mobile/office networks me UDP block hai wahan bhi chale). Agar WebRTC
  phir bhi na chale, dashboard **khud** HLS par switch ho jata hai.

---

## 🔒 Security note (padhna zaroori)

Portal ka PIN `1234` sirf web page ke andar video chhupata hai. Stream khud
protected nahi hai — jise link pata hai woh PIN ke bina bhi dekh sakta hai:

- `http://87.232.72.64:8889/camera`
- `http://87.232.72.64:8888/camera`
- `rtsp://87.232.72.64:8554/camera`

Agar **asli password protection** chahiye (MediaMTX level par, taaki link
khud kaam na kare), to woh alag se add kiya ja sakta hai — bas bol dein.
