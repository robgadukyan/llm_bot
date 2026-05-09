from tools.email import build_email_body


def test_build_email_body_contains_package():
    package = "# Title\nDemo Lesson Plan"
    body = build_email_body(package)
    assert "Demo Lesson Plan" in body
    assert "Dear colleague" in body
