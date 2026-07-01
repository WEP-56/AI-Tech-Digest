"""模型配置路由"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ModelConfig
from app.security import encrypt_value, decrypt_value, mask_value
from app.schemas import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse, ModelTestResult
from app.services.auth_service import get_current_user
from app.services.llm_client import create_llm_client

router = APIRouter(prefix="/api/admin/models", tags=["模型配置"])


def _to_response(config: ModelConfig) -> ModelConfigResponse:
    return ModelConfigResponse(
        id=config.id,
        name=config.name,
        provider_type=config.provider_type,
        base_url=config.base_url,
        model_name=config.model_name,
        temperature=config.temperature,
        max_output_tokens=config.max_output_tokens,
        timeout_seconds=config.timeout_seconds,
        retry_count=config.retry_count,
        anthropic_version=config.anthropic_version,
        enabled=config.enabled,
        is_default=config.is_default,
        api_key_masked=mask_value(decrypt_value(config.api_key_encrypted)),
        has_api_key=bool(config.api_key_encrypted),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("", response_model=list[ModelConfigResponse])
def list_models(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(ModelConfig).order_by(ModelConfig.created_at.desc()).all()


@router.post("", response_model=ModelConfigResponse)
def create_model(req: ModelConfigCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = ModelConfig(
        name=req.name,
        provider_type=req.provider_type,
        base_url=req.base_url,
        api_key_encrypted=encrypt_value(req.api_key),
        model_name=req.model_name,
        temperature=req.temperature,
        max_output_tokens=req.max_output_tokens,
        timeout_seconds=req.timeout_seconds,
        retry_count=req.retry_count,
        anthropic_version=req.anthropic_version,
        enabled=req.enabled,
        is_default=req.is_default,
    )
    # 如果设为默认，取消其他默认
    if req.is_default:
        db.query(ModelConfig).update({ModelConfig.is_default: False})
    db.add(config)
    db.commit()
    db.refresh(config)
    return _to_response(config)


@router.get("/{model_id}", response_model=ModelConfigResponse)
def get_model(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return _to_response(config)


@router.put("/{model_id}", response_model=ModelConfigResponse)
def update_model(model_id: int, req: ModelConfigUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    if req.name is not None:
        config.name = req.name
    if req.provider_type is not None:
        config.provider_type = req.provider_type
    if req.base_url is not None:
        config.base_url = req.base_url
    if req.api_key is not None:
        config.api_key_encrypted = encrypt_value(req.api_key)
    if req.model_name is not None:
        config.model_name = req.model_name
    if req.temperature is not None:
        config.temperature = req.temperature
    if req.max_output_tokens is not None:
        config.max_output_tokens = req.max_output_tokens
    if req.timeout_seconds is not None:
        config.timeout_seconds = req.timeout_seconds
    if req.retry_count is not None:
        config.retry_count = req.retry_count
    if req.anthropic_version is not None:
        config.anthropic_version = req.anthropic_version
    if req.enabled is not None:
        config.enabled = req.enabled
    if req.is_default is not None:
        if req.is_default:
            db.query(ModelConfig).update({ModelConfig.is_default: False})
        config.is_default = req.is_default
    db.commit()
    db.refresh(config)
    return _to_response(config)


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    db.delete(config)
    db.commit()
    return {"success": True, "message": "已删除"}


@router.post("/{model_id}/test", response_model=ModelTestResult)
def test_model(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    api_key = decrypt_value(config.api_key_encrypted)
    if not api_key:
        return ModelTestResult(success=False, message="API Key为空")
    client_config = {
        "provider_type": config.provider_type,
        "base_url": config.base_url,
        "api_key": api_key,
        "model_name": config.model_name,
        "temperature": config.temperature,
        "max_output_tokens": 100,
        "timeout_seconds": config.timeout_seconds,
        "retry_count": 0,
        "anthropic_version": config.anthropic_version,
    }
    start = time.time()
    try:
        client = create_llm_client(client_config)
        result = client.generate("你是一个测试助手。", "请用一句话回复：模型连接正常。")
        latency = int((time.time() - start) * 1000)
        if result.success:
            return ModelTestResult(success=True, message="连接成功", response_text=result.text[:200], latency_ms=latency)
        else:
            return ModelTestResult(success=False, message=result.error, latency_ms=latency)
    except Exception as e:
        return ModelTestResult(success=False, message=str(e), latency_ms=int((time.time() - start) * 1000))


@router.post("/{model_id}/set-default")
def set_default(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    db.query(ModelConfig).update({ModelConfig.is_default: False})
    config.is_default = True
    db.commit()
    return {"success": True, "message": "已设为默认模型"}
