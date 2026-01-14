"""
系统相关路由模块
处理系统配置、AI测试等功能
"""

from fastapi import APIRouter, HTTPException, Depends

from src.api.auth import verify_token, success_response
from src.config import set_global_config, AppConfig, get_config_instance
from src.types_module import AppConfigModel

# 创建路由器
router = APIRouter(prefix="/system", tags=["system"])

# --------------- 系统相关接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_system():
    """获取系统配置"""
    return success_response('获取成功', get_config_instance().get_config())


@router.post("", dependencies=[Depends(verify_token)])
async def api_save_system(config: AppConfigModel):
    """保存系统配置"""
    try:
        validation_errors = AppConfig.validate_config(config)
        if validation_errors:
            error_messages = []
            for section, errors in validation_errors.items():
                for error in errors:
                    error_messages.append(f"{section}: {error}")
            raise HTTPException(
                status_code=400,
                detail=f"配置验证失败: {'; '.join(error_messages)}"
            )

        success = set_global_config(config)
        if not success:
            raise HTTPException(status_code=500, detail="配置保存失败")

        updated_config = get_config_instance().get_config()
        return success_response('配置保存成功', updated_config)

    except HTTPException:
        raise
    except Exception as e:
        from src.utils.logger import logger
        logger.error(f"保存系统配置时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置时发生未知错误: {str(e)}")
