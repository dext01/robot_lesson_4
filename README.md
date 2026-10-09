# robot_lesson_4 — ПР04. Параметризуем движение

Практика ПР04 курса «Введение в ROS 2» (НГУ, ФИТ, осень 2026).
Нода `patrol` из ПР03 получила параметры `linear_speed`, `turn_rate`,
`publish_hz`. Их можно менять на работающей ноде через
`ros2 param set`; недопустимые значения отклоняются до изменения
таймера и состояния.

| Параметр | По умолчанию | Допустимо |
|---|---|---|
| `linear_speed` | 0.5 м/с | 0…1 |
| `turn_rate` | 0.3 рад/с | −1…1 |
| `publish_hz` | 10.0 Гц | 1…30 |

Все значения должны быть конечными числами (NaN и inf отклоняются).

## Структура

```
src/
├── turtle_bringup/              # launch turtlesim (из ПР02)
└── patrol/
    ├── patrol/patrol.py         # нода, validate_param, choose_cmd
    └── test/
        ├── test_choose_cmd.py   # чистые функции: 10→5, 0, −5, NaN, inf
        └── test_params_node.py  # живая нода: таймер, отклонение, состояние
evidence/pr04/
├── parameters.md                # команды, вывод, разбор стадий
├── tests.txt                    # pytest: 25 passed, 1 skipped
├── report.json
└── *.txt                        # сырой stdout опыта
AI_USAGE.md
```

Ветка `defect/pr04-no-hz-check` — коммит с отключённой проверкой
частоты (стадия «Сломать»).

## Как воспроизвести

Контейнер `pr04-local-demo` (`osrf/ros:lyrical-desktop-full`),
`ROS_DOMAIN_ID=16`:

```bash
source /opt/ros/lyrical/setup.bash
cd /work
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
python3 -m pytest src/patrol/test

# терминал A
ros2 launch turtle_bringup sim.launch.py
# терминал B
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
# терминал C
ros2 topic hz /turtle1/cmd_vel            # ≈ 10
ros2 param set /patrol publish_hz 5.0     # successful, hz ≈ 5
ros2 param set /patrol publish_hz 0.0     # failed, значение 5.0 сохранено
```

Подробности — [`evidence/pr04/parameters.md`](evidence/pr04/parameters.md).
