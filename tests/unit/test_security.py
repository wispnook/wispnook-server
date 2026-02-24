from app.auth import security


def test_password_hash_roundtrip():
    password = "SuperSecret123"
    hashed = security.hash_password(password)
    assert hashed != password
    assert security.verify_password(password, hashed)


def test_jwt_cycle():
    token, _ = security.create_access_token("user-id")
    payload = security.decode_token(token)
    assert payload["sub"] == "user-id"
