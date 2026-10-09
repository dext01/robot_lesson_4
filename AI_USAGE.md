# Использование ИИ

## ПР03

`ai_used: true`. ИИ-ассистент (LLM) использовался как помощник.

### Сам

- Разобрал задание, поднял Docker-контейнер с ROS 2 Lyrical,
  перенёс `turtle_bringup` из ПР02.
- Провёл опыт (сбой без remap, исправление через remap, замер hz).
  Все числа в отчётах — реальный stdout в `evidence/pr03/*.txt`.

### С ИИ

- Структура ноды `patrol.py`, выделение `choose_cmd`, юнит-тесты.
- Оформление `demo.md`, `report.json`, `README.md`, CI workflow.
- Проверка решения на соответствие заданию, исправление остановки
  ноды по Ctrl+C.

## ПР04

`ai_used: true`. ИИ-ассистент (LLM) использовался как помощник.

- **С ИИ:** параметры и их проверка в `patrol.py`, тесты, оформление
  `parameters.md`, `report.json`, README.
- **Проверка:** `python3 -m pytest src/patrol/test` и живой прогон
  `ros2 param set/get`, `ros2 topic hz`; вывод без правки — в
  `evidence/pr04/*.txt`. Опыт повторяется вживую на защите.
