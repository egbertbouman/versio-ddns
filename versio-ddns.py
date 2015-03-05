import sys
import urllib
import httplib
import argparse
import mechanize
import ConfigParser

from bs4 import BeautifulSoup
from mechanize._opener import urlopen
from mechanize._form import ParseResponse

GET_IP_URL = 'http://ipv4.icanhazip.com'

VERSIO_URL_HOME = 'https://www.secure.versio.nl/customer'
VERSIO_URL_LOGIN = 'https://www.secure.versio.nl/login'
VERSIO_URL_DOMAINS = 'https://www.secure.versio.nl/c-domains'
VERSIO_URL_MANAGEDNS = 'https://www.secure.versio.nl/c-dmanagedns?id={domain_id}'


def get_ip():
    try:
        return urllib.urlopen(GET_IP_URL).read().strip()
    except:
        pass

def login_required(func):
   def wrap(*args, **kwargs):
       if getattr(args[0], 'logged_in'):
           return func(*args, **kwargs)
       else:
           raise Exception('You need to be logged in to execute ' + func.__name__)
   return wrap


class ManageVersioDNS(object):

    def __init__(self):
        self.logged_in = False
        self.browser = mechanize.Browser()
        self.browser.set_handle_robots(False)

    def login(self, username, password):
        self.browser.open(VERSIO_URL_LOGIN)
        self.browser.select_form(nr = 0)
        self.browser.form['email'] = username
        self.browser.form['password'] = password
        response = self.browser.submit()
        response_url = response.geturl()
        self.logged_in = response_url == VERSIO_URL_HOME
        return self.logged_in

    @login_required
    def get_domains(self):
        response = self.browser.open(VERSIO_URL_DOMAINS)
        soup = BeautifulSoup(response.read())
        return {domain.get('id'): domain.a.get('href')[13:]
                for domain in soup.find_all(attrs={'class': 'domain'})}

    @login_required
    def get_records(self, domain_id):
        records = []
        self.browser.open(VERSIO_URL_MANAGEDNS.format(domain_id=domain_id))
        self.browser.select_form(predicate=lambda f: f.attrs.get('id', None) == 'update_records_form')
        indices = [i for i, c in enumerate(self.browser.form.controls) if c.name == 'name[]']
        for index in indices:
            text = self.browser.form.controls[index].value
            type = self.browser.form.controls[index+1].value[0]
            value  = self.browser.form.controls[index+2].value
            records.append((text, type, value))
        return records

    @login_required
    def add_record(self, domain_id, text, type, value):
        self.browser.open(VERSIO_URL_MANAGEDNS.format(domain_id=domain_id))
        self.browser.select_form(predicate=lambda f: f.attrs.get('id', None) == 'add_record_form')
        self.browser.form['name'] = text
        self.browser.form['type'] = [type]
        self.browser.form['value'] = value
        self.browser.form['ttl'] = ['14400']
        response = self.browser.submit()

    @login_required
    def update_record(self, domain_id, text, type, value):
        self.browser.open(VERSIO_URL_MANAGEDNS.format(domain_id=domain_id))
        self.browser.select_form(predicate=lambda f: f.attrs.get('id', None) == 'update_records_form')
        indices = [i for i, c in enumerate(self.browser.form.controls) if c.name == 'name[]']
        for index in indices:
            cur_text = self.browser.form.controls[index].value
            cur_type = self.browser.form.controls[index+1].value[0]
            cur_value  = self.browser.form.controls[index+2].value
            if cur_text == text and cur_type == type:
                if cur_value != value:
                    self.browser.form.controls[index+2].value = value
                    response = self.browser.submit()
                    return 1
                return 0
        return -1


def main(argv):
    parser = argparse.ArgumentParser(add_help=False, description=('Dynamic DNS update script for domains registered with Versio'))
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')

    group1 = parser.add_argument_group(title='File-based configuration')
    group1.add_argument('--config', '-c', help='Read configuration from file')

    group2 = parser.add_argument_group(title='Command line configuration')
    group2.add_argument('--username', '-u', help='Versio username')
    group2.add_argument('--password', '-p', help='Versio password')
    group2.add_argument('--host', '-h', help='DNS name / hostname to update (example: host.mydomain.eu)')

    try:
        args = parser.parse_args(sys.argv[1:])

        username = args.username
        password = args.password
        host = args.host

        if args.config:
            config = ConfigParser.RawConfigParser()
            with open(args.config) as fp:
                config.readfp(fp)

            username = config.get('versio-ddns', 'username')
            password = config.get('versio-ddns', 'password')
            host = config.get('versio-ddns', 'host')

        if not username or not password or not host:
            parser.print_usage()
            raise ValueError('username, password, and host are required options')

        ip = get_ip()
        print 'Current IP is', ip

        versio = ManageVersioDNS()
        versio.login(username, password)
        domains = versio.get_domains()
        print 'Found domains: ' + ', '.join(domains.keys())

        domain = host.partition('.')[2]
        if not domain in domains:
            print 'Unknown domain', domain
            sys.exit(1)

        domain_id = domains[domain]
        records = versio.get_records(domain_id)
        for record in records:
            print 'Found DNS record %s(%s) = %s' % record
        
        ret = versio.update_record(domain_id, host, 'A', ip)
        if ret == 1:
            print 'Updated DNS record %s(A) = %s' % (host, ip)
        elif ret == 0:
            print 'DNS record already up-to-date'
        else:
            versio.add_record(domain_id, host, 'A', ip)
            print 'Created DNS record %s(A) = %s' % (host, ip)

    except Exception, e:
        print 'Error:', str(e)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
