import sys
import requests
import click
import arrow
import json
import hashlib
import platform


class hcCred:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key

    def __repr__(self):
        return """healthchecks api access credentials
        to {url}""".format(url=self.url)


class hcRegistry:
    def __init__(self, cred, registry):
        self.registry = registry
        self.hc = hc(cred)
        # read file
        try:
            with open(self.registry, 'r') as myfile:
                data = myfile.read()

            # parse file
            self.data = json.loads(data)
        except Exception:
            print("could not load registry")

    def get_hash(self, job):
        md5 = hashlib.md5()
        md5.update(platform.node().encode('utf-8'))
        md5.update(str(job.slices).encode('utf-8'))
        md5.update(job.command.encode('utf-8'))
        return md5.hexdigest()

    def find_by_hash(self, job):
        h = self.get_hash(job)
        return next((elem for elem in self.data if elem['hash'] == h), False)

    def find_by_job_id(self, job):
        pass

    def get_id(self, job):
        r = self.find_by_hash(job)
        if r:
            return r['HC_ID']

        # r = self.find_by_job_id(job)
        return False

    def register(self, id):
        pass


class hc:
    def __init__(self, cred):
        self.cred = cred

    def get_checks(self):
        """Returns a list of checks from the HC API"""
        url = "{}checks/".format(self.cred.url)
        headers = {'X-Api-Key': self.cred.api_key}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            sys.exit(1)
        if response:
            return response.json()['checks']

        raise Exception('fetching cron checks failed')

    def print_status(self, status_filter=""):
        """Show status of monitored cron jobs"""
        checks = self.get_checks()
        click.echo("Status Last ping       Check name")
        click.echo("---------------------------------")

        for i in checks:
            if status_filter and i['status'] != status_filter:
                continue

            # determine color based on status
            color = 'white'
            bold = False

            if i['status'] == 'up':
                bold = True

            if i['status'] == 'down':
                color = 'red'

            if i['status'] == 'grace':
                color = 'yellow'

            if i['status'] == 'paused':
                color = 'blue'

            # determine last ping
            last_ping = arrow.get(i['last_ping']).humanize()
            if i['status'] == 'new':
                last_ping = ''

            click.secho(
                "{status:<6} {last_ping:<15} {name}".format(
                    status=i['status'],
                    name=i['name'],
                    last_ping=last_ping
                ),
                fg=color,
                bold=bold
            )
