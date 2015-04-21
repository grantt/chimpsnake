from __future__ import unicode_literals
import sys
import json
import logging
import requests

default_logger = logging.getLogger(__name__)
default_logger.setLevel(logging.INFO)
default_logger.addHandler(logging.StreamHandler(sys.stderr))


class MailchimpObject(object):
    default_fields = {'start', 'limit', 'sort_field', 'sort_dir'}

    def __init__(self, client):
        self.client = client

    def compose_parameters(self, fields, kwargs):
        parameters = set(kwargs.keys()).intersection(fields.union(self.default_fields))
        return {field: kwargs[field] for field in parameters}


class ChimpsnakeException(Exception):
    pass


class AuthenticationError(ChimpsnakeException):
    pass


class Client(object):

    base_url = 'https://{}.api.mailchimp.com/2.0/'
    headers = {
        'content-type': 'application/json',
    }

    def __init__(self, api_key=None, logger=None):
        self.logger = logger or default_logger
        if not (api_key and isinstance(api_key, basestring)):
            raise AuthenticationError("Please provide a valid Mailchimp API key (ex. 'myapikey-us2').")

        self.api_key, self.data_center = api_key.split('-')

        # Apply the data center prefix to the API base URL
        self.base_url = self.base_url.format(self.data_center)

        # Apply endpoint classes
        self.lists = Lists(self)

    def call(self, endpoint, method, parameters=None):
        parameters = parameters or {}
        headers = self.headers
        url = '{base}/{endpoint}/{method}'.format(
            base=self.base_url,
            endpoint=endpoint,
            method=method,
        )

        # Authentication gets stuffed in the request parameters
        parameters.update({
            'apikey': self.api_key,
        })
        # And convert to JSON
        parameters = json.dumps(parameters)

        response = requests.post(url, data=parameters, headers=headers)
        data = self.parse_response(response)
        return data

    def parse_response(self, response):
        if response.status_code != 200:
            self.handle_failure(response)
        data = response.json()
        return data

    def handle_failure(self, response):
        raise ChimpsnakeException("Bad response from Mailchimp server")

    def ping(self):
        """
        Ping Mailchimp to see if the key is valid

        :return:
        """
        return self.call('helper', 'ping')


class Lists(MailchimpObject):
    endpoint = 'lists'

    def list(self, **kwargs):
        fields = {'list_id', 'list_name', 'from_name', 'from_email', 'from_subject', 'created_before', 'created_after'}
        parameters = self.compose_parameters(fields, kwargs)

        return self.client.call(self.endpoint, 'list', parameters=parameters)

    def members(self, id_, **kwargs):
        fields = {'status', 'segment'}
        parameters = self.compose_parameters(fields, kwargs)
        parameters['id'] = id_

        return self.client.call(self.endpoint, 'members', parameters=parameters)