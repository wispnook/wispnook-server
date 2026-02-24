import pytest


@pytest.mark.integration
def test_register_and_login_flow(client):
    payload = {"email": "tester@example.com", "username": "tester", "password": "Password123!"}
    register = client.post("/auth/register", json=payload)
    assert register.status_code == 201
    tokens = register.json()
    assert "access_token" in tokens

    login = client.post(
        "/auth/login", json={"username": payload["username"], "password": payload["password"]}
    )
    assert login.status_code == 200
    data = login.json()
    assert data["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200

    update = client.patch("/users/me", json={"bio": "Hello world"}, headers=headers)
    assert update.status_code == 200

    post_resp = client.post("/posts", json={"content": "First post!"}, headers=headers)
    assert post_resp.status_code == 201
    post_id = post_resp.json()["id"]

    assert client.get(f"/posts/{post_id}", headers=headers).status_code == 200
    assert client.get("/posts", headers=headers).status_code == 200

    like = client.post(f"/posts/{post_id}/likes", headers=headers)
    assert like.status_code == 204
    assert client.get(f"/posts/{post_id}/likes/count", headers=headers).json()["count"] >= 1
    assert client.delete(f"/posts/{post_id}/likes", headers=headers).status_code == 204

    comment_resp = client.post(
        f"/posts/{post_id}/comments", json={"content": "Nice post!"}, headers=headers
    )
    assert comment_resp.status_code == 201
    comment_id = comment_resp.json()["id"]
    assert client.get(f"/posts/{post_id}/comments", headers=headers).status_code == 200

    assert client.delete(f"/comments/{comment_id}", headers=headers).status_code == 204
    assert client.get("/feed", headers=headers).status_code == 200

    second_payload = {
        "email": "second@example.com",
        "username": "second-user",
        "password": "Password123!",
    }
    assert client.post("/auth/register", json=second_payload).status_code == 201

    search = client.get("/users", params={"query": "second-user"}).json()
    target_id = search["items"][0]["id"]
    assert client.post(f"/follows/{target_id}", headers=headers).status_code == 204
    assert client.get(f"/follows/{target_id}/followers").status_code == 200
    assert client.delete(f"/follows/{target_id}", headers=headers).status_code == 204
