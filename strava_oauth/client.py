import os
from urllib.parse import urlencode, urlparse, parse_qsl

import requests


class StravaOAuthClient(object):
  _base = 'https://www.strava.com/oauth'

  def __init__(self, client_id=None, client_secret=None, access_token=None):
    self.access_token = access_token
    self.client_id = client_id
    self.client_secret = client_secret

  def post(self, relative_url, **kwargs):
    params = {'client_id': self.client_id,
              'client_secret': self.client_secret}
    params.update(kwargs)
    return requests.post(self.build_url(relative_url), data=params)

  def build_authorize_url(self, redirect_url):
    return self.build_url('authorize', client_id=self.client_id, 
                          scope='activity:read_all', redirect_uri=redirect_url,
                          response_type='code', approval_prompt='auto')
  
  def build_url(self, relative_url, **params):
    url = os.path.join(self._base, relative_url.strip('/'))
    url_parts = urlparse(url)
    query = dict(parse_qsl(url_parts.query))
    query.update(params)
    return url_parts._replace(query=urlencode(query)).geturl()