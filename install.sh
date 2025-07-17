git clone https://github.com/xNoBanOnlyZXC/Pusher.git
cd Pusher
chmod +x pusher
mv pusher /usr/local/bin
mkdir -p /var/bots
mv pusher.py /var/bots
cd ..
rm -rf Pusher
pusher setup