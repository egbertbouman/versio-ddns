import urllib
import httplib
import mechanize

from bs4 import BeautifulSoup
from mechanize._opener import urlopen
from mechanize._form import ParseResponse

GET_IP_URL = 'http://ipv4.icanhazip.com'

VERSIO_URL_LOGIN = 'https://www.secure.versio.nl/login'
VERSIO_URL_DOMAINS = 'https://www.secure.versio.nl/c-domains'
VERSIO_URL_MANAGEDNS = 'https://www.secure.versio.nl/c-dmanagedns?id={domain_id}'

VERSIO_USERNAME = ''
VERSIO_PASSWORD = ''
VERSIO_DOMAIN = ''
VERSIO_SUBDOMAIN = ''

ip = urllib.urlopen(GET_IP_URL).read().strip()

print 'Current IP is', ip

browser = mechanize.Browser()
browser.set_handle_robots(False)
browser.open(VERSIO_URL_LOGIN)
browser.select_form(nr = 0)
browser.form['email'] = VERSIO_USERNAME
browser.form['password'] = VERSIO_PASSWORD
response = browser.submit()
response_url = response.geturl()

response = browser.open(VERSIO_URL_DOMAINS)
soup = BeautifulSoup(response.read())
domains = {domain.get('id'): domain.a.get('href')[13:]
           for domain in soup.find_all(attrs={'class': 'domain'})}

print 'Found domains: ' + ', '.join(domains.keys())

browser.open(VERSIO_URL_MANAGEDNS.format(domain_id=domains[VERSIO_DOMAIN]))

add = True
browser.select_form(predicate=lambda f: f.attrs.get('id', None) == 'update_records_form')
indices = [i for i, c in enumerate(browser.form.controls) if c.name == 'name[]']
for index in indices:
    text = browser.form.controls[index].value
    type = browser.form.controls[index+1].value[0]
    value  = browser.form.controls[index+2].value
    print 'Found DNS record %s(%s) = %s' % (text, type, value)
    if text == VERSIO_SUBDOMAIN and type == 'A':
        if value != ip:
            browser.form.controls[index+2].value = ip
            response = browser.submit()
            print 'Update DNS record %s(A) = %s' % (VERSIO_SUBDOMAIN, ip)
        else:
            print 'DNS record already up-to-date'
        add = False
        break

if add:
    browser.select_form(predicate=lambda f: f.attrs.get('id', None) == 'add_record_form')
    browser.form['name'] = VERSIO_SUBDOMAIN
    browser.form['type'] = ['A']
    browser.form['value'] = ip
    browser.form['ttl'] = ['14400']
    response = browser.submit()
    print 'Created DNS record %s(A) = %s' % (VERSIO_SUBDOMAIN, ip)

