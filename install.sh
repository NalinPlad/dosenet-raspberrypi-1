echo "Installing everything... make sure to run with sudo"

set -e

git pull --force

# Update and upgrade system
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install python3-pip

# Install dependancies
pip3 install -r requirements.txt

# Copy all .desktop files to desktop
cp *.desktop /home/pi/Desktop
