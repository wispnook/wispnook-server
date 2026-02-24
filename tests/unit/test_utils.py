from app.utils.exceptions import NotFoundError, RateLimitError, to_http_exception


def test_to_http_exception_mappings():
    http_exc = to_http_exception(NotFoundError("missing"))
    assert http_exc.status_code == 404
    assert http_exc.detail["code"] == "resource_not_found"

    http_exc = to_http_exception(RateLimitError("slow down"))
    assert http_exc.status_code == 429
    assert http_exc.detail["code"] == "rate_limited"
