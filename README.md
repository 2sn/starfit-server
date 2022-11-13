Automatically deploy a server running a web frontend for [StarFit](https://github.com/conradtchan/starfit) to a remote host. Almost every part of the server configuration can be automated using Ansible, allowing it to be tracked in this Git repo.

Any changes made by hand to the server may be lost if the Ansible playbook is run again. There are a few steps that must be performed manually before and after using this playbook. In summary:

1. Ensure pre-requisites are met
2. Run Ansible playbook
3. Configure DNS records for email authentication

# Pre-requisites
- Ansible is installed on your local machine ([Installation Guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html))
- Remote host is running Fedora (tested with NeCTAR Fedora 36 VM image)
- Remote host has ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) open
- Volume is attached (containing StarFit data files) to the remote host, labelled `starfit-data` (how to label volumes: https://supercomputing.swin.edu.au/rcdocs/volumes/#labels)

The data directory structure should look something like this:
```
.
├── db
│   ├── he2sn.HW02.star.el.y.stardb.gz
│   ├── ...
│   └── znuc2012.Ye.star.el.y.stardb.gz
├── ref
│   ├── bbnf02.dat
│   ├── ...
│   └── sollo09.dat
└── stars
    ├── BD_80_245.dat
    ├── ...
    └── SMSS_J031300-670839.dat
 ```

# Usage

```
ansible-playbook -i <user>@<ip-address>, playbook.yml
```

You will be prompted for the domain and email used for registering the SSL certificate via [Let's Encrypt](https://letsencrypt.org).

You can skip the prompts by providing them as extra arguments
```
ansible-playbook -i <user>@<ip-address>, -e "domain=<domain> email=<email>" playbook.yml
```

This will use the latest version of [StarFit from PyPI](https://pypi.org/project/starfit/)

There are also two other playbooks: `update-starfit.yml` and `update-webpage.yml`, which do as their names suggest.
These run only the `starfit` and `starfitweb` roles, respectively, and do not prompt you for a domain and email
```
ansible-playbook -i <user>@<ip-address>, update-webpage.yml
```

By default, `starfit` is installed from PyPI. For development and testing you can choose to install from source or from Test PyPI e.g.
```
ansible-playbook -i <user>@<ip-address>, -e "install_from=testpypi" update-starfit.yml
```
The role variable `install_from` can be one of `source`, `pypi` or `testpypi`.
# Email authentication
The StarFit webpage sends results to users via email. This may or may not work out of the box, depending on your domain name and the range that your IP address resides in. It is highly likely that the emails will be caught by spam filters. Email authentication should be configured to ensure deliverability and avoid spam filters.

Run
```
sudo show-recordsets
```
on the remote host to display the DNS records required to configure email authentication. This information is also displayed at the final step of the ansible playbook. Create the SPF, DKIM, and DMARC records with your domain name registrar. These records may take some time to propagate and take effect.

# Adding new model databases
Note: the follow instructions only add new databases to the web application, and does *not* add them to the StarFit PyPI package. To add new files to StarFit, follow the [instructions on the StarFit repo](https://github.com/conradtchan/starfit#adding-new-data-files).

New model databases can be added to `/var/www/html/data/db`. This path is publicly accessible at `https://<ip-address>/data`, but it won't be included in the PyPI build unless it is also added to the data download hashlist.

The labels in the webpage database list are specified in the file `/var/www/html/data/db/labels`. The dropdown menu is dynamically populated when the page is loaded. If no label is specified, a label is extracted from the filename.

# Adding new smaple stars
Note: the follow instructions only add new sample to the web application, and does *not* add them to the StarFit PyPI package. To add new files to StarFit, follow the [instructions on the StarFit repo](https://github.com/conradtchan/starfit#adding-new-data-files).

New sample stars can be added to `/var/www/html/data/stars`. This path is publicly accessible at `https://<ip-address>/data`, but it won't be included in the PyPI build unless it is also added to the stars download hashlist.

The labels in the webpage dropdown menu are specified in the file `/var/www/html/data/stars/labels`. The dropdown menu is dynamically populated when the page is loaded. If no label is specified, a label is extracted from the filename.

# Troubleshooting jobs
All user jobs are run via RQ (Redis Queue) workers in combination with a Redis database. If there are jobs failing for seemingly unknown reasons, try restarting the Redis and RQ workers services
```
systemctl restart redis
systemctl restart rq.target
```

You can also monitor the queues, workers and jobs via RQ Monitor. Just forward port 8899 to your local machine e.g.
```
ssh -L 8000:localhost:8899 <user>@<domain>
```
then go to `localhost:8000` in your browser. This can help you determine which worker a particular job ran on.
You can then view the logs for that worker e.g.
```
journalctl -u rq-worker@07
```

RQ worker services are named `rq-worker@<N>` and are grouped together via the target `rq.target` for convenience when stopping/starting/restarting all of them at once.
