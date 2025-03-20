from functools import wraps
from flask import request, g
from app.core.exceptions import AuthenticationException, NotFoundException
from app.core.status_codes import UNAUTHORIZED, APPLICATION_NOT_FOUND
from app.infrastructure.database.repositories.application_repository import (
    ApplicationRepository,
)
from app.infrastructure.database.session import get_db_session


def app_key_required(f):
    """应用密钥验证装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头中获取应用密钥
        app_key = request.headers.get("X-App-Key")
        if not app_key:
            raise AuthenticationException("缺少应用密钥")

        # 初始化存储库
        db_session = get_db_session()
        app_repo = ApplicationRepository(db_session)

        # 验证应用密钥
        app = app_repo.get_by_app_key(app_key)
        if not app:
            raise NotFoundException("无效的应用密钥", APPLICATION_NOT_FOUND)

        # 验证应用是否启用
        if not app.is_active:
            raise AuthenticationException("应用已禁用")

        # 将应用信息和用户ID存储在请求上下文中
        g.application = {"id": app.id, "name": app.name, "app_key": app.app_key}
        g.user_id = app.user_id
        g.db_session = db_session

        return f(*args, **kwargs)

    return decorated_function
