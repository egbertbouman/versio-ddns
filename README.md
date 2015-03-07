# versio-ddns

Dynamic DNS update script for domains registered with [Versio](http://www.versio.nl/). Versio-ddns does not use the DirectAdmin API, which means that you can use it regardless of the web host you're using.

### Dependencies
* Python 2.7+
* mechanize
* beautifulsoup4 

The python packages can be installed with

    pip install beautifulsoup4
    pip install mechanize


### Usage
```
usage: versio-ddns.py [--help] [--config CONFIG] [--username USERNAME]
                      [--password PASSWORD] [--host HOST]

Dynamic DNS update script for domains registered with Versio

optional arguments:
  --help                Show this help message and exit

File-based configuration:
  --config CONFIG, -c CONFIG
                        Read configuration from file

Command line configuration:
  --username USERNAME, -u USERNAME
                        Versio username
  --password PASSWORD, -p PASSWORD
                        Versio password
  --host HOST, -h HOST  DNS name / hostname to update (example:
                        host.mydomain.eu)
```

### Example versio-dns.conf
```
[versio-ddns]
username = myusername
password = mypassword
host = host.mydomain.eu
```
