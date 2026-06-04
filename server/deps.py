"""요청자 프로필 추출.

1단계: 프론트엔드가 보내는 X-User-* 헤더를 신뢰(사내망 한정).
2단계(SSO): 이 함수만 세션/토큰 기반으로 교체하면 라우터는 그대로.
"""
from fastapi import Header
from typing import Optional
from urllib.parse import unquote


class CurrentUser:
    def __init__(self, name: str = "", dept: str = "", role: str = ""):
        self.name = name
        self.dept = dept
        self.role = role

    @property
    def can_write(self) -> bool:
        # viewer(참조자)는 읽기 전용. role 미지정은 1단계 호환을 위해 허용.
        return self.role != "viewer"


def get_current_user(
    x_user_name: Optional[str] = Header(default=""),
    x_user_dept: Optional[str] = Header(default=""),
    x_user_role: Optional[str] = Header(default=""),
) -> CurrentUser:
    # 프론트엔드가 한글 이름을 percent-encoding 해서 보냄
    return CurrentUser(
        name=unquote(x_user_name or "")[:60],
        dept=(x_user_dept or "")[:40],
        role=(x_user_role or "")[:20],
    )
