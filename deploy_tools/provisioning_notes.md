# Provisioning a new site

## Required packages

* nginx
* Python 3
* virtualenv + pip
* Git

eg, on Ubuntu:

    sudo apt update
    sudo apt install nginx git python3 python3-venv

## Nginx Virtual Host config

* see nginx.template.conf
* replace DOMAIN with, e.g., staging.my-domain.com

## Systemd service

* see gunicorn-systemd.template.service
* replace DOMAIN with, e.g., staging.my-domain.com
* replace USER with, e.g., user

## Folder structure

Assume we have a user account at /home/username

    /home/username
    └── sites
        ├── DOMAIN1
        │    ├── .env
        │    ├── env
        │    ├── functional_tests
        │    ├── jackbot
        │    └── tests
        └── DOMAIN2
             ├── .env
             ├── env
             ├── etc
