# Usage

```
ansible-playbook -i <user>@<ip-address>, playbook.yml
```

You will be prompted for the domain and email used for registering SSL certificate.

You can skip the prompts by providing them as extra arguments
```
ansible-playbook -i <user>@<ip-address>, -e "domain=<domain> email=<email>" playbook.yml
```

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
