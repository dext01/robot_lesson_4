"""Тесты чистых функций choose_cmd и validate_param."""

import math

from patrol.patrol import choose_cmd, validate_param
import pytest
from turtlesim_msgs.msg import Pose


def test_no_pose_returns_zero_twist() -> None:
    cmd = choose_cmd(None, 0.5, 0.3)
    assert cmd.linear.x == 0.0
    assert cmd.angular.z == 0.0


def test_pose_uses_parameter_values() -> None:
    cmd = choose_cmd(Pose(), 0.8, -0.4)
    assert cmd.linear.x == 0.8
    assert cmd.angular.z == -0.4
    assert cmd.linear.y == 0.0


def test_publish_hz_10_to_5_is_valid() -> None:
    assert validate_param('publish_hz', 10.0) is None
    assert validate_param('publish_hz', 5.0) is None


@pytest.mark.parametrize('bad', [0.0, -5.0, math.nan, math.inf, 31.0])
def test_publish_hz_rejected(bad: float) -> None:
    assert validate_param('publish_hz', bad) is not None


@pytest.mark.parametrize('name, bad', [
    ('linear_speed', -0.1),
    ('linear_speed', 1.5),
    ('linear_speed', math.nan),
    ('turn_rate', 1.1),
    ('turn_rate', -1.1),
    ('turn_rate', math.inf),
])
def test_speed_limits(name: str, bad: float) -> None:
    assert validate_param(name, bad) is not None


def test_speed_bounds_inclusive() -> None:
    assert validate_param('linear_speed', 0.0) is None
    assert validate_param('linear_speed', 1.0) is None
    assert validate_param('turn_rate', -1.0) is None
    assert validate_param('turn_rate', 1.0) is None
