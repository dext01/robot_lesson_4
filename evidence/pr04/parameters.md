# ПР04. Параметры ноды patrol

Опыт поставлен 9 октября 2026 года в Docker-контейнере `pr04-local-demo`
(`osrf/ros:lyrical-desktop-full`, `ROS_DISTRO=lyrical`). Рабочая папка
`/work` — это `4_lesson` на хосте. Ниже реальные команды и их вывод,
полный stdout лежит в соседних `.txt`.

Тип позы:

```
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
```

## Параметры

| Параметр | По умолчанию | Допустимо |
|---|---|---|
| `linear_speed` | 0.5 м/с | конечное число 0…1 |
| `turn_rate` | 0.3 рад/с | конечное число −1…1 |
| `publish_hz` | 10.0 Гц | конечное число 1…30 |

Проверка — чистая функция `validate_param(name, value)` в
`src/patrol/patrol/patrol.py`. Колбэк `add_on_set_parameters_callback`
сначала проверяет **все** новые значения и только потом меняет
состояние. При допустимой смене `publish_hz` старый таймер
останавливается (`cancel` + `destroy_timer`), создаётся новый с периодом
`1 / publish_hz`. Таймер у ноды всегда один — это проверяет тест
`test_publish_hz_10_to_5_recreates_timer`.

## Стадия 1 · Собрать

```
$ ros2 launch turtle_bringup sim.launch.py
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
[INFO] [patrol]: patrol started: linear_speed=0.5 turn_rate=0.3 publish_hz=10.0

$ ros2 param list /patrol
  linear_speed
  publish_hz
  ...
  turn_rate
```

Скорости управляют командой ([`speed-params.txt`](speed-params.txt)):

```
$ ros2 topic echo /turtle1/cmd_vel --once     # linear.x: 0.5, angular.z: 0.3
$ ros2 param set /patrol linear_speed 0.8
Set parameter successful
$ ros2 param set /patrol turn_rate -0.5
Set parameter successful
$ ros2 topic echo /turtle1/cmd_vel --once     # linear.x: 0.8, angular.z: -0.5
$ ros2 param set /patrol linear_speed 1.5
Setting parameter failed: linear_speed must be in [0.0, 1.0], got 1.5
```

Частота управляет таймером, 10 → 5 Гц:

```
$ ros2 topic hz /turtle1/cmd_vel --window 30          # hz-10.txt
average rate: 10.002
$ ros2 param set /patrol publish_hz 5.0              # param-set-5.txt
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ ros2 topic hz /turtle1/cmd_vel --window 15          # hz-5.txt
average rate: 5.000
```

Лог ноды: `publish_hz -> 5.0 (period 0.200 s)`.

## Стадия 2 · Сломать

Ветка `defect/pr04-no-hz-check`, коммит `7d1a798`: в колбэке пропущена
проверка `publish_hz`. Передаём 0:

```
$ ros2 node list                                      # defect-nodes-before.txt
/patrol
/turtlesim
$ ros2 topic hz /turtle1/cmd_vel                      # defect-hz-before.txt
average rate: 10.001
$ timeout 10 ros2 param set /patrol publish_hz 0.0    # defect-param-set-0.txt
exit code: 124      ← ответа нет: нода упала, не ответив на запрос
```

Лог ноды ([`defect-patrol-log.txt`](defect-patrol-log.txt)):

```
  File "/work/build/patrol/patrol/patrol.py", line 119, in _restart_timer
    self._timer = self.create_timer(1.0 / publish_hz, self._on_timer)
ZeroDivisionError: division by zero
[ros2run]: Process exited with failure 1
```

После этого `/patrol` пропал из `ros2 node list`
([`defect-nodes-after.txt`](defect-nodes-after.txt): только `/turtlesim`),
`ros2 topic hz` больше ничего не получает. Старый таймер к моменту
деления уже уничтожен, поэтому даже без падения процесса нода осталась бы
без таймера — активное состояние разрушено.

Тот же тест, что потом подтверждает исправление
([`defect-tests.txt`](defect-tests.txt)):

```
FAILED test_params_node.py::test_bad_publish_hz_rejected_and_state_kept[0.0]
FAILED test_params_node.py::test_bad_publish_hz_rejected_and_state_kept[-5.0]
FAILED test_params_node.py::test_bad_publish_hz_rejected_and_state_kept[nan]
3 failed, 3 passed
```

## Стадия 3 · Доказать

Проверка возвращена (ветка `main`). Нода работает на 5 Гц после шага
10 → 5, затем передаём недопустимые значения:

```
$ ros2 param set /patrol publish_hz 0.0               # param-set-0.txt
Setting parameter failed: publish_hz must be in [1.0, 30.0], got 0.0
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ ros2 param set /patrol publish_hz -5.0              # param-set-negative.txt
Setting parameter failed: publish_hz must be in [1.0, 30.0], got -5.0
$ ros2 param set /patrol publish_hz .nan              # param-set-nan.txt
Setting parameter failed: publish_hz must be finite, got nan
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ ros2 topic hz /turtle1/cmd_vel --window 15          # hz-after-0.txt
average rate: 5.001
$ ros2 node list                                      # nodes-after.txt
/patrol
/turtlesim
```

Значение и поток остались прежними, нода жива. Тот же тест
([`tests.txt`](tests.txt)):

```
$ python3 -m pytest src/patrol/test
25 passed, 1 skipped
```

Тесты чистой функции `validate_param`: 10 → 5 допустимо; 0, −5, NaN,
inf, 31 отклоняются; границы скоростей включительно.

## Сервис и действие

```
$ ros2 service type /clear
std_srvs/srv/Empty
$ ros2 service call /clear std_srvs/srv/Empty
requester: making request: std_srvs.srv.Empty_Request()
response:
std_srvs.srv.Empty_Response()

$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]
```

Запрос сервиса (`/clear`) — короткий вызов: клиент отправляет запрос и
один раз получает ответ, промежуточного состояния нет. Цель действия
(`/turtle1/rotate_absolute`) — долгая задача: сервер принимает цель,
по ходу присылает feedback (оставшийся угол), в конце — результат, и
цель можно отменить до завершения.
