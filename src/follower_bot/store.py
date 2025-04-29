import logging
from functools import wraps
from typing import List, Optional

from sqlmodel import (
    Session,
    SQLModel,
    and_,
    asc,
    create_engine,
    select,
)
from sqlmodel import (
    func as model_func,
)

from .model import Follower, Following, FollowingCreateBy, History, State


def _inject_session(func):
    @wraps(func)
    def wrapper(self: "Store", *args, **kwargs):
        if "session" in kwargs:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                kwargs["session"].rollback()
                raise e
        else:
            with Session(self.engine) as session:
                try:
                    return func(self, *args, **kwargs, session=session)
                except Exception as e:
                    session.rollback()
                    raise e

    return wrapper


class Store:
    def __init__(self, url: str, log_level: Optional[str]):
        self.engine = create_engine(url)
        if log_level is not None:
            logging.getLogger("sqlalchemy").setLevel(log_level.upper())
        SQLModel.metadata.create_all(self.engine)
        self._init_state()

    @_inject_session
    def _init_state(self, session: Session = None):
        state = session.exec(select(State)).one_or_none()
        if state is None:
            state = State()
            session.add(state)
            session.commit()

    @_inject_session
    def add_history(self, history: History, session: Session = None):
        session.add(history)
        session.commit()

    @_inject_session
    def query_state(self, session: Session = None) -> State:
        return session.exec(select(State)).one()

    @_inject_session
    def query_following_count(self, session: Session = None) -> int:
        return session.exec(
            select(model_func.count(Following.id)).where(Following.followed.is_(True))
        )

    @_inject_session
    def query_unfollowed_following(
        self, limit: int, creators: List[FollowingCreateBy], session: Session = None
    ) -> List[Following]:
        return session.exec(
            select(Following)
            .where(
                and_(
                    Following.followed.is_(False),
                    Following.fail_count < 3,
                    Following.create_by.in_(creators),
                )
            )
            .order_by(asc(Following.join_date))
            .limit(limit)
        ).all()

    @_inject_session
    def add_followings(
        self, followings: List[Following], session: Session = None
    ) -> None:
        for following in followings:
            if session.get(Following, following.id) is not None:
                continue

            session.add(following)
            session.commit()
            session.refresh(following)

    @_inject_session
    def update_state(self, state: State, session: Session = None) -> None:
        session.add(state)
        session.commit()
        session.refresh(state)

    @_inject_session
    def update_following(self, following: Following, session: Session = None):
        session.add(following)
        session.commit()
        session.refresh(following)

    @_inject_session
    def upsert_followers(self, followers: List[Follower], session: Session = None):
        for follower in followers:
            db_follower = session.get(Follower, follower.id)
            if db_follower is not None:
                db_follower.search_id = follower.search_id
                db_follower.follower = True
                db_follower.follow_date = follower.follow_date
                session.add(db_follower)
                session.commit()
                continue

            session.add(follower)
            session.commit()
            session.refresh(follower)

    @_inject_session
    def query_unfollow_followers(
        self, search_id: int, session: Session = None
    ) -> List[Follower]:
        return session.exec(
            select(Follower).where(
                and_(Follower.search_id != search_id, Follower.follower.is_(True))
            )
        ).all()

    @_inject_session
    def update_follower(self, follower: Follower, session: Session = None) -> None:
        session.add(follower)
        session.commit()
        session.refresh(follower)

    @_inject_session
    def delete_following(self, following_id: int, session: Session = None) -> None:
        session.delete(session.get(Following, following_id))
        session.commit()

    def close(self) -> None:
        self.engine.dispose()
