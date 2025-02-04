#!/bin/bash

# TOOOOOODOOOOOOO
# ENABLE I2C AND OTHER INTERFACES. IT WONT WORK WITHOUT IT


echo "Installing everything... make sure to run with sudo"

echo "-------------------------------------"
echo "IMPORTANT: This script must be run TWICE"
echo "This script will cause your pi to REBOOT"
echo "After the first reboot, re run this script and answer the prompts"
echo "-------------------------------------"

echo "This is my:"
echo "[1] First time running this script"
echo "[2] Second time running this script"

read -p "=> " choice

set -e

if [[ $choice == "1" ]]
then
    git pull --force

    # Update and upgrade system
    sudo apt-get -y update
    sudo apt-get -y upgrade
    sudo apt-get -y install python3-pip

    # Install dependancies
    pip3 install -r requirements.txt

    # Copy all .desktop files to desktop
    cp -f *.desktop /home/pi/Desktop

    # Create data folder
    mkdir /home/pi/data

    # Generate ssl certs
    sudo ./updated_gps/gensslcert.sh

    # Add permissions to script
    chmod +x ./rpihotspot/setup-network.sh

    # Clean existing configs
    sudo ./rpihotspot/setup-network.sh --clean
else
    echo "Enter the number of the monitor:"

    read -p "=> " num

    # Install rabbitmq
    sudo apt-get install -y rabbitmq-server
    sudo systemctl enable rabbitmq-server
    sudo systemctl start rabbitmq-server

    # Add permissions to script
    chmod +x ./rpihotspot/setup-network.sh

    sudo ./rpihotspot/setup-network.sh --install-upgrade --ap-ssid="dosenet-$num" --ap-password="RadwatchAP$num" --ap-country-code="US"
fi