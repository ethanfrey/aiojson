#!/bin/bash

# prep work
apt-get update
apt-get install software-properties-common git -y

# add python repos
add-apt-repository ppa:fkrull/deadsnakes -y
apt-get update

# install python3.5, pip, and virtualenv
apt-get install python3.5 python3.5-venv -y
apt-get install python3-pip -y
pip3 install --upgrade pip

# as vagrant setup the virtualenv for couch
su vagrant -c "python3.5 -m venv /home/vagrant/aiojson"
su vagrant -c "/home/vagrant/aiojson/bin/pip install -r /vagrant/requirements.pip"
su vagrant -c "/home/vagrant/aiojson/bin/ipython -c '%install_ext /vagrant/ipython/await.py'"
su vagrant -c "cp /vagrant/ipython/ipython_config.py /home/vagrant/.ipython/profile_default/ipython_config.py"
su vagrant -c "cat << EOF >> /home/vagrant/.bash_aliases
####
# ADDED BY PROVISIONING:
####

. ~/aiojson/bin/activate
cd /vagrant

EOF"
