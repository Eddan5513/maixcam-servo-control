# 🤖 MaixCAM Advanced Servo Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![MaixPy](https://img.shields.io/badge/MaixPy-4.x-green.svg)](https://wiki.sipeed.com/maixpy/)

Продвинутое приложение для управления сервоприводом на основе детекции объектов, цветов и движения для MaixCAM.

![MaixCAM Servo Control](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-3900%2B-blue)
![Documentation](https://img.shields.io/badge/Documentation-Comprehensive-orange)

## 🚀 Возможности

### Режимы детекции
- **Color Detection** 🎨 - детекция по цвету с калибровкой
- **Object Detection** 🤖 - нейросетевая детекция объектов (YOLOv8)
- **Motion Detection** 🏃 - детекция движения

### Пресеты цветов
- Yellow, Red, Green, Blue, Orange, Purple, White, Black
- Custom - калибровка своего цвета через тачскрин

### Пресеты объектов
- person, car, dog, cat, bottle, cup, cell phone
- Поддержка всех 80 классов COCO dataset

### Настройки сервопривода
- **Выбор пина** - настраиваемый PWM пин (по умолчанию A18)
- **Углы** - настройка углов открытия/закрытия (по умолчанию 90°/0°)
- **Задержка закрытия** - время до автоматического закрытия (по умолчанию 10 сек)
- **Режим ARM** - автоматическое переключение в режим готовности после исчезновения объекта
- **Задержка реарма** - время ожидания перед повторной готовностью (по умолчанию 2 сек)
- **Повторное срабатывание** - опция повторного открытия каждые N секунд при обнаружении

### UI/OSD
- Статус сервопривода (OPEN/CLOSED)
- Статус готовности (ARMED/DISARMED)
- Текущий режим детекции
- Целевой объект/цвет
- FPS счетчик
- Таймеры обратного отсчета
- Визуализация детекций с bounding boxes

## 📋 Требования

- MaixCAM (первое поколение с экраном) 📷
- Сервопривод SG90 или аналогичный ⚙️
- MaixVision для загрузки кода 💻
- Предустановленная модель YOLOv8 (обычно `/root/models/yolov8n.mud`) 🤖

## 🔌 Подключение

```
Servo Signal -> A18 (или другой PWM пин)
Servo GND    -> GND
Servo Power  -> VBUS 5V
```

**Важно:** Убедитесь что источник питания обеспечивает достаточный ток для сервопривода.

## 🎮 Использование

### Запуск
1. Подключитесь к MaixCAM через MaixVision (IP: 10.144.30.1)
2. Загрузите `advanced_servo_app.py`
3. Запустите приложение

### Тестирование
```bash
# Тест сервопривода
python3 utils/servo_test.py

# Проверка PWM пинов
python3 utils/check_pwm_pins.py

# Калибровка цвета
python3 utils/calibrate_color.py
```

### Примеры
```bash
# Простая версия
python3 examples/simple_servo_app.py

# Детекция цвета
python3 examples/color_servo_app.py

# Полная версия
python3 advanced_servo_app.py
```

### Управление
- **TAP на экране** - открыть меню
- **В меню:**
  - Выбор режима детекции (Color/Object/Motion)
  - Выбор пресета цвета
  - Выбор целевого объекта
  - Калибровка цвета
  - ARM/DISARM
  - Сохранение настроек

### Калибровка цвета
1. Откройте меню
2. Выберите "Calibrate Color"
3. Коснитесь объекта нужного цвета на экране
4. Система автоматически создаст пороги в LAB пространстве

## ⚙️ Конфигурация

Настройки сохраняются в `/root/advanced_servo_config.json`:

```json
{
  "servo_pin": "A18",
  "pwm_id": 6,
  "servo_angle_open": 90,
  "servo_angle_close": 0,
  "close_delay": 10,
  "rearm_mode": true,
  "rearm_delay": 2,
  "repeat_trigger": false,
  "repeat_interval": 10,
  "detection_mode": "color",
  "color_preset": "Yellow",
  "object_preset": "person",
  "confidence_threshold": 0.5,
  "min_area": 500,
  "motion_sensitivity": 50
}
```

### Доступные PWM пины
Проверьте документацию MaixCAM для списка доступных PWM пинов. Обычно:
- A18, A19, A20, A21 и другие

## 🎯 Режимы работы

### Режим ARM
- **Включен (по умолчанию):** После исчезновения объекта система автоматически переходит в режим готовности через заданное время
- **Выключен:** Срабатывает один раз, требуется ручной реарм через меню

### Повторное срабатывание
- **Выключено (по умолчанию):** Открывает серву один раз при обнаружении
- **Включено:** Повторно открывает серву каждые N секунд пока объект виден

## 🔧 Оптимизация

### Производительность
- Разрешение камеры: 640x480 для баланса скорости/качества
- Целевой FPS: 30
- Оптимизированная обработка изображений
- Эффективное использование LAB цветового пространства

### Точность детекции
- **Color:** Широкие пороги с запасом для надежности
- **Object:** Настраиваемый порог уверенности (по умолчанию 0.5)
- **Motion:** Настраиваемая чувствительность

## 📁 Файлы проекта

- `advanced_servo_app.py` - основное приложение
- `color_servo_app.py` - простая версия с детекцией цвета
- `servo_detector_app.py` - версия с базовым меню
- `servo_test.py` - тест сервопривода
- `yellow_servo_control.py` - базовая версия для желтого цвета

## 🐛 Отладка

### Серва не двигается
1. Проверьте подключение к пину A18
2. Убедитесь что VBUS 5V обеспечивает достаточный ток
3. Запустите `servo_test.py` для проверки
4. Попробуйте другой PWM пин

### Плохая детекция цвета
1. Используйте калибровку через тачскрин
2. Обеспечьте хорошее освещение
3. Увеличьте пороги в конфиге

### Низкий FPS
1. Уменьшите разрешение камеры в конфиге
2. Используйте Color Detection вместо Object Detection
3. Увеличьте min_area для фильтрации мелких объектов

## 📝 Лицензия

MIT License

## 👨‍💻 Автор

Created for MaixCAM development

## 📖 Документация

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Быстрый старт за 5 минут
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Примеры использования и интеграции
- **[docs/TECHNICAL.md](docs/TECHNICAL.md)** - Техническая документация и оптимизация
- **[docs/config_examples.json](docs/config_examples.json)** - Готовые конфигурации
- **[CHANGELOG.md](CHANGELOG.md)** - История изменений

## 📂 Структура проекта

```
maixcam-servo-control/
├── advanced_servo_app.py      # Основное приложение
├── examples/                   # Примеры приложений
│   ├── simple_servo_app.py    # Упрощенная версия
│   ├── color_servo_app.py     # Детекция цвета
│   ├── servo_detector_app.py  # Мультирежимная версия
│   └── yellow_servo_control.py # Базовая версия
├── utils/                      # Утилиты
│   ├── servo_test.py          # Тест сервопривода
│   ├── check_pwm_pins.py      # Проверка PWM пинов
│   └── calibrate_color.py     # Калибровка цвета
├── docs/                       # Документация
│   ├── QUICKSTART.md          # Быстрый старт
│   ├── EXAMPLES.md            # Примеры
│   ├── TECHNICAL.md           # Техническая документация
│   ├── PROJECT_SUMMARY.md     # Обзор проекта
│   └── config_examples.json   # Примеры конфигов
├── README.md                   # Основная документация
├── CHANGELOG.md                # История изменений
└── LICENSE                     # MIT License
```

## 🔗 Ссылки

- [GitHub Repository](https://github.com/bobberdolle1/maixcam-servo-control)
- [MaixPy Documentation](https://wiki.sipeed.com/maixpy/)
- [MaixCAM Hardware](https://wiki.sipeed.com/hardware/en/maixcam/maixcam.html)
- [YOLOv8 on MaixPy](https://wiki.sipeed.com/maixpy/doc/en/vision/yolov5.html)
