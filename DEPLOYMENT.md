# Deployment Guide: Progsity Mock Exam & Judge Server

The testing site consists of:
- **Frontend**: Responsive Progsity exam simulator with CodeMirror IDE (`static/`).
- **Backend**: Python standard library HTTP judge server (`server.py`) serving static assets and handling code execution APIs (`/api/run`, `/api/submit`).
- **Sandbox Guard**: `sandbox_guard.py` executing code in C++ (`g++`), C (`gcc`), Python 3 (`python`), and JavaScript (`node`).

---

## Method 1: Local Network / LAN Access (Same Wi-Fi)

Run the server on your computer and open it from any other computer, tablet, or phone on the same Wi-Fi.

1. **Start the server**:
   Double click `run_testing_site.bat` or run:
   ```powershell
   cd testing_site
   python server.py
   ```
2. **Find your local IP address**:
   In PowerShell / Command Prompt, run:
   ```powershell
   ipconfig
   ```
   Look for `IPv4 Address` under your active Wi-Fi or Ethernet adapter (e.g. `192.168.1.15` or `10.0.0.42`).
3. **Open on any other device**:
   On your phone or second laptop browser:
   ```
   http://192.168.1.15:5500
   ```
   *(If it doesn't connect, ensure Windows Firewall allows Python on Private networks: Windows Security -> Firewall & network protection -> Allow an app through firewall).*

---

## Method 2: Instant Public HTTPS URL (Cloudflare Tunnel / ngrok)

Share the site over the internet with zero hosting fees and free SSL certificates without configuring router port-forwarding.

### Option A: Cloudflare Tunnel (Recommended - 100% Free, No Account Needed)
1. Download `cloudflared` from [cloudflare.com](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or via WinGet:
   ```powershell
   winget install Cloudflare.cloudflared
   ```
2. Run your server in one terminal:
   ```powershell
   cd testing_site; python server.py
   ```
3. Run the tunnel in another terminal:
   ```powershell
   cloudflared tunnel --url http://localhost:5500
   ```
4. Cloudflare gives you a temporary public HTTPS link (e.g. `https://random-words.trycloudflare.com`). Anyone with this link can access the test site and submit code from anywhere.

### Option B: ngrok
1. Run:
   ```powershell
   ngrok http 5500
   ```
2. Use the generated `https://xxxx.ngrok-free.app` URL.

---

## Method 3: Cloud Deployment (Render / Railway / Fly.io via Docker)

A ready-to-use `Dockerfile` is included in `testing_site/Dockerfile`.

### Deploying to Render (Free Tier):
1. Push your repository to GitHub.
2. Sign in to [render.com](https://render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. In settings:
   - **Root Directory**: `testing_site`
   - **Runtime**: `Docker`
   - **Instance Type**: Free
6. Render builds the Docker image (installs Python, GCC/G++, and Node.js) and gives you a permanent URL like `https://my-exam-site.onrender.com`.

### Deploying to Railway:
1. Install Railway CLI (`npm i -g @railway/cli`) or connect via GitHub on [railway.app](https://railway.app).
2. Inside `testing_site/`, run:
   ```bash
   railway up
   ```
3. Generate domain under Settings -> Networking.

---

## Method 4: Self-Hosted Linux VPS (DigitalOcean / Hetzner / AWS EC2)

### Using Docker Compose (Simplest):
1. Copy the `testing_site/` directory to your VPS.
2. Inside `testing_site/`, run:
   ```bash
   docker compose up -d --build
   ```
3. The server starts on port `5500` in the background with memory and CPU guards.

### Using Native Linux Systemd:
1. Install compilers & Node.js on Ubuntu/Debian:
   ```bash
   sudo apt update
   sudo apt install -y python3 build-essential nodejs
   ```
2. Create systemd service `/etc/systemd/system/judge-server.service`:
   ```ini
   [Unit]
   Description=Progsity Judge Server
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/var/www/testing_site
   ExecStart=/usr/bin/python3 /var/www/testing_site/server.py
   Restart=always
   Environment=PORT=5500

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start:
   ```bash
   sudo systemctl enable --now judge-server
   ```
