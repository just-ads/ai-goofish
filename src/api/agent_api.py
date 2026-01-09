"""
Agent管理API接口
"""
from fastapi import APIRouter, HTTPException, status

from src.services.agent_service import get_agent_manager
from src.types.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentListResponse
)
from src.utils.logger import logger

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/", response_model=AgentListResponse, summary="获取所有Agent")
async def list_agents():
    """
    获取所有Agent配置列表

    Returns:
        Agent列表响应
    """
    try:
        manager = get_agent_manager()
        result = manager.list_agents()
        return result
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取Agent列表失败"
        )


@router.get("/{agent_id}", response_model=AgentResponse, summary="获取指定Agent")
async def get_agent(agent_id: str):
    """
    获取指定Agent配置

    Args:
        agent_id: Agent ID

    Returns:
        Agent配置响应
    """
    try:
        manager = get_agent_manager()
        agent = manager.get_agent(agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent不存在: {agent_id}"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取Agent失败"
        )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, summary="创建Agent")
async def create_agent(agent_data: AgentCreateRequest):
    """
    创建新的Agent配置

    Args:
        agent_data: Agent创建请求数据

    Returns:
        创建的Agent响应
    """
    try:
        manager = get_agent_manager()

        # 验证配置
        errors = manager.validate_agent_config(dict(agent_data))
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )

        agent = manager.create_agent(agent_data)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建Agent失败，可能是ID已存在"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建Agent失败"
        )


@router.put("/{agent_id}", response_model=AgentResponse, summary="更新Agent")
async def update_agent(agent_id: str, agent_data: AgentUpdateRequest):
    """
    更新指定Agent配置

    Args:
        agent_id: Agent ID
        agent_data: Agent更新请求数据

    Returns:
        更新后的Agent响应
    """
    try:
        manager = get_agent_manager()

        # 验证配置（如果有值）
        if any(v is not None for v in agent_data.values()):
            errors = manager.validate_agent_config(dict(agent_data))
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"errors": errors}
                )

        agent = manager.update_agent(agent_id, agent_data)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent不存在: {agent_id}"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新Agent失败"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除Agent")
async def delete_agent(agent_id: str):
    """
    删除指定Agent配置

    Args:
        agent_id: Agent ID
    """
    try:
        manager = get_agent_manager()
        success = manager.delete_agent(agent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent不存在: {agent_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除Agent失败"
        )


@router.get("/{agent_id}/config", summary="获取Agent完整配置")
async def get_agent_config(agent_id: str):
    """
    获取Agent完整配置（包含敏感信息如API密钥）

    Args:
        agent_id: Agent ID

    Returns:
        Agent完整配置
    """
    try:
        manager = get_agent_manager()
        agent_config = manager.get_agent_config(agent_id)

        if agent_config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent不存在: {agent_id}"
            )

        return agent_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Agent配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取Agent配置失败"
        )


@router.post("/{agent_id}/set-default", response_model=AgentResponse, summary="设置默认Agent")
async def set_default_agent(agent_id: str):
    """
    设置指定Agent为默认Agent

    Args:
        agent_id: Agent ID

    Returns:
        更新后的Agent响应
    """
    try:
        manager = get_agent_manager()

        # 先检查Agent是否存在
        agent = manager.get_agent(agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent不存在: {agent_id}"
            )

        # 设置为默认
        success = manager.set_default_agent(agent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设置默认Agent失败"
            )

        # 返回更新后的Agent
        return manager.get_agent(agent_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置默认Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置默认Agent失败"
        )


@router.get("/default/", response_model=AgentResponse, summary="获取默认Agent")
async def get_default_agent():
    """
    获取默认Agent配置

    Returns:
        默认Agent响应
    """
    try:
        manager = get_agent_manager()
        agent = manager.get_default_agent()

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有找到默认Agent"
            )

        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取默认Agent失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取默认Agent失败"
        )