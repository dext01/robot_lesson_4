"""Тесты параметров на живой ноде patrol (без turtlesim)."""

import math

from patrol.patrol import PatrolNode
import pytest
import rclpy
from rclpy.parameter import Parameter


@pytest.fixture
def node():
    rclpy.init()
    n = PatrolNode()
    yield n
    n.destroy_node()
    rclpy.try_shutdown()


def test_defaults(node: PatrolNode) -> None:
    assert node.get_parameter('linear_speed').value == 0.5
    assert node.get_parameter('turn_rate').value == 0.3
    assert node.get_parameter('publish_hz').value == 10.0
    assert node.timer_period == pytest.approx(0.1)


def test_publish_hz_10_to_5_recreates_timer(node: PatrolNode) -> None:
    old_timer = node._timer
    result = node.set_parameters([Parameter('publish_hz', value=5.0)])[0]
    assert result.successful
    assert node.get_parameter('publish_hz').value == 5.0
    assert node.timer_period == pytest.approx(0.2)
    assert node._timer is not old_timer
    assert len(list(node.timers)) == 1


@pytest.mark.parametrize('bad', [0.0, -5.0, math.nan])
def test_bad_publish_hz_rejected_and_state_kept(
    node: PatrolNode, bad: float
) -> None:
    old_timer = node._timer
    result = node.set_parameters([Parameter('publish_hz', value=bad)])[0]
    assert not result.successful
    assert node.get_parameter('publish_hz').value == 10.0
    assert node._timer is old_timer
    assert node.timer_period == pytest.approx(0.1)
    assert len(list(node.timers)) == 1


def test_speed_change_applies(node: PatrolNode) -> None:
    result = node.set_parameters([
        Parameter('linear_speed', value=0.8),
        Parameter('turn_rate', value=-0.5),
    ])
    assert all(r.successful for r in result)
    assert node._linear_speed == 0.8
    assert node._turn_rate == -0.5
