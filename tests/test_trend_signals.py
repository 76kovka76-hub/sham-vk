import unittest
from datetime import datetime, timezone
from email.utils import format_datetime
from unittest.mock import Mock

from trend_signals import current_topics


class TrendSignalsTests(unittest.TestCase):
    def test_current_technology_tags_only(self):
        date = format_datetime(datetime(2026, 11, 13, 12, tzinfo=timezone.utc))
        feed = f"""<rss><channel>
        <item><title>Роботы в смартфонах: новый ИИ</title><pubDate>{date}</pubDate></item>
        <item><title>Автомобили на Марсе</title><pubDate>{date}</pubDate></item>
        <item><title>Жертвы аварии</title><pubDate>{date}</pubDate></item>
        </channel></rss>""".encode("utf-8")
        reply = Mock(content=feed)
        reply.raise_for_status.return_value = None
        result = current_topics(
            now=datetime(2026, 11, 13, 13, tzinfo=timezone.utc),
            getter=lambda *args, **kwargs: reply)
        self.assertIn("роботы", result)
        self.assertIn("автомобили", result)
        self.assertNotIn("жертвы аварии", result)

    def test_failure_never_breaks_scheduled_posts(self):
        def missing(*args, **kwargs):
            raise __import__("requests").Timeout("feed unavailable")
        self.assertEqual(current_topics(getter=missing), [])


if __name__ == "__main__":
    unittest.main()
