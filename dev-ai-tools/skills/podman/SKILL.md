---
name: podman
description: >
  Install, configure, and manage Podman containers on macOS. Use when the user
  wants to install Podman, set up Docker compatibility, manage containers or
  Podman machines, configure auto-start, troubleshoot container issues, or
  migrate from Docker Desktop.
---

# Podman

Manages the full Podman lifecycle on macOS -- installation, Docker CLI compatibility, container operations, machine management, optional auto-start, and troubleshooting.

## Guardrails

- Confirm with the user before uninstalling Docker Desktop.
- Confirm before destructive operations: `podman machine rm`, `podman system prune`, `podman container prune`.
- Confirm before modifying system-level configuration (LaunchAgents, sudo operations like `podman-mac-helper install`).
- When operations require `sudo`, explain what the command does before running it.

---

## Workflow 1: Install Podman

### Prerequisite: Docker Desktop must not be present

Check before installing:

```bash
ls /Applications/Docker.app 2>/dev/null && echo "FOUND" || echo "NOT FOUND"
```

If Docker Desktop is found, confirm with the user, then uninstall:

```bash
osascript -e 'quit app "Docker Desktop"'
sudo rm -rf /Applications/Docker.app
rm -rf ~/Library/Containers/com.docker.docker
rm -rf ~/Library/Application\ Support/Docker\ Desktop
rm -rf ~/.docker
```

If installed via Homebrew instead: `brew uninstall --cask docker` (then remove the data dirs above).

If Docker Desktop is not found, skip straight to installation.

### Install

```bash
brew install podman podman-desktop
```

Install krunkit (required -- Homebrew does not bundle it with Podman Desktop):

```bash
brew tap slp/krunkit
brew install krunkit
```

Initialize and start the Podman machine:

```bash
podman machine init
podman machine start
```

To allocate custom resources during init:

```bash
podman machine init --cpus 4 --memory 8192 --disk-size 100
```

Verify:

```bash
podman info
podman machine list
```

---

## Workflow 2: Docker CLI Compatibility

Sets up the Docker CLI to route through Podman so existing `docker` and `docker compose` commands work unchanged.

### Step 1: Install Docker CLI tools

```bash
brew install docker docker-compose docker-buildx
```

### Step 2: Install the mac-helper

This forwards `/var/run/docker.sock` to the Podman socket:

```bash
sudo /opt/homebrew/bin/podman-mac-helper install
```

### Step 3: Restart the machine for the socket to take effect

```bash
podman machine stop
podman machine start
```

### Step 4: Set the Docker CLI context

```bash
docker context use default
```

### Step 5: Configure Homebrew CLI plugin path

```bash
mkdir -p ~/.docker
cat > ~/.docker/config.json << 'EOF'
{
  "cliPluginsExtraDirs": [
    "/opt/homebrew/lib/docker/cli-plugins"
  ]
}
EOF
```

### Step 6: Verify

```bash
docker -v
docker compose -v
docker ps
```

All three should succeed without errors. `docker ps` should return an empty container list (not a connection error).

---

## Workflow 3: Auto-start (optional)

Configures the Podman machine to start automatically at login using a macOS LaunchAgent.

### Enable auto-start

Create the plist:

```bash
cat > ~/Library/LaunchAgents/com.podman.machine.start.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.podman.machine.start</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/podman</string>
    <string>machine</string>
    <string>start</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>AbandonProcessGroup</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/podman-machine-start.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/podman-machine-start.err</string>
</dict>
</plist>
EOF
```

`AbandonProcessGroup` is critical -- without it, launchd interprets the process exit as a crash and restart-loops.

Load the agent:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.podman.machine.start.plist
```

### Disable auto-start

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.podman.machine.start.plist
rm ~/Library/LaunchAgents/com.podman.machine.start.plist
```

### Check status

```bash
launchctl print gui/$(id -u)/com.podman.machine.start
cat /tmp/podman-machine-start.log
cat /tmp/podman-machine-start.err
```

---

## Workflow 4: Manage Containers

### Run

```bash
podman run -d --name <name> -p <host>:<container> <image>
```

### Lifecycle

```bash
podman ps -a
podman stop <container>
podman start <container>
podman restart <container>
podman rm <container>
podman rm -f <container>
```

### Inspect

```bash
podman logs <container>
podman logs -f <container>
podman exec -it <container> /bin/sh
podman inspect <container>
podman stats <container> --no-stream
podman port <container>
```

### Images

```bash
podman images
podman pull <image>
podman build -t <tag> .
podman rmi <image>
```

### Compose

```bash
podman compose up -d
podman compose down
podman compose logs -f
podman compose ps
```

With Docker compatibility enabled (Workflow 2), `docker compose` also works.

### Cleanup

```bash
podman container prune
podman image prune -a
podman system prune -a
```

---

## Workflow 5: Manage Podman Machine

### Status

```bash
podman machine list
podman machine inspect
```

### Start / Stop

```bash
podman machine start
podman machine stop
```

### Modify resources

```bash
podman machine stop
podman machine set --cpus 4 --memory 8192
podman machine start
```

### Switch to rootful mode

```bash
podman machine stop
podman machine set --rootful
podman machine start
```

### Reset (destroy and recreate)

Confirm with the user first -- this destroys all containers and images in the machine.

```bash
podman machine stop
podman machine rm --force
podman machine init
podman machine start
```

---

## Workflow 6: Troubleshooting

### Machine won't start

**Corrupted VM:** Stop and recreate:

```bash
podman machine stop
podman machine rm --force
podman machine init
podman machine start
```

**Insufficient resources:** Init with explicit resource allocation:

```bash
podman machine init --cpus 2 --memory 2048 --disk-size 20
```

**Hypervisor denied:** Verify support:

```bash
sysctl kern.hv_support
```

Should output `1`. If not, the Mac hardware or macOS version doesn't support the Hypervisor framework.

### Docker socket not working

Verify the mac-helper is installed:

```bash
ls /var/run/docker.sock
```

If missing, run:

```bash
sudo /opt/homebrew/bin/podman-mac-helper install
podman machine stop && podman machine start
docker context use default
```

Check `~/.docker/config.json` exists with the `cliPluginsExtraDirs` entry (see Workflow 2 Step 5).

### krunkit not found

Homebrew does not bundle krunkit with Podman Desktop. Install it:

```bash
brew tap slp/krunkit
brew install krunkit
```

### Volume mount permission issues

If you get "Permission denied" on mounted volumes with `--userns=keep-id`, the macOS user ID may conflict with the VM's user. Check with:

```bash
id -u
podman machine ssh id -u
```

For volumes on non-standard partitions (case-sensitive APFS), Podman may fail with "no such file or directory." This is a known limitation -- use the default mount paths (`/Users`, `/private`, `/var/folders`).

### Auto-start not working

Check the LaunchAgent status and logs:

```bash
launchctl print gui/$(id -u)/com.podman.machine.start
cat /tmp/podman-machine-start.log
cat /tmp/podman-machine-start.err
```

If launchd is restart-looping, ensure the plist has `AbandonProcessGroup` set to `true`.

---

## Sources

- [Nike Confluence: Migrating from Docker Desktop to Podman on macOS](https://confluence.nike.com/pages/viewpage.action?pageId=1381316885)
- [Podman official docs](https://docs.podman.io/)
- [Podman Desktop installation (macOS)](https://podman-desktop.io/docs/installation/macos-install)
- [Podman macOS auto-start tutorial](https://github.com/containers/podman/blob/main/docs/tutorials/macos_autostart.md)
- [Podman Desktop Docker compatibility](https://podman-desktop.io/docs/migrating-from-docker/managing-docker-compatibility)
- [Podman Desktop troubleshooting (macOS)](https://podman-desktop.io/docs/troubleshooting/troubleshooting-podman-on-macos)
