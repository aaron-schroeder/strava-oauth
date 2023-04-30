import json
from urllib.parse import urljoin

from flask import Blueprint, abort, redirect, request, url_for
from sqlalchemy import select, update

from strava_oauth import db
from strava_oauth.client import StravaOAuthClient
from strava_oauth.models import OAuthToken, ApiApp


api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/authorize/<int:client_id>')
def authorize(client_id):
  strava_app = db.session.get(ApiApp, client_id)
  # TODO: handle bad id here
  full_callback_url = urljoin(request.base_url, 
                              url_for('api.callback', client_id=client_id))
  oauth_client = StravaOAuthClient(client_id=strava_app.client_id, 
                                   client_secret=strava_app.client_secret)
  return redirect(oauth_client.build_authorize_url(full_callback_url))


@api.route('/callback/<int:client_id>')
def callback(client_id):
  strava_app = db.session.get(ApiApp, client_id)

  if (error := request.args.get('error')) is not None:
    # Handles user clicking "cancel" button, resulting in a response like:
    # /callback?state=&error=access_denied
    return {
      'warning': 'It looks like you clicked "cancel" on Strava\'s '
                 'authorization page. If you want to use the Strava API '
                 'to access your data, you must grant access.',
      'error': error
    }

  # Validate that the user accepted the necessary scope,
  # and display a warning if not.
  if 'activity:read_all' not in request.args.get('scope', '').split(','):
    return {
      'warning': 'Please accept the permission '
                 '"View data about your private activities" on Strava\'s '
                 'authorization page (otherwise, you can\'t access your data).',
    }

  oauth_client = StravaOAuthClient(client_id=strava_app.client_id,
                                   client_secret=strava_app.client_secret)
  resp = oauth_client.post('token', code=request.args.get('code'),
                           grant_type='authorization_code')
  token_data = resp.json()
  new_token = OAuthToken.create(athlete_id=token_data['athlete']['id'],
                                access_token_code=token_data['access_token'],
                                refresh_token_code=token_data['refresh_token'],
                                expires_at=token_data['expires_at'],
                                app_client_id=strava_app.client_id)

  return {'oauth_token': new_token.to_dict()}, 201
  