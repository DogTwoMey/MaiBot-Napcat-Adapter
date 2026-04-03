"""NapCat 适配器内部共享类型。"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, TypeAlias


NapCatActionParams: TypeAlias = Mapping[str, Any]
NapCatActionParamsInput: TypeAlias = Optional[Mapping[str, Any]]
NapCatActionResponse: TypeAlias = Dict[str, Any]
NapCatIdInput: TypeAlias = int | str
NapCatMutablePayload: TypeAlias = MutableMapping[str, Any]
NapCatOptionalIdInput: TypeAlias = int | str | None
NapCatPayload: TypeAlias = Mapping[str, Any]
NapCatPayloadDict: TypeAlias = Dict[str, Any]
NapCatPayloadList: TypeAlias = List[Dict[str, Any]]
NapCatSegment: TypeAlias = Dict[str, Any]
NapCatSegments: TypeAlias = List[Dict[str, Any]]
