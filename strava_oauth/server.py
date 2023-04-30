import argparse
import json
import sys
import webbrowser

from sqlalchemy import select

from strava_oauth import db
from strava_oauth.client import StravaOAuthClient
from strava_oauth.models import ApiApp, OAuthToken
from strava_oauth.app import create_app


def parse_input_args(input_args):
  root_parser = argparse.ArgumentParser(add_help=False)

  parser = argparse.ArgumentParser(description='strava-oauth', 
                                   parents=[root_parser])
  
  subparsers = parser.add_subparsers(dest='command', help='Available commands')
  subparsers.required = False

  client_id_help_text = 'The `client_id` of a Strava API app you own'
  client_secret_help_text = 'The `client_secret` of a Strava API app you own'
  
  # register sub-command parser
  parser_register = subparsers.add_parser('register',
    help='Register a new Strava API app', parents=[root_parser])
  parser_register.add_argument('-c', '--client_id', help=client_id_help_text)
  parser_register.add_argument('-s', '--client_secret',
    help=client_secret_help_text)

  # authorize sub-command parser
  parser_authorize = subparsers.add_parser('authorize',
    help='Register a new Strava API app', parents=[root_parser])
  parser_authorize.add_argument('-c', '--client_id', help=client_id_help_text)

  # fresh sub-command parser
  parser_authorize = subparsers.add_parser('fresh',
    help='Refresh an existing token', parents=[root_parser])
  parser_authorize.add_argument('-c', '--client_id', help=client_id_help_text)
  parser_authorize.add_argument('-a', '--athlete_id', 
                                help='Your Strava account ID')

  # list sub-command parser
  parser_list = subparsers.add_parser('list',
    help='List all registered Strava API apps and their tokens', 
    parents=[root_parser])

  return parser.parse_args(input_args)


def main():
  args = sys.argv[1:]
  input_args = parse_input_args(args)

  if input_args.command == 'register':
    _register(input_args.client_id, input_args.client_secret)
  elif input_args.command == 'authorize':
    _authorize(input_args.client_id)
  elif input_args.command == 'fresh':
    _fresh(input_args.client_id)
  elif input_args.command == 'list':
    _list()
  else:
    print(f'I do not know the subcommand "{input_args.command}".')


def _register(client_id, client_secret):
  """
  Example usage:
  ```
  strava-oauth register -c 12345 -s jdksghsgsghlrudskjgjzdf
  ```
  """
  api_app = ApiApp.create(client_id=client_id,
                          client_secret=client_secret)
  print('Strava API app successfully registered:\n'
        f'  client_id = {api_app.client_id}\n'
        f'  client_secret = {api_app.client_secret}')


def _authorize(client_id=None):
  """
  Example usage:
  ```
  strava-oauth authorize [-c 12345]
  ```
  The id argument is optional if only one app is registered, otherwise
  raise.
  """
  app = create_app()
  print('Launching OAuth Flask app...')
  print('Launching web browser to complete authorization...')
  webbrowser.open(f'http://127.0.0.1:5000/api/authorize/{client_id}')
  app.run()


def _fresh(client_id=None, athlete_id=None):
  """
  Example usage:
  ```
  strava-oauth fresh [-c 12345] [-a 1234567890]
  ```
  """
  stmt = select(OAuthToken)
  if client_id is not None:
    stmt = stmt.filter_by(app_client_id=client_id)
  if athlete_id is not None:
    stmt = stmt.filter_by(athlete_id=athlete_id)

  token = db.session.scalars(stmt).first()

  strava_app = db.session.get(ApiApp, token.app_client_id)
  oauth_client = StravaOAuthClient(client_id=strava_app.client_id,
                                   client_secret=strava_app.client_secret)

  if token.expired:
    resp = oauth_client.post('/token',
                              refresh_token=token.refresh_token_code,
                              grant_type='refresh_token')
    data = resp.json()
    token.refresh_token_code = data['refresh_token']
    token.access_token_code = data['access_token']
    token.expires_at = data['expires_at']
    db.session.commit()
  print(json.dumps(token.to_dict(), indent=2))


def _list():
  """
  Example usage:
  ```
  strava-oauth list [-c 12345]
  ```
  """
  from sqlalchemy import select
  api_apps = db.session.scalars(select(ApiApp)).all()
  # "If you want more customized output then you will have to 
  # subclass JSONEncoder and implement your own custom serialization."
  # Ref: https://stackoverflow.com/questions/3768895
  for app in api_apps:
    print(json.dumps(app.to_dict(), indent=2))


if __name__ == '__main__':
  sys.exit(main())
