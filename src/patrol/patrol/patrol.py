"""Patrol нода: подписка на /turtle1/pose и периодическая публикация Twist."""

from __future__ import annotations

import math

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.signals import SignalHandlerOptions
from turtlesim_msgs.msg import Pose

DEFAULTS = {
    'linear_speed': 0.5,
    'turn_rate': 0.3,
    'publish_hz': 10.0,
}

# Допустимые диапазоны (включительно).
LIMITS = {
    'linear_speed': (0.0, 1.0),
    'turn_rate': (-1.0, 1.0),
    'publish_hz': (1.0, 30.0),
}


def validate_param(name: str, value: object) -> str | None:
    """
    Проверить одно значение параметра.

    Возвращает None, если значение допустимо, иначе текст причины.
    Функция чистая: не трогает ноду и таймер.
    """
    if name not in LIMITS:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f'{name} must be a number, got {value!r}'
    if not math.isfinite(value):
        return f'{name} must be finite, got {value}'
    low, high = LIMITS[name]
    if not low <= value <= high:
        return f'{name} must be in [{low}, {high}], got {value}'
    return None


def choose_cmd(pose: Pose | None, linear_speed: float,
               turn_rate: float) -> Twist:
    """
    Выбрать Twist по последней позе.

    До первой позы возвращает нулевой Twist. При наличии позы —
    linear.x и angular.z из параметров.
    """
    cmd = Twist()
    if pose is None:
        return cmd
    cmd.linear.x = float(linear_speed)
    cmd.angular.z = float(turn_rate)
    return cmd


class PatrolNode(Node):
    """Хранит последнюю позу и периодически публикует Twist в cmd_vel."""

    def __init__(self) -> None:
        super().__init__('patrol')
        for name, value in DEFAULTS.items():
            self.declare_parameter(name, value)
            reason = validate_param(name, self.get_parameter(name).value)
            if reason is not None:
                raise ValueError(reason)
        self._linear_speed = float(self.get_parameter('linear_speed').value)
        self._turn_rate = float(self.get_parameter('turn_rate').value)
        self._publish_hz = float(self.get_parameter('publish_hz').value)

        self._last_pose: Pose | None = None
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10
        )
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(1.0 / self._publish_hz, self._on_timer)
        self.add_on_set_parameters_callback(self._on_set_parameters)
        self.get_logger().info(
            f'patrol started: linear_speed={self._linear_speed} '
            f'turn_rate={self._turn_rate} publish_hz={self._publish_hz}'
        )

    @property
    def timer_period(self) -> float:
        return self._timer.timer_period_ns / 1e9

    def _on_set_parameters(
        self, params: list[Parameter]
    ) -> SetParametersResult:
        # Сначала проверяем все значения, и только потом меняем состояние.
        for param in params:
            if param.name == 'publish_hz':
                continue  # ДЕФЕКТ ПР04: проверка частоты временно отключена
            reason = validate_param(param.name, param.value)
            if reason is not None:
                self.get_logger().warning(f'rejected: {reason}')
                return SetParametersResult(successful=False, reason=reason)

        for param in params:
            if param.name == 'linear_speed':
                self._linear_speed = float(param.value)
            elif param.name == 'turn_rate':
                self._turn_rate = float(param.value)
            elif param.name == 'publish_hz':
                self._restart_timer(float(param.value))
        return SetParametersResult(successful=True)

    def _restart_timer(self, publish_hz: float) -> None:
        old_timer = self._timer
        old_timer.cancel()
        self.destroy_timer(old_timer)
        self._timer = self.create_timer(1.0 / publish_hz, self._on_timer)
        self._publish_hz = publish_hz
        self.get_logger().info(
            f'publish_hz -> {publish_hz} (period {1.0 / publish_hz:.3f} s)'
        )

    def _on_pose(self, msg: Pose) -> None:
        self._last_pose = msg

    def _on_timer(self) -> None:
        cmd = choose_cmd(self._last_pose, self._linear_speed, self._turn_rate)
        self._cmd_pub.publish(cmd)

    def publish_stop(self) -> None:
        self._cmd_pub.publish(Twist())


def main(args: list[str] | None = None) -> None:
    # Без своего обработчика SIGINT rclpy не закрывает контекст до finally,
    # и финальный нулевой Twist успевает уйти.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
