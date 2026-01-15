# ----------------- 统一返回工具 -----------------
def success_response(message: str, data=None):
    """统一成功响应格式"""
    return {"message": message, "data": data}