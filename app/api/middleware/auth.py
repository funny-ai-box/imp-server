"""认证中间件"""

from functools import wraps
from flask import request, g, current_app
import jwt
from app.core.exceptions import AuthenticationException
from app.core.status_codes import UNAUTHORIZED, TOKEN_EXPIRED, INVALID_TOKEN
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.session import get_db_session


def auth_required(f):
    """JWT认证装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头中获取JWT令牌
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationException("缺少认证令牌")

        # 提取令牌
        token_parts = auth_header.split()
        print(token_parts)
        if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
            raise AuthenticationException("无效的认证格式")

        token = token_parts[1]

        try:
            # 解码令牌
            secret_key = current_app.config.get("JWT_SECRET_KEY")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])

            # 获取用户ID
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException("无效的令牌")

            # 初始化存储库
            db_session = get_db_session()
            user_repo = UserRepository(db_session)

            # 验证用户是否存在
            user = user_repo.find_by_id(user_id)
            if not user:
                raise AuthenticationException("用户不存在")

            # 验证用户状态
            if not user.is_active:
                raise AuthenticationException("账户已禁用")

            # 将用户ID和会话存储在请求上下文中
            g.user_id = user_id
            g.db_session = db_session

            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("令牌已过期")
        except jwt.InvalidTokenError:
            raise AuthenticationException("无效的令牌")
        except Exception as e:
            if isinstance(e, AuthenticationException):
                raise
            raise AuthenticationException(f"认证失败: {str(e)}")

    return decorated_function


def admin_required(f):
    """管理员权限装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先验证JWT令牌
        @auth_required
        def check_admin(*args, **kwargs):
            # 获取用户
            db_session = g.db_session
            user_repo = UserRepository(db_session)
            user = user_repo.find_by_id(g.user_id)

            # 验证管理员权限
            if not user.is_admin:
                raise AuthenticationException("需要管理员权限")

            return f(*args, **kwargs)

        return check_admin(*args, **kwargs)

    return decorated_function
