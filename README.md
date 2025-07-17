<div align="center">
    <h1>Pusher</h1>
    Convenient sending of files to your Telegram chat
    <p>Made by <bold>~$ sudo++</bold></p>
    <img alt="code size" src="https://img.shields.io/github/languages/code-size/xnobanonlyzxc/pusher?style=for-the-badge">
    <img alt="repo stars" src="https://img.shields.io/github/stars/xnobanonlyzxc/pusher?style=for-the-badge">
    <img alt="repo stars" src="https://img.shields.io/github/commit-activity/w/xnobanonlyzxc/pusher?style=for-the-badge">
</div>

---
# How to install?

Use this one-line command:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/xNoBanOnlyZXC/Pusher/refs/heads/main/install.sh)"
```

Or manually:

```bash
git clone https://github.com/xNoBanOnlyZXC/Pusher.git
cd Pusher
chmod +x pusher
mv pusher /usr/local/bin
mkdir -p /var/bots
mv pusher.py /var/bots
cd ..
rm -rf Pusher
pusher setup
```

# How to use?

Type `pusher` for more information:

```text
usage: pusher.py [-h] {push,pull,token,chat,setup} ...

Pusher for file managevent with Telegram bot

positional arguments:
  {push,pull,token,chat,setup}
                        Commands
    push                Send file or dir via Telegram
    pull                Download file by message id
    token               Set Telegram bot token.
    chat                Set your Telegram Chat ID.
    setup               Setup Pusher

options:
  -h, --help            show this help message and exit
```
