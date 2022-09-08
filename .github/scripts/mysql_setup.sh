#!/usr/bin/env bash

# Run from .github/workflows/installer.yml

set -euxo pipefail

sudo apt -y install gnutls-bin
sudo sed -i "s/^bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf
cat /etc/mysql/mysql.conf.d/mysqld.cnf
sudo service mysql start
mysql -e 'CREATE DATABASE ${CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME};' -uroot -proot
mysql -e 'CREATE USER `${CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME}`@`%` IDENTIFIED WITH mysql_native_password BY "${CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_PASSWORD}";' -uroot -proot
mysql -e 'GRANT ALL PRIVILEGES ON `${CAMCOPS_DOCKER_MYSQL_CAMCOPS_DATABASE_NAME}`.* TO `${CAMCOPS_DOCKER_MYSQL_CAMCOPS_USER_NAME}`@`%`;' -uroot -proot
