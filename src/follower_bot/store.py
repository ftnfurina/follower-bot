import logging
from functools import wraps
from typing import List, Optional

from sqlmodel import Session, SQLModel, and_, create_engine, func, select, asc

from .model import State, User


def _inject_session(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with Session(self.engine) as session:
            try:
                result = func(self, *args, **kwargs, session=session)
                if session.new or session.dirty or session.deleted:
                    session.commit()
                return result
            except Exception as e:
                session.rollback()
                raise e

    return wrapper


class Store:
    def __init__(self, db_url: str, db_log_level: Optional[str]):
        self.engine = create_engine(db_url)
        if db_log_level is not None:
            logging.getLogger("sqlalchemy").setLevel(db_log_level)
        SQLModel.metadata.create_all(self.engine)
        self._init_state()

    @_inject_session
    def query_unfollowed_users(self, limit: int, session: Session = None) -> List[User]:
        # Query unfollowed users with follow_fail_count < 3
        return session.exec(
            select(User)
            .where(and_(User.is_followed.is_(False), User.follow_fail_count < 3))
            .order_by(asc(User.join_at))
            .limit(limit)
        ).all()

    @_inject_session
    def query_users(self, users: List[User], session: Session = None) -> List[User]:
        return session.exec(
            select(User).where(User.id.in_([u.id for u in users]))
        ).all()

    @_inject_session
    def add_users(self, users: List[User], session: Session = None) -> int:
        added_ids = [u.id for u in self.query_users(users)]
        add_users = [u for u in users if u.id not in added_ids]
        session.add_all(add_users)
        [session.refresh(u) for u in add_users]
        return len(add_users)

    @_inject_session
    def update_user(self, user: User, session: Session = None) -> None:
        session.add(user)
        session.refresh(user)

    @property
    @_inject_session
    def followed_users_count(self, session: Session = None) -> int:
        return session.exec(
            select(func.count(User.id)).where(User.is_followed.is_(True))
        ).one()

    @property
    @_inject_session
    def state(self, session: Session = None) -> State:
        return session.exec(select(State)).first()

    @_inject_session
    def _init_state(self, session: Session = None) -> None:
        if self.state is not None:
            return
        session.add(State())

    @property
    def last_page(self) -> int:
        return self.state.last_page

    @_inject_session
    def update_last_page(self, page: int, session: Session = None) -> None:
        self.state.last_page = page
        session.add(self.state)
        session.refresh(self.state)

    def close(self) -> None:
        self.engine.dispose()
