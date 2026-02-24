from app.domain.events import schemas


def test_user_created_schema_roundtrip():
    event = schemas.UserCreatedEvent(
        user={
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "username": "user",
        }
    )
    dumped = event.model_dump()
    parsed = schemas.UserCreatedEvent.model_validate(dumped)
    assert parsed.user.username == "user"


def test_post_liked_schema():
    event = schemas.PostLikedEvent(
        post_id="123e4567-e89b-12d3-a456-426614174000",
        user_id="123e4567-e89b-12d3-a456-426614174111",
    )
    assert str(event.post_id) == "123e4567-e89b-12d3-a456-426614174000"
