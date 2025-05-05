import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlmodel import Session, SQLModel, and_, create_engine, func, or_, select, update

from .model import CreateBy, Follower, Following, History, State


class Store:
    def __init__(self, url: str, log_level: Optional[str]):
        self.engine = create_engine(url)
        if log_level is not None:
            logging.getLogger("sqlalchemy").setLevel(log_level.upper())
        SQLModel.metadata.create_all(self.engine)
        self._init_state()

    def close(self) -> None:
        self.engine.dispose()

    def _init_state(self) -> None:
        with Session(self.engine) as session:
            if self.query_state(session) is None:
                state = State()
                session.add(state)
                session.commit()

    def query_state(self, session: Session) -> Optional[State]:
        return session.exec(select(State)).one_or_none()

    def upsert(self, model: SQLModel, session: Session) -> None:
        session.add(model)
        session.commit()
        session.refresh(model)

    def upsert_follower(self, follower: Follower, session: Session) -> None:
        db_follower = session.get(Follower, follower.id)
        if db_follower is None:
            session.add(follower)
            session.commit()
        else:
            follower.id = db_follower.id
            db_follower.sync_id = follower.sync_id
            db_follower.login = follower.login
            if not db_follower.followed and follower.followed:
                db_follower.last_follow_date = follower.last_follow_date

            db_follower.followed = follower.followed
            session.add(db_follower)
            session.commit()

    def upsert_followers(self, followers: List[Follower], session: Session) -> None:
        for follower in followers:
            self.upsert_follower(follower, session)

    def upsert_following(self, following: Following, session: Session) -> None:
        db_following = session.get(Following, following.id)
        if db_following is None:
            session.add(following)
            session.commit()
        else:
            following.id = db_following.id
            db_following.sync_id = following.sync_id
            db_following.login = following.login
            if not db_following.followed and following.followed:
                db_following.last_follow_date = following.last_follow_date
                db_following.create_by = following.create_by

            db_following.followed = following.followed
            session.add(db_following)
            session.commit()

    def upsert_followings(self, followings: List[Following], session: Session) -> None:
        [self.upsert_following(following, session) for following in followings]

    def update_unfollow_followers(self, sync_id: int, session: Session) -> None:
        session.exec(
            update(Follower)
            .where(
                and_(
                    Follower.sync_id != sync_id,
                    Follower.sync_id.is_not(None),
                )
            )
            .values(followed=False, unfollow_count=Follower.unfollow_count + 1)
        )
        session.commit()

    def update_unfollow_followings(self, sync_id: int, session: Session) -> None:
        session.exec(
            update(Following)
            .where(
                and_(
                    Following.sync_id != sync_id,
                    Following.sync_id.is_not(None),
                )
            )
            .values(followed=False, unfollow_count=Following.unfollow_count + 1)
        )
        session.commit()

    def query_not_following_followers(
        self, limit: int, unfollow_threshold: int, session: Session
    ) -> List[Tuple[Follower, Optional[Following]]]:
        query = (
            select(Follower, Following)
            .join(Following, Follower.id == Following.id, isouter=True)
            .where(
                Follower.followed.is_(True),
                Follower.unfollow_count <= unfollow_threshold,
                or_(Following.id.is_(None), Following.followed.is_(False)),
            )
            .limit(limit)
        )
        return session.exec(query).all()

    def query_unfollow_followers(
        self, limit: int, not_create_by_user: bool, session: Session
    ) -> List[Tuple[Follower, Following]]:
        query = (
            select(Follower, Following)
            .join(Following, Follower.id == Following.id)
            .where(
                Follower.followed.is_(False),
                Following.followed.is_(True),
                Following.create_by != CreateBy.USER if not_create_by_user else 1 == 1,
            )
            .limit(limit)
        )
        return session.exec(query).all()

    def query_followed_followings(
        self, since: int, limit: int, session: Session
    ) -> List[Following]:
        query = (
            select(Following)
            .where(
                Following.followed.is_(True),
                Following.id > since,
            )
            .order_by(Following.id)
            .limit(limit)
        )
        return session.exec(query).all()

    def query_follower_count(self, session: Session) -> int:
        return session.exec(
            select(func.count(Follower.id)).where(Follower.followed.is_(True))
        ).one()

    def query_following_count(self, session: Session) -> int:
        return session.exec(
            select(func.count(Following.id)).where(Following.followed.is_(True))
        ).one()

    def query_histories(
        self, start_date: Optional[datetime], end_date: datetime, session: Session
    ) -> List[History]:
        query = (
            select(History)
            .where(
                History.start_date >= start_date if start_date is not None else 1 == 1,
                History.end_date <= end_date,
            )
            .order_by(History.id)
        )
        return session.exec(query).all()
