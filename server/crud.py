"""payload <-> 승격 컬럼 변환 및 공통 헬퍼."""

# 첨부 필드 접두사 (base64 blob 이 들어있는 필드)
_ATTACH_PREFIXES = ("doc_", "photo_")

# requests payload 에서 승격 컬럼으로 뽑을 키
_REQ_PROMOTED = [
    "docno", "status", "urgency", "risk", "scope", "reqdate", "client",
    "brand", "product", "fgcode", "pilotstatus", "pilotdate", "pdcheck", "richeck",
]

_NP_PROMOTED = {
    "week_key": "weekKey",
    "product_name": "productName",
    "brand": "brand",
    "customer": "customer",
    "category": "category",
    "launch_date": "launchDate",
    "linked_request_id": "linkedRequestId",
}


def request_columns_from_payload(payload: dict) -> dict:
    """payload 에서 requests 승격 컬럼 dict 추출."""
    cols = {k: payload.get(k) for k in _REQ_PROMOTED}
    cols["new_product_id"] = payload.get("newProductId")
    return cols


def newproduct_columns_from_payload(payload: dict) -> dict:
    cols = {col: payload.get(key) for col, key in _NP_PROMOTED.items()}
    cols["excluded"] = bool(payload.get("excluded"))
    return cols


def strip_attachment_blobs(payload: dict) -> dict:
    """목록 응답용: 첨부 필드의 base64 data 만 제거하고 메타(name/size/type)는 유지."""
    out = {}
    for k, v in payload.items():
        if any(k.startswith(p) for p in _ATTACH_PREFIXES) and isinstance(v, dict) and "data" in v:
            out[k] = {kk: vv for kk, vv in v.items() if kk != "data"}
        else:
            out[k] = v
    return out
