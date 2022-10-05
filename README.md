Automatically deploy the StarFit web server to a remote host. 

Prerequisites:
- Ansible is installed on your local machine
- Remote host is running Fedora (tested with NeCTAR Fedora 36 image)
- Volume is attached (containing StarFit data files) to the remote host, labelled `starfit-data` (how to label volumes: https://supercomputing.swin.edu.au/rcdocs/volumes/#labels)

# Usage

```
ansible-playbook -i <user>@<ip-address>, playbook.yml
```

You will be prompted for the domain and email used for registering SSL certificate.

You can skip the prompts by providing them as extra arguments
```
ansible-playbook -i <user>@<ip-address>, -e "domain=<domain> email=<email>" playbook.yml
```

This will use the latest version of StarFit from https://pypi.org/project/starfit/

# Email authentication
The StarFit webpage sends results to users via email. This may or may not work out of the box, depending on your domain name and the range that your IP address resides in. It is highly likely that the emails will be caught by spam filters. Email authentication should be configured to ensure deliverability and avoid spam filters.

Run 
```
sudo show-recordsets
```
on the remote host to display the DNS records required to configure email authentication. This information is also displayed at the final step of the ansible playbook. Create the SPF, DKIM, and DMARC records with your domain name registrar. These records may take some time to propagate and take effect.

# Adding new model databases

New model databases can be added to `/var/www/html/data/db`. Note that this path is publicly accessible at `https://<ip-address>/data`, but it won't be included in the PyPI build unless it is also added to the data download hashlist.

The new database can then be added to the drop-down menu by adding an entry with the name and filename in `roles/starfit/files/html/index.html`, under `<select name = "database">`. Only the filename needs to be included, not the full path. E.g.

```
<select name = "database">
    <option value="znuc2012.S4.star.el.y.stardb.gz">znuc.S4 (2012)</option>
    <option value="znuc.S4.star.el.y.stardb.gz">znuc.S4 (2010)</option>
    <option value="znuc2012.Ye.star.el.y.stardb.gz">znuc.Ye (2012)</option>
    <option value="znuc.Ye.star.el.y.stardb.gz">znuc.Ye (2010)</option>
    <option value="he2sn.HW02.star.el.y.stardb.gz">he2sn.HW02</option>
</select>
```
