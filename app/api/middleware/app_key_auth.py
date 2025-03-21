from functools import wraps
from app.infrastructure.database.repositories.user_app_repository import UserAppRepository
from flask import request, g
from app.core.exceptions import AuthenticationException, NotFoundException
from app.core.status_codes import APPLICATION_NOT_FOUND
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
        user_app_repo = UserAppRepository(db_session)
        
        # 验证应用密钥
        app = user_app_repo.get_by_app_key(app_key)
        if not app:
            raise NotFoundException("无效的应用密钥", APPLICATION_NOT_FOUND)
        
        # 验证应用是否已发布
        if not app.published:
            raise AuthenticationException("该应用未发布，无法使用")
        
        # 将应用信息和用户ID存储在请求上下文中
        g.app_key = app_key
        g.app = app
        g.user_id = app.user_id
        g.db_session = db_session
        
        return f(*args, **kwargs)
    
    return decorated_function