# RIT distributed Wiki

This is a geographically distributed wiki software developed for CSCI 652.
The Wiki has a coordinator server and one or more web servers.

## Run the Wiki

First you need to create a config file for each server. Examples can be found
in `config/`. The config is structured as follows:

```toml
this_ip = <IP of this server>
port = <port to run the web server on>
replicas = <list of all web server IPs>
coordinator = <IP of the coordinator server>
```

If `this_ip == coordinator` then that server will act as the coordinator.

Next install all of the python dependencies by running `pipenv install`. Python
3 and pipenv will need to be installed if they aren't already.

Then to start each server run `pipenv run python start.py <path to server config>`

