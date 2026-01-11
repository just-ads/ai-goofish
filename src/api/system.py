"""
系统相关路由模块
处理系统配置、AI测试等功能
"""
from json import JSONDecodeError

from fastapi import APIRouter, HTTPException, Depends

from src.agent.agent import AgentConfig, AgentPresetTemplate
from src.agent.client import AgentClient
from src.api.auth import verify_token, success_response
from src.config import set_global_config, AppConfig, get_config_instance
from src.types_module import AppConfigModel, AgentConfigDict

# 创建路由器
router = APIRouter(prefix="/system", tags=["system"])

# --------------- 系统相关接口 ----------------
@router.get("", dependencies=[Depends(verify_token)])
async def api_get_system():
    """获取系统配置"""
    return success_response('获取成功', get_config_instance().get_config())


@router.post("/", dependencies=[Depends(verify_token)])
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


@router.post("/aitest", dependencies=[Depends(verify_token)])
async def api_aitest(config: AgentConfigDict):
    """测试AI配置"""
    try:
        # 提供默认值
        headers = config.get('headers')
        if headers is None:
            headers = {"Authorization": "Bearer {key}", "Content-Type": "application/json"}

        body = config.get('body')
        if body is None:
            body = {"model": "{model}", "messages": "{messages}"}

        proxy = config.get('proxy')
        if proxy is None:
            proxy = ""

        agent_config = AgentConfig(
            id=config.get('id', 'test'),
            name=config.get('name', 'test'),
            endpoint=config.get('endpoint', ''),
            api_key=config.get('api_key', ''),
            model=config.get('model', ''),
            proxy=proxy,
            headers=headers,
            body=body
        )
        client = AgentClient(agent_config)
        messages = client.ask(messages=[{"role": "user", "content": "Hello."}])
        return success_response('测试成功', f'{messages}')
    except JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"OPENAI_EXTRA_BODY: 无效JSON字符串")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {e}")


@router.get("/agent-templates", dependencies=[Depends(verify_token)])
async def api_get_agent_templates():
    """获取agent预设模板列表"""
    try:
        templates = AgentPresetTemplate.get_preset_templates()
        template_list = [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "endpoint": template.endpoint,
                "api_key": template.api_key,
                "model": template.model,
                "headers": template.headers,
                "body": template.body
            }
            for template in templates
        ]
        return success_response('获取成功', template_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {e}")