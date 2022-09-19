# Usage

```
ansible-playbook -i <user>@<ip-address>, playbook.yml
```

You will be prompted for the domain and email used for registering SSL certificate.

You can skip the prompts by providing them as extra arguments
```
ansible-playbook -i <user>@<ip-address>, -e "domain=<domain> email=<email>" playbook.yml
```
