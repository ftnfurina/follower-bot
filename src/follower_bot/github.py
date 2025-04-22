from typing import Dict, List, Optional

import requests
from ratelimit import limits, sleep_and_retry

from .model import User


# https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
@sleep_and_retry
@limits(calls=5000, period=3600)
def _fetch(
    method: str, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None
) -> requests.Response:
    return requests.request(method, url, headers=headers, params=params)


def fetch_users(page: int, per_page: int, q: str, token: str) -> List[User]:
    # https://docs.github.com/en/rest/search/search#search-users
    url = "https://api.github.com/search/users"
    params = {
        "page": page,
        "per_page": per_page,
        "q": q,
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Follower Bot",
        "Authorization": f"token {token}",
    }

    response: requests.Response = _fetch("GET", url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    return [User(**user) for user in data["items"]]


def fetch_follow_user(user: User, token: str) -> bool:
    # https://docs.github.com/en/rest/users/followers#follow-a-user
    url = f"https://api.github.com/user/following/{user.login}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Follower Bot",
    }
    response: requests.Response = _fetch("PUT", url, headers=headers)
    return response.status_code == 204
