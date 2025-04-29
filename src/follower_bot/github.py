from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from loguru import logger
from rate_keeper import RateKeeper

from .model import User

PER_PAGE_MAX = 100

# UTC timestamp clock
timestamp_clock = datetime.now(timezone.utc).timestamp
# https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
rate_keeper = RateKeeper(limit=5000, period=3600, clock=timestamp_clock)


def _create_headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Follower Bot",
        "Authorization": f"token {token}",
    }


@rate_keeper.decorator
def _fetch(
    method: str, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None
) -> requests.Response:
    logger.debug(f"Delay for {rate_keeper.delay_time:.2f} seconds")
    response = requests.request(method, url, headers=headers, params=params)

    headers_map = {
        "x-ratelimit-limit": rate_keeper.update_limit,
        "x-ratelimit-used": rate_keeper.update_used,
        "x-ratelimit-reset": rate_keeper.update_reset,
    }

    for key, value in response.headers.items():
        lower_key = key.lower()
        if lower_key in headers_map:
            headers_map[lower_key](int(value))

    logger.debug(f"Recommended delay : {rate_keeper.recommend_delay:.2f} seconds")
    logger.debug(f"Rate Keeper: {rate_keeper}")
    return response


def get_search_users(
    since: int, token: str, per_page: int = PER_PAGE_MAX
) -> List[User]:
    # https://docs.github.com/zh/rest/users/users?apiVersion=2022-11-28#list-users
    url = "https://api.github.com/users"
    params = {
        "since": since,
        "per_page": per_page,
    }
    headers = _create_headers(token)
    response: requests.Response = _fetch("GET", url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return [User(**user) for user in data]


def put_user_following(user_login: str, token: str) -> bool:
    # https://docs.github.com/en/rest/users/followers#follow-a-user
    url = f"https://api.github.com/user/following/{user_login}"
    headers = _create_headers(token)
    response: requests.Response = _fetch("PUT", url, headers=headers)
    response.raise_for_status()
    return response.status_code == 204


def delete_user_following(user_login: str, token: str) -> bool:
    # https://docs.github.com/en/rest/users/followers#unfollow-a-user
    url = f"https://api.github.com/user/following/{user_login}"
    headers = _create_headers(token)
    response: requests.Response = _fetch("DELETE", url, headers=headers)
    response.raise_for_status()
    return response.status_code == 204


def get_user_followers(
    page: int, token: str, per_page: int = PER_PAGE_MAX
) -> List[User]:
    # https://docs.github.com/en/rest/users/followers#list-followers-of-the-authenticated-user
    url = "https://api.github.com/user/followers"
    params = {
        "page": page,
        "per_page": per_page,
    }
    headers = _create_headers(token)
    response: requests.Response = _fetch("GET", url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return [User(**user) for user in data]
