# My Project

## Git Daemon — Quick Setup

### Server side (Fedora, e.g. 192.168.2.104)

#### 1. Install
sudo dnf install -y git git-daemon
sudo firewall-cmd --add-port=9418/tcp --permanent
sudo firewall-cmd --reload

#### 2. Create bare repo
cd ~/projects
git clone --bare esmfamil esmfamil.git
touch esmfamil.git/git-daemon-export-ok

#### 3. Run daemon
cd ~/projects/esmfamil.git
git daemon --reuseaddr --base-path=. --export-all --verbose --enable=receive-pack

# Flags:
#   --base-path=.            serve repos from current dir
#   --export-all             don't require git-daemon-export-ok
#   --enable=receive-pack    allow git push
#   --verbose                log connections
#   --reuseaddr              restart without "address in use"
#   --detach                 run in background (optional)

#### 4. Pull pushed changes into your working repo
cd ~/projects/esmfamil
git remote add origin ~/projects/esmfamil.git   # once
git fetch origin
git merge origin/<branch>

---

### Client side (any machine on the LAN)

#### 1. Clone
git clone git://192.168.2.104/ esmfamil
cd esmfamil

#### 2. Or add remote to an existing repo
git remote add origin git://192.168.2.104/
git fetch origin

#### 3. First push (set upstream)
git push -u origin <branch>

#### 4. Later
git pull
git push

---

### Notes

- `git://` has NO authentication → anyone on the LAN can read AND push.
  Only use on a trusted network. For real security, use SSH.
- Push to the bare repo, never directly to a non-bare working repo.
- Bare repo layout:
    ~/projects/esmfamil       ← working repo (client)
    ~/projects/esmfamil.git   ← bare repo (server)
- Check daemon is listening:
    ss -tlnp | grep 9418