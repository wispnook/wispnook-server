from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_redis, get_session
from app.domain.schemas.comments import CommentCreate, CommentListResponse, CommentOut
from app.domain.schemas.posts import PostCreate, PostListResponse, PostOut
from app.rate_limit.dependency import rate_limiter
from app.services.comment_service import CommentService
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "",
    response_model=PostOut,
    status_code=201,
    dependencies=[Depends(rate_limiter)],
    summary="Create a post",
    description=(
        "Publish a new text post with an optional media URL. "
        "Idempotent: supply an `Idempotency-Key` header to prevent duplicate submissions on retry."
    ),
    response_description="The created post with its current like count",
)
async def create_post(
    payload: PostCreate,
    session: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
    user=Depends(get_current_user),
):
    service = PostService(session)
    post = await service.create_post(str(user.id), payload, redis)
    like_count = await service.count_likes(str(post.id), redis)
    return PostOut(
        id=post.id,
        author_id=post.author_id,
        content=post.content,
        media_url=post.media_url,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=like_count,
    )


@router.get(
    "/{post_id}",
    response_model=PostOut,
    summary="Get a post",
    description="Returns a single post by its UUID, including the current like count.",
    response_description="Post detail with like count",
)
async def get_post(
    post_id: str, session: AsyncSession = Depends(get_session), redis=Depends(get_redis)
):
    service = PostService(session)
    post = await service.get_post(post_id)
    like_count = await service.count_likes(post_id, redis)
    return PostOut(
        id=post.id,
        author_id=post.author_id,
        content=post.content,
        media_url=post.media_url,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=like_count,
    )


@router.get(
    "",
    response_model=PostListResponse,
    summary="List posts",
    description=(
        "Returns a paginated list of posts. "
        "Optionally filter by `author_id` to retrieve posts from a specific user."
    ),
    response_description="Paginated list of posts with like counts",
)
async def list_posts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, le=100, description="Number of results per page (max 100)"),
    author_id: str | None = Query(default=None, description="Filter posts by author UUID"),
    session: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
):
    service = PostService(session)
    items, total = await service.list_posts(page, size, author_id)
    posts = []
    for post in items:
        like_count = await service.count_likes(str(post.id), redis)
        posts.append(
            PostOut(
                id=post.id,
                author_id=post.author_id,
                content=post.content,
                media_url=post.media_url,
                created_at=post.created_at,
                updated_at=post.updated_at,
                like_count=like_count,
            )
        )
    return PostListResponse(items=posts, page=page, size=size, total=total)


@router.delete(
    "/{post_id}",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Delete a post",
    description=(
        "Permanently delete a post. " "Only the post's author or an admin can perform this action."
    ),
)
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = PostService(session)
    await service.delete_post(post_id, str(user.id), user.role == "admin")


@router.post(
    "/{post_id}/likes",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Like a post",
    description=(
        "Add a like to a post on behalf of the authenticated user. "
        "Liking an already-liked post has no effect."
    ),
)
async def like_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
    user=Depends(get_current_user),
):
    service = PostService(session)
    await service.like_post(post_id, str(user.id), redis)


@router.delete(
    "/{post_id}/likes",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Unlike a post",
    description=(
        "Remove the authenticated user's like from a post. "
        "Unliking a post that wasn't liked has no effect."
    ),
)
async def unlike_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
    user=Depends(get_current_user),
):
    service = PostService(session)
    await service.unlike_post(post_id, str(user.id), redis)


@router.get(
    "/{post_id}/likes/count",
    summary="Get like count",
    description=(
        "Returns the current like count for a post. "
        "The count is served from a Redis cache for performance."
    ),
    response_description="Object containing the post ID and its like count",
)
async def like_count(
    post_id: str, session: AsyncSession = Depends(get_session), redis=Depends(get_redis)
):
    service = PostService(session)
    count = await service.count_likes(post_id, redis)
    return {"post_id": post_id, "count": count}


@router.post(
    "/{post_id}/comments",
    response_model=CommentOut,
    status_code=201,
    dependencies=[Depends(rate_limiter)],
    summary="Add a comment",
    description="Post a comment on behalf of the authenticated user.",
    response_description="The created comment",
)
async def add_comment(
    post_id: str,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = CommentService(session)
    comment = await service.add_comment(post_id, str(user.id), payload)
    return CommentOut(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get(
    "/{post_id}/comments",
    response_model=CommentListResponse,
    summary="List comments",
    description="Returns a paginated list of comments for a post, ordered by creation time.",
    response_description="Paginated list of comments",
)
async def list_comments(
    post_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, le=100, description="Number of results per page (max 100)"),
    session: AsyncSession = Depends(get_session),
):
    service = CommentService(session)
    items, total = await service.list_comments(post_id, page, size)
    serialized = [
        CommentOut(
            id=item.id,
            post_id=item.post_id,
            author_id=item.author_id,
            content=item.content,
            created_at=item.created_at,
        )
        for item in items
    ]
    return CommentListResponse(items=serialized, page=page, size=size, total=total)
