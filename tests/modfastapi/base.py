from typing import Annotated, Any

from fastapi import APIRouter, Header, Query

from extendable_pydantic import ExtendableBaseModel


class SearchParams(ExtendableBaseModel):
    name: str = ""


class SearchHeaders(ExtendableBaseModel):
    user_agent: str = ""


router = APIRouter()


@router.get("/search")
def search(params: Annotated[SearchParams, Query()]) -> dict[str, Any]:
    return params.model_dump()


@router.get("/headers")
def headers(params: Annotated[SearchHeaders, Header()]) -> dict[str, Any]:
    return params.model_dump()
