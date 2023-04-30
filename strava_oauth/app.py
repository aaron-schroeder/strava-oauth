from flask import Flask

from strava_oauth import db
from strava_oauth.api import api as api_blueprint


def create_app():
  app = Flask(__name__)
  app.register_blueprint(api_blueprint)

  @app.teardown_appcontext
  def shutdown_session(exception=None):
    db.session.remove()

  return app
