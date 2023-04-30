import datetime
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship

from strava_oauth import db
from strava_oauth.database import Base


class SQLChemistryMixin:
  @classmethod
  def create(cls, **kwargs):
    """
    Add a single instance to the session, flush, and commit.

    If an IntegrityError is raised during flush, the transaction is 
    rolled back and the IntegrityError is raised (instead of a 
    PendingRollbackError).

    Ref:
      https://gist.github.com/edelooff/a3243d7967eaa9d2b665
    """
    instance = cls(**kwargs)
    db.session.add(instance)
    if db.echo:
      print(f'\nADDING {instance}')
    try:
      db.session.flush()
    except IntegrityError as e:
      db.session.rollback()
      raise e
    else:
      db.session.commit()
      if db.echo:
        print('* SUCCESS')
      return instance


class ApiApp(SQLChemistryMixin, Base):
  __tablename__ = 'api_app'

  client_id: Mapped[int] = mapped_column(primary_key=True)
  client_secret: Mapped[str]
  tokens: Mapped[List['OAuthToken']] = relationship()

  def to_dict(self):
    return dict(client_id=self.client_id, client_secret=self.client_secret,
                tokens=[t.to_dict() for t in self.tokens])


class OAuthToken(SQLChemistryMixin, Base):
  __tablename__ = 'oauth_token'

  id: Mapped[int] = mapped_column(primary_key=True)
  athlete_id: Mapped[int] # = mapped_column() # want this to be unique w/parent
  access_token_code: Mapped[str]
  refresh_token_code: Mapped[str]
  expires_at: Mapped[int]
  # athlete dict could go here too, from first response
  app_client_id: Mapped[int] = mapped_column(ForeignKey('api_app.client_id'))

  @property
  def expired(self):
    return datetime.datetime.utcnow() > self.expiration_time

  @property
  def expiration_time(self):
    return datetime.datetime.utcfromtimestamp(self.expires_at)
  
  def to_dict(self):
    return dict(id=self.id, athlete_id=self.athlete_id, 
                access_token=self.access_token_code, 
                refresh_token=self.refresh_token_code,
                expires_at=self.expires_at,
                expiration_time=str(self.expiration_time),
                client_id=self.app_client_id)
