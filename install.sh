echo "Installing everything... make sure to run with sudo"

git pull

sudo apt-get -y update
sudo apt-get -u upgrade
sudo apt-get -y install python3-pip

pip3 install -r requirements.txt
