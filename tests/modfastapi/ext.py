from .base import SearchHeaders, SearchParams


class SearchParamsExt(SearchParams, extends=True):
    tags: list[str] = []


class SearchHeadersExt(SearchHeaders, extends=True):
    x_token: str = ""
