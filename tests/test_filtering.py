from app.services.filter_service import NotificationFilterService


def test_filter_ignored_package():
    should_ignore, reason = NotificationFilterService.should_ignore(
        source_package="com.android.systemui",
        source_app="System",
        body="Screenshot captured",
    )
    assert should_ignore is True
    assert "ignored package list" in reason


def test_filter_otp_message():
    should_ignore, reason = NotificationFilterService.should_ignore(
        source_package="com.google.android.apps.messaging",
        source_app="SMS",
        body="Your OTP for login is 592819. Do not share with anyone.",
    )
    assert should_ignore is True
    assert "OTP" in reason


def test_filter_promotional_spam():
    should_ignore, reason = NotificationFilterService.should_ignore(
        source_package="com.shopping.app",
        source_app="Store",
        body="Mega Flash Sale! Flat 50% off on all items today only!",
    )
    assert should_ignore is True
    assert "Promotional" in reason


def test_allow_actionable_notification():
    should_ignore, reason = NotificationFilterService.should_ignore(
        source_package="com.whatsapp",
        source_app="WhatsApp",
        body="Can you send me the pitch deck by tomorrow morning?",
    )
    assert should_ignore is False
    assert reason is None
