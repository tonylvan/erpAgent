"""
查询历史与收藏管理 API

功能:
- 查询历史自动保存
- 收藏查询管理
- 点赞/点踩反馈
- 热门查询推荐
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hashlib

from app.api.v1.auth import get_current_user, UserInfo
from app.core.database import get_db
from app.core.ai_analysis import ai_service
import logging

logger = logging.getLogger(__name__)
def get_user_id_from_username(db, username: str) -> int:
    """根据用户名获取用户 ID"""
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM sys_users WHERE username = %s LIMIT 1", (username,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return row[0]
    raise HTTPException(status_code=404, detail="用户不存在")


def get_user_id_from_username(db, username: str) -> int:
    """根据用户名获取用户 ID"""
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM sys_users WHERE username = %s LIMIT 1", (username,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return row[0]
    raise HTTPException(status_code=404, detail="用户不存在")



router = APIRouter(prefix="/query", tags=["查询历史与收藏"])


# ==================== 数据模型 ====================

class QueryHistoryCreate(BaseModel):
    query_text: str
    sql_query: Optional[str] = None
    result_snapshot: Optional[dict] = None
    result_type: str = "table"  # table/chart/stats/text
    result_count: Optional[int] = 0
    execution_time_ms: Optional[int] = 0
    cache_hit: bool = False

class QueryHistoryResponse(BaseModel):
    query_id: int
    user_id: int
    query_text: str
    sql_query: Optional[str]
    result_type: str
    result_count: Optional[int]
    execution_time_ms: Optional[int]
    cache_hit: bool
    created_at: datetime
    is_saved: bool = False
    like_count: int = 0
    dislike_count: int = 0

class SavedQueryCreate(BaseModel):
    query_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False

class SavedQueryResponse(BaseModel):
    saved_id: int
    query_id: int
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
    is_public: bool
    view_count: int
    created_at: datetime
    updated_at: datetime
    query_text: str
    result_type: str

class FeedbackCreate(BaseModel):
    feedback_type: str  # 'like' or 'dislike'
    comment: Optional[str] = None
    trigger_ai_analysis: bool = False  # 是否触发 AI 分析（点踩时使用）

class AIAnalysisResponse(BaseModel):
    query_id: int
    analysis: str  # AI 分析内容
    suggested_optimizations: List[str]  # 优化建议
    confidence_score: float  # 置信度
    requires_user_confirmation: bool = True


# ==================== API 端点 ====================

@router.post("/history", response_model=dict)
def save_query_history(
    history_data: QueryHistoryCreate,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    保存查询历史（自动调用）
    
    - **query_text**: 用户查询文本
    - **sql_query**: 生成的 SQL
    - **result_snapshot**: 结果快照
    - **result_type**: 结果类型
    - **execution_time_ms**: 执行时间
    - **cache_hit**: 是否命中缓存
    """
    try:
        cursor = db.cursor()
        
        # 生成查询哈希（用于去重）
        query_hash = hashlib.sha256(history_data.query_text.encode()).hexdigest()
        
        # 插入查询历史
        cursor.execute("""
            INSERT INTO query_history 
            (user_id, query_text, sql_query, result_snapshot, result_type, 
             result_count, execution_time_ms, cache_hit, query_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING query_id
        """, (
            get_user_id_from_username(db, current_user.username),
            history_data.query_text,
            history_data.sql_query,
            history_data.result_snapshot,
            history_data.result_type,
            history_data.result_count,
            history_data.execution_time_ms,
            history_data.cache_hit,
            query_hash
        ))
        
        query_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()
        
        return {
            "success": True,
            "query_id": query_id,
            "message": "查询历史已保存"
        }
    
    except Exception as e:
        logger.error(f"保存查询历史失败：{e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存失败：{str(e)}"
        )


@router.get("/history", response_model=List[QueryHistoryResponse])
def get_query_history(
    limit: int = 50,
    offset: int = 0,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    查询我的查询历史
    
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                q.query_id, q.user_id, q.query_text, q.sql_query,
                q.result_type, q.result_count, q.execution_time_ms,
                q.cache_hit, q.created_at,
                CASE WHEN s.saved_id IS NOT NULL THEN true ELSE false END as is_saved,
                COUNT(f.feedback_id) FILTER (WHERE f.feedback_type = 'like') as like_count,
                COUNT(f.feedback_id) FILTER (WHERE f.feedback_type = 'dislike') as dislike_count
            FROM query_history q
            LEFT JOIN saved_queries s ON q.query_id = s.query_id
            LEFT JOIN query_feedback f ON q.query_id = f.query_id
            WHERE q.user_id = %s
            GROUP BY q.query_id, s.saved_id
            ORDER BY q.created_at DESC
            LIMIT %s OFFSET %s
        """, (get_user_id_from_username(db, current_user.username), limit, offset))
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [
            QueryHistoryResponse(
                query_id=row[0],
                user_id=row[1],
                query_text=row[2],
                sql_query=row[3],
                result_type=row[4],
                result_count=row[5],
                execution_time_ms=row[6],
                cache_hit=row[7],
                created_at=row[8],
                is_saved=row[9],
                like_count=row[10],
                dislike_count=row[11]
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"查询历史记录失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败：{str(e)}"
        )


@router.post("/save", response_model=dict)
def save_query(
    save_data: SavedQueryCreate,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    收藏查询
    
    - **query_id**: 查询历史 ID
    - **title**: 收藏标题
    - **description**: 描述
    - **tags**: 标签数组
    - **is_public**: 是否公开
    """
    try:
        cursor = db.cursor()
        
        # 检查查询是否存在
        cursor.execute("""
            SELECT query_id FROM query_history WHERE query_id = %s AND user_id = %s
        """, (save_data.query_id, get_user_id_from_username(db, current_user.username)))
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="查询不存在"
            )
        
        # 插入收藏
        cursor.execute("""
            INSERT INTO saved_queries 
            (user_id, query_id, title, description, tags, is_public)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING saved_id
        """, (
            get_user_id_from_username(db, current_user.username),
            save_data.query_id,
            save_data.title,
            save_data.description,
            save_data.tags,
            save_data.is_public
        ))
        
        saved_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()
        
        return {
            "success": True,
            "saved_id": saved_id,
            "message": "收藏成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏查询失败：{e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收藏失败：{str(e)}"
        )


@router.get("/saved", response_model=List[SavedQueryResponse])
def get_saved_queries(
    limit: int = 50,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    查询我的收藏
    
    - **limit**: 返回数量限制
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                s.saved_id, s.query_id, s.title, s.description,
                s.tags, s.is_public, s.view_count, s.created_at, s.updated_at,
                q.query_text, q.result_type
            FROM saved_queries s
            JOIN query_history q ON s.query_id = q.query_id
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
            LIMIT %s
        """, (get_user_id_from_username(db, current_user.username), limit))
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [
            SavedQueryResponse(
                saved_id=row[0],
                query_id=row[1],
                title=row[2],
                description=row[3],
                tags=row[4],
                is_public=row[5],
                view_count=row[6],
                created_at=row[7],
                updated_at=row[8],
                query_text=row[9],
                result_type=row[10]
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"查询收藏列表失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败：{str(e)}"
        )


@router.delete("/saved/{saved_id}")
def delete_saved_query(
    saved_id: int,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    删除收藏
    
    - **saved_id**: 收藏 ID
    """
    try:
        cursor = db.cursor()
        
        # 检查是否属于自己的收藏
        cursor.execute("""
            SELECT saved_id FROM saved_queries 
            WHERE saved_id = %s AND user_id = %s
        """, (saved_id, get_user_id_from_username(db, current_user.username)))
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="收藏不存在或无权删除"
            )
        
        # 删除收藏
        cursor.execute("""
            DELETE FROM saved_queries WHERE saved_id = %s
        """, (saved_id,))
        
        db.commit()
        cursor.close()
        
        return {
            "success": True,
            "message": "删除成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除收藏失败：{e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败：{str(e)}"
        )


@router.post("/feedback/{query_id}")
def submit_feedback(
    query_id: int,
    feedback_data: FeedbackCreate,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    提交查询反馈（点赞/点踩）
    
    - **query_id**: 查询 ID
    - **feedback_type**: 'like' 或 'dislike'
    - **comment**: 反馈意见
    - **trigger_ai_analysis**: 是否触发 AI 分析（点踩时推荐设为 true）
    
    点踩流程:
    1. 用户点踩 → trigger_ai_analysis=true
    2. AI 分析原因并生成优化建议
    3. 返回分析结果供用户确认
    4. 用户确认后保存反馈并执行优化
    """
    try:
        cursor = db.cursor()
        
        # 如果是点踩且要求 AI 分析
        if feedback_data.feedback_type == 'dislike' and feedback_data.trigger_ai_analysis:
            # 获取查询详情
            cursor.execute("""
                SELECT query_text, sql_query, result_type, execution_time_ms
                FROM query_history
                WHERE query_id = %s AND user_id = %s
            """, (query_id, get_user_id_from_username(db, current_user.username)))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="查询不存在"
                )
            
            query_text, sql_query, result_type, execution_time_ms = row
            
            # 调用 AI 服务进行分析
            ai_result = ai_service.analyze_query_feedback(
                query_text=query_text,
                sql_query=sql_query,
                result_type=result_type,
                execution_time_ms=execution_time_ms,
                user_comment=feedback_data.comment
            )
            
            cursor.close()
            
            return {
                "success": True,
                "requires_confirmation": True,
                "analysis": ai_result["analysis"],
                "suggested_optimizations": ai_result["suggested_optimizations"],
                "confidence_score": ai_result["confidence_score"],
                "query_id": query_id,
                "message": "AI 分析完成，请确认分析结果"
            }
        
        # 普通反馈（点赞或点踩不触发 AI 分析）
        cursor.execute("""
            INSERT INTO query_feedback (query_id, user_id, feedback_type, comment)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (query_id, user_id) DO UPDATE
            SET feedback_type = EXCLUDED.feedback_type, comment = EXCLUDED.comment
        """, (query_id, get_user_id_from_username(db, current_user.username), feedback_data.feedback_type, feedback_data.comment))
        
        db.commit()
        cursor.close()
        
        return {
            "success": True,
            "message": "反馈已提交"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败：{e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交失败：{str(e)}"
        )


@router.post("/feedback/{query_id}/confirm")
def confirm_feedback_with_ai(
    query_id: int,
    feedback_data: FeedbackCreate,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    确认 AI 分析后的反馈（用户确认 AI 分析后调用）
    
    - **query_id**: 查询 ID
    - **feedback_type**: 'dislike'（仅支持点踩）
    - **comment**: 用户对 AI 分析的补充意见
    - **ai_analysis_confirmed**: 是否确认 AI 分析
    
    确认后执行:
    1. 保存反馈到数据库
    2. 记录 AI 分析结果
    3. 触发查询优化流程
    4. 返回优化后的查询结果
    """
    try:
        cursor = db.cursor()
        
        # 验证查询所有权
        cursor.execute("""
            SELECT query_id, query_text, sql_query FROM query_history
            WHERE query_id = %s AND user_id = %s
        """, (query_id, get_user_id_from_username(db, current_user.username)))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="查询不存在"
            )
        
        # 保存反馈
        cursor.execute("""
            INSERT INTO query_feedback (query_id, user_id, feedback_type, comment)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (query_id, user_id) DO UPDATE
            SET feedback_type = EXCLUDED.feedback_type, 
                comment = EXCLUDED.comment,
                updated_at = CURRENT_TIMESTAMP
        """, (query_id, get_user_id_from_username(db, current_user.username), 'dislike', feedback_data.comment))
        
        db.commit()
        cursor.close()
        
        # TODO: 触发查询优化流程
        # 1. 调用 AI 重新生成查询
        # 2. 执行优化后的查询
        # 3. 返回新结果
        
        return {
            "success": True,
            "message": "反馈已确认，正在执行优化...",
            "query_id": query_id,
            "optimization_status": "processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认反馈失败：{e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认失败：{str(e)}"
        )


@router.get("/popular")
def get_popular_queries(
    limit: int = 10,
    db=Depends(get_db)
):
    """
    查询热门查询（公共）
    
    - **limit**: 返回数量限制
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                q.query_id, q.query_text, q.result_type,
                COUNT(s.saved_id) as save_count,
                COUNT(f.feedback_id) FILTER (WHERE f.feedback_type = 'like') as like_count
            FROM query_history q
            LEFT JOIN saved_queries s ON q.query_id = s.query_id AND s.is_public = true
            LEFT JOIN query_feedback f ON q.query_id = f.query_id
            WHERE q.created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY q.query_id, q.query_text, q.result_type
            ORDER BY save_count DESC, like_count DESC
            LIMIT %s
        """, (limit,))
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [
            {
                "query_id": row[0],
                "query_text": row[1],
                "result_type": row[2],
                "save_count": row[3],
                "like_count": row[4]
            }
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"查询热门查询失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败：{str(e)}"
        )
