from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
  pass


class SQLChemistry:
  def __init__(self):
    self.engine = None
    self.session = None

  def init(self, sqlalchemy_uri='sqlite:///strava_oauth.sqlite3', echo=False):
    self.engine = create_engine(sqlalchemy_uri, echo=echo)
    self.session = self._make_scoped_session()
    self.create_all()
  
  def _make_session_factory(self):
    return sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

  def _make_scoped_session(self):
    # Flask-SQLAlchemy calls this `factory`
    Session = self._make_session_factory()
    return scoped_session(Session)
  
  # Flask-SQLAlchemy has this but I can't figure out if I'll need it
  # def _teardown_session(self):
  #   self.session.remove()

  def create_all(self):
    import strava_oauth.models
    Base.metadata.create_all(bind=self.engine)

  def drop_all(self):
    Base.metadata.drop_all(bind=self.engine)

  @property
  def echo(self):
    return self.engine.echo
