from flask import jsonify

def handle_exception(e):
    """全局异常处理器"""
    # 记录错误
    # current_app.logger.error(f"Unhandled exception: {str(e)}")
    
    # 返回JSON格式的错误响应
    response = {
        "success": False,
        "error": {
            "type": e.__class__.__name__,
            "message": str(e)
        }
    }
    
    # 确定HTTP状态码
    status_code = getattr(e, 'code', 500)
    
    return jsonify(response), status_code