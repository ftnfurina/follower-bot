from datetime import datetime
from enum import IntEnum
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel):
    id: int = Field(description="User ID", primary_key=True)
    login: str = Field(description="User login", unique=True)


class GithubUser(User):
    name: Optional[str] = Field(default=None, description="User name")
    company: Optional[str] = Field(default=None, description="User company")
    location: Optional[str] = Field(default=None, description="User location")
    email: Optional[str] = Field(default=None, description="User email")
    public_repos: int = Field(description="Number of public repositories")
    public_gists: int = Field(description="Number of public gists")
    followers: int = Field(description="Number of followers")
    following: int = Field(description="Number of following")
    # created_at: datetime = Field(description="Date of creation")
    updated_at: datetime = Field(description="Date of last update")

    @property
    def repos(self) -> int:
        return self.public_repos

    @property
    def gists(self) -> int:
        return self.public_gists

    @property
    def updated(self) -> datetime:
        return self.updated_at


class Follower(User, table=True):
    follow_date: datetime = Field(
        default_factory=datetime.now, description="Date of follow"
    )
    last_follow_date: datetime = Field(
        default_factory=datetime.now, description="Date of last follow"
    )
    followed: bool = Field(default=True, description="Whether the user is followed")
    unfollow_count: int = Field(default=0, description="Number of unfollows")
    sync_id: Optional[int] = Field(default=None, description="Sync ID")


def user2follower(user: User, sync_id: Optional[int]) -> Follower:
    return Follower(
        id=user.id,
        login=user.login,
        sync_id=sync_id,
    )


def users2followers(users: list[User], sync_id: Optional[int]) -> list[Follower]:
    return [user2follower(user, sync_id) for user in users]


class CreateBy(IntEnum):
    USER = 1

    FOLLOW_USER = 2
    MUTUAL_FOLLOW = 4
    MUTUAL_UNFOLLOW = 8
    SYNC_FOLLOWER = 16
    SYNC_FOLLOWING = 32
    UNFOLLOW_FOLLOWING = 64

    MAIL_STATS = 128


class Following(User, table=True):
    create_by: CreateBy = Field(description="Who created the following")
    follow_date: datetime = Field(
        default_factory=datetime.now, description="Date of follow"
    )
    last_follow_date: datetime = Field(
        default_factory=datetime.now, description="Date of last follow"
    )
    followed: bool = Field(default=True, description="Whether the user is followed")
    unfollow_count: int = Field(default=0, description="Number of unfollows")
    sync_id: Optional[int] = Field(default=None, description="Sync ID")


def user2following(
    user: User, create_by: CreateBy, sync_id: Optional[int] = None
) -> Following:
    return Following(
        id=user.id,
        login=user.login,
        create_by=create_by,
        sync_id=sync_id,
    )


def users2followings(
    users: list[User], create_by: CreateBy, sync_id: Optional[int] = None
) -> list[Following]:
    return [user2following(user, create_by, sync_id) for user in users]


class State(SQLModel, table=True):
    id: Optional[int] = Field(description="State ID", primary_key=True)
    sync_follower_id: Optional[int] = Field(
        default=None, description="Sync follower ID"
    )
    sync_follower_page: int = Field(default=1, description="Sync follower page")
    sync_following_id: Optional[int] = Field(
        default=None, description="Sync following ID"
    )
    sync_following_page: int = Field(default=1, description="Sync following page")
    follow_user_since: int = Field(default=0, description="Follow user search since")
    unfollow_following_since: int = Field(
        default=0, description="Unfollow following since"
    )
    stat_last_date: datetime = Field(
        default_factory=datetime.now, description="Last date of statistics"
    )


class HistoryState(IntEnum):
    SUCCESS = 1
    FAIL = 2


class History(SQLModel, table=True):
    id: Optional[int] = Field(description="History ID", primary_key=True)
    create_by: CreateBy = Field(description="Who created the history")
    start_date: datetime = Field(
        default_factory=datetime.now, description="Start date of history"
    )
    end_date: datetime = Field(
        default_factory=datetime.now, description="End date of history"
    )
    state: HistoryState = Field(description="State of history")
    message: Optional[str] = Field(default=None, description="Message of history")
    count: int = Field(default=0, description="Count of history")
