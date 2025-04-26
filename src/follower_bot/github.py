from typing import Dict, List, Optional

import requests
from ratelimit import limits, sleep_and_retry

from .model import User

PER_PAGE_MAX = 100


def _create_headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Follower Bot",
        "Authorization": f"token {token}",
    }


# https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
@sleep_and_retry
@limits(calls=5000, period=3600)
def _fetch(
    method: str, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None
) -> requests.Response:
    return requests.request(method, url, headers=headers, params=params)


def get_search_users(
    page: int, q: str, token: str, per_page: int = PER_PAGE_MAX
) -> List[User]:
    # https://docs.github.com/en/rest/search/search#search-users
    url = "https://api.github.com/search/users"
    params = {
        "page": page,
        "per_page": per_page,
        "q": q,
    }
    headers = _create_headers(token)
    response: requests.Response = _fetch("GET", url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return [User(**user) for user in data["items"]]


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
