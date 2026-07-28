import os
import tempfile
import unittest
from unittest import mock

from provider_example import server


class DelayRangeTest(unittest.TestCase):
    def test_defaults(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(server._delay_range_seconds(), (23.0, 40.0))

    def test_environment_override(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PROVIDER_DELAY_MIN_SECONDS": "0.05",
                "PROVIDER_DELAY_MAX_SECONDS": "0.15",
            },
            clear=True,
        ):
            self.assertEqual(server._delay_range_seconds(), (0.05, 0.15))

    def test_rejects_reversed_range(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PROVIDER_DELAY_MIN_SECONDS": "2",
                "PROVIDER_DELAY_MAX_SECONDS": "1",
            },
            clear=True,
        ):
            with self.assertRaises(ValueError):
                server._delay_range_seconds()


class TaskDelayTest(unittest.TestCase):
    def test_uses_explicit_task_delay(self) -> None:
        self.assertEqual(
            server._task_delay_seconds({"delay_seconds": 3.25}, 23.0, 40.0),
            3.25,
        )

    def test_falls_back_to_configured_range(self) -> None:
        with mock.patch.object(server.random, "uniform", return_value=31.5) as uniform:
            self.assertEqual(server._task_delay_seconds({}, 23.0, 40.0), 31.5)
        uniform.assert_called_once_with(23.0, 40.0)

    def test_rejects_invalid_task_delay(self) -> None:
        for value in (-1, True, "2", float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    server._task_delay_seconds({"delay_seconds": value}, 23.0, 40.0)


class TaskBehaviorTest(unittest.TestCase):
    def test_defaults_to_success(self) -> None:
        self.assertEqual(server._task_behavior({}), "success")
        self.assertFalse(server._should_fail_task("task-success", "success", ""))

    def test_rejects_unknown_behavior(self) -> None:
        with self.assertRaises(ValueError):
            server._task_behavior({"behavior": "sometimes"})

    def test_fail_once_is_shared_through_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            self.assertTrue(
                server._should_fail_task("task-retry", "fail_once", state_dir)
            )
            self.assertFalse(
                server._should_fail_task("task-retry", "fail_once", state_dir)
            )
            self.assertTrue(
                server._should_fail_task("task-other", "fail_once", state_dir)
            )

    def test_fail_always_never_succeeds(self) -> None:
        self.assertTrue(server._should_fail_task("task-1", "fail_always", ""))
        self.assertTrue(server._should_fail_task("task-1", "fail_always", ""))


if __name__ == "__main__":
    unittest.main()
