# 🤖 MaixCAM Advanced Servo Control

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![MaixPy](https://img.shields.io/badge/MaixPy-4.x-green.svg)](https://wiki.sipeed.com/maixpy/)
[![Version](https://img.shields.io/badge/version-1.1.0-brightgreen.svg)](https://github.com/bobberdolle1/maixcam-servo-control/releases)
[![Stars](https://img.shields.io/github/stars/bobberdolle1/maixcam-servo-control?style=social)](https://github.com/bobberdolle1/maixcam-servo-control/stargazers)

**Advanced AI-powered servo control system for MaixCAM with YOLOv8 object detection, color tracking, and motion sensing**

[English](#english) | [Русский](#russian)

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-3900%2B-blue)
![Documentation](https://img.shields.io/badge/Documentation-Comprehensive-orange)

</div>

---

<a name="english"></a>
## 🌟 English

### 🎯 What is this?

A **production-ready**, **AI-powered** servo control system for MaixCAM that combines:
- 🎨 **Color Detection** - LAB color space with touchscreen calibration
- 🤖 **Object Detection** - YOLOv8 neural network (80 COCO classes)
- 🏃 **Motion Detection** - Real-time frame differencing
- 📱 **Touch UI** - Full-featured menu system with live settings
- ⚡ **High Performance** - 30 FPS @ 640x480, optimized algorithms
- 🎛️ **Flexible Control** - ARM mode, rearm logic, repeat triggers

Perfect for **robotics**, **automation**, **IoT projects**, **computer vision** applications, and **AI experiments**!

### ✨ Key Features

<table>
<tr>
<td width="50%">

#### 🎨 Detection Modes
- **Color Detection** with 8 presets
- **YOLOv8 Object Detection** (80 classes)
- **Motion Detection** with sensitivity control
- **Custom Color Calibration** via touchscreen

</td>
<td width="50%">

#### ⚙️ Servo Control
- **Configurable angles** (0-180°)
- **ARM/DISARM mode** for safety
- **Auto-rearm** with delay
- **Repeat trigger** mode
- **Multiple PWM pins** support

</td>
</tr>
<tr>
<td width="50%">

#### 📱 User Interface
- **Touchscreen menu** system
- **Real-time OSD** with status
- **Live settings** adjustment
- **FPS counter** and timers
- **Detection visualization**

</td>
<td width="50%">

#### 🚀 Performance
- **30 FPS** color detection
- **20 FPS** object detection
- **~30ms latency**
- **Optimized algorithms**
- **Multiple resolutions** (320x240 to 1280x720)

</td>
</tr>
</table>

### 📦 What's Included

```
📁 Project Structure
├── 🎯 advanced_servo_app.py    # Main application (full-featured)
├── 📂 examples/                 # Example applications
│   ├── simple_servo_app.py     # Minimal version for quick start
│   ├── color_servo_app.py      # Color detection example
│   └── ...                     # More examples
├── 🛠️ utils/                    # Utility scripts
│   ├── servo_test.py           # Hardware testing
│   ├── check_pwm_pins.py       # PWM pin checker
│   └── calibrate_color.py      # Color calibration tool
└── 📚 docs/                     # Comprehensive documentation
    ├── QUICKSTART.md           # 5-minute setup guide
    ├── EXAMPLES.md             # 10+ real-world use cases
    └── TECHNICAL.md            # Deep technical dive
```

### 🚀 Quick Start (5 minutes)

#### 1️⃣ Hardware Setup
```
Servo Signal (yellow) → A18 (PWM6)
Servo GND (brown)     → GND
Servo Power (red)     → VBUS 5V (2A recommended)
```

#### 2️⃣ Test Hardware
```bash
python3 utils/servo_test.py
python3 utils/check_pwm_pins.py
```

#### 3️⃣ Run Application
```bash
# Simple version
python3 examples/simple_servo_app.py

# Full version with UI
python3 advanced_servo_app.py
```

#### 4️⃣ Configure
- **Tap screen** to open menu
- Select **detection mode** (Color/Object/Motion)
- Choose **target** (color or object)
- Adjust **settings** (delays, thresholds, resolution)
- **Save** and enjoy!

### 🎯 Use Cases

<table>
<tr>
<td>🐾 <b>Pet Feeder</b><br/>Automatic feeding when pet detected</td>
<td>🎨 <b>Color Sorter</b><br/>Sort objects by color</td>
<td>🚨 <b>Security</b><br/>Motion-activated alerts</td>
</tr>
<tr>
<td>👥 <b>People Counter</b><br/>Count visitors/customers</td>
<td>🚪 <b>Auto Door</b><br/>Hands-free door opener</td>
<td>🎮 <b>Gesture Control</b><br/>Control devices with gestures</td>
</tr>
<tr>
<td>📸 <b>Wildlife Camera</b><br/>Trigger on animal detection</td>
<td>✅ <b>Quality Control</b><br/>Detect defects in production</td>
<td>🅿️ <b>Parking Monitor</b><br/>Track parking occupancy</td>
</tr>
</table>

### 📊 Performance Benchmarks

| Mode     | Resolution | FPS  | Latency | Use Case                    |
|----------|------------|------|---------|----------------------------|
| Color    | 640x480    | ~30  | ~30ms   | Fast color tracking        |
| Color    | 1280x720   | ~15  | ~60ms   | High-accuracy detection    |
| Object   | 640x480    | ~20  | ~50ms   | Real-time object detection |
| Motion   | 640x480    | ~30  | ~30ms   | Motion sensing             |

### 🛠️ Requirements

- **Hardware:** MaixCAM (1st gen with screen), SG90 servo (or compatible)
- **Software:** MaixPy 4.x, YOLOv8 model (`/root/models/yolov8n.mud`)
- **Power:** 5V 2A power supply recommended
- **Tools:** MaixVision IDE for deployment

### 📚 Documentation

- 📖 [**Quick Start Guide**](docs/QUICKSTART.md) - Get started in 5 minutes
- 💡 [**Examples & Use Cases**](docs/EXAMPLES.md) - 10+ real-world scenarios
- 🔧 [**Technical Documentation**](docs/TECHNICAL.md) - Deep dive & optimization
- 📝 [**Changelog**](CHANGELOG.md) - Version history

### 🤝 Contributing

Contributions welcome! Areas for improvement:
- Face detection mode
- QR code scanning
- Multi-servo support
- Web interface
- Mobile app control
- Cloud integration

### 📄 License

MIT License - See [LICENSE](LICENSE) file

### 🔗 Links

- **Repository:** https://github.com/bobberdolle1/maixcam-servo-control
- **Issues:** https://github.com/bobberdolle1/maixcam-servo-control/issues
- **MaixPy Docs:** https://wiki.sipeed.com/maixpy/

### 🏷️ Topics

`maixcam` `maix` `sipeed` `servo-control` `yolov8` `object-detection` `color-detection` `motion-detection` `computer-vision` `ai` `machine-learning` `robotics` `automation` `iot` `embedded` `python` `opencv` `neural-network` `real-time` `edge-ai` `tinyml` `maker` `diy` `raspberry-pi-alternative` `arduino-alternative` `esp32-cam-alternative`

---

<a name="russian"></a>
## 🌟 Русский

### 🎯 Что это?

**Готовая к использованию** система управления сервоприводом с **искусственным интеллектом** для MaixCAM:
- 🎨 **Детекция цвета** - LAB цветовое пространство с калибровкой
- 🤖 **Детекция объектов** - Нейросеть YOLOv8 (80 классов COCO)
- 🏃 **Детекция движения** - Анализ кадров в реальном времени
- 📱 **Сенсорный UI** - Полнофункциональное меню с настройками
- ⚡ **Высокая производительность** - 30 FPS @ 640x480
- 🎛️ **Гибкое управление** - Режим ARM, реарм, повторные срабатывания

Идеально для **робототехники**, **автоматизации**, **IoT проектов**, **компьютерного зрения** и **AI экспериментов**!

### ✨ Основные возможности

<table>
<tr>
<td width="50%">

#### 🎨 Режимы детекции
- **Детекция цвета** с 8 пресетами
- **YOLOv8 детекция объектов** (80 классов)
- **Детекция движения** с настройкой чувствительности
- **Калибровка цвета** через тачскрин

</td>
<td width="50%">

#### ⚙️ Управление сервой
- **Настраиваемые углы** (0-180°)
- **Режим ARM/DISARM** для безопасности
- **Авто-реарм** с задержкой
- **Режим повтора** срабатывания
- **Поддержка нескольких PWM** пинов

</td>
</tr>
<tr>
<td width="50%">

#### 📱 Интерфейс
- **Сенсорное меню**
- **OSD в реальном времени**
- **Настройки на лету**
- **Счетчик FPS** и таймеры
- **Визуализация детекций**

</td>
<td width="50%">

#### 🚀 Производительность
- **30 FPS** детекция цвета
- **20 FPS** детекция объектов
- **~30ms задержка**
- **Оптимизированные алгоритмы**
- **Несколько разрешений** (320x240 до 1280x720)

</td>
</tr>
</table>

### 📦 Что входит

```
📁 Структура проекта
├── 🎯 advanced_servo_app.py    # Основное приложение
├── 📂 examples/                 # Примеры приложений
│   ├── simple_servo_app.py     # Упрощенная версия
│   ├── color_servo_app.py      # Пример детекции цвета
│   └── ...                     # Другие примеры
├── 🛠️ utils/                    # Утилиты
│   ├── servo_test.py           # Тест оборудования
│   ├── check_pwm_pins.py       # Проверка PWM пинов
│   └── calibrate_color.py      # Калибровка цвета
└── 📚 docs/                     # Документация
    ├── QUICKSTART.md           # Быстрый старт
    ├── EXAMPLES.md             # Примеры использования
    └── TECHNICAL.md            # Техническая документация
```

### 🚀 Быстрый старт (5 минут)

#### 1️⃣ Подключение
```
Servo Signal (желтый) → A18 (PWM6)
Servo GND (коричневый) → GND
Servo Power (красный)  → VBUS 5V (рекомендуется 2A)
```

#### 2️⃣ Тест оборудования
```bash
python3 utils/servo_test.py
python3 utils/check_pwm_pins.py
```

#### 3️⃣ Запуск
```bash
# Простая версия
python3 examples/simple_servo_app.py

# Полная версия с UI
python3 advanced_servo_app.py
```

#### 4️⃣ Настройка
- **Коснитесь экрана** для открытия меню
- Выберите **режим детекции** (Цвет/Объект/Движение)
- Выберите **цель** (цвет или объект)
- Настройте **параметры** (задержки, пороги, разрешение)
- **Сохраните** и пользуйтесь!

### 🎯 Примеры использования

<table>
<tr>
<td>🐾 <b>Кормушка для питомцев</b><br/>Автоматическая кормушка</td>
<td>🎨 <b>Сортировщик</b><br/>Сортировка по цвету</td>
<td>🚨 <b>Безопасность</b><br/>Детектор движения</td>
</tr>
<tr>
<td>👥 <b>Счетчик людей</b><br/>Подсчет посетителей</td>
<td>🚪 <b>Авто-дверь</b><br/>Открывание без рук</td>
<td>🎮 <b>Жесты</b><br/>Управление жестами</td>
</tr>
<tr>
<td>📸 <b>Камера для животных</b><br/>Съемка дикой природы</td>
<td>✅ <b>Контроль качества</b><br/>Детекция дефектов</td>
<td>🅿️ <b>Парковка</b><br/>Мониторинг мест</td>
</tr>
</table>

### 📊 Производительность

| Режим    | Разрешение | FPS  | Задержка | Применение                 |
|----------|------------|------|----------|----------------------------|
| Цвет     | 640x480    | ~30  | ~30ms    | Быстрое отслеживание       |
| Цвет     | 1280x720   | ~15  | ~60ms    | Высокая точность           |
| Объект   | 640x480    | ~20  | ~50ms    | Детекция в реальном времени|
| Движение | 640x480    | ~30  | ~30ms    | Датчик движения            |

### 🛠️ Требования

- **Железо:** MaixCAM (1-го поколения с экраном), серва SG90 (или аналог)
- **ПО:** MaixPy 4.x, модель YOLOv8 (`/root/models/yolov8n.mud`)
- **Питание:** Блок питания 5V 2A (рекомендуется)
- **Инструменты:** MaixVision IDE для загрузки

### 📚 Документация

- 📖 [**Быстрый старт**](docs/QUICKSTART.md) - Начните за 5 минут
- 💡 [**Примеры**](docs/EXAMPLES.md) - 10+ реальных сценариев
- 🔧 [**Техническая документация**](docs/TECHNICAL.md) - Глубокое погружение
- 📝 [**История изменений**](CHANGELOG.md) - Версии и обновления

### 🤝 Участие в разработке

Приветствуются любые улучшения:
- Детекция лиц
- Сканирование QR кодов
- Поддержка нескольких серв
- Веб-интерфейс
- Мобильное приложение
- Облачная интеграция

### 📄 Лицензия

MIT License - См. файл [LICENSE](LICENSE)

### 🔗 Ссылки

- **Репозиторий:** https://github.com/bobberdolle1/maixcam-servo-control
- **Проблемы:** https://github.com/bobberdolle1/maixcam-servo-control/issues
- **Документация MaixPy:** https://wiki.sipeed.com/maixpy/

### 🏷️ Теги

`maixcam` `maix` `sipeed` `управление-сервой` `yolov8` `детекция-объектов` `детекция-цвета` `детекция-движения` `компьютерное-зрение` `искусственный-интеллект` `машинное-обучение` `робототехника` `автоматизация` `интернет-вещей` `встраиваемые-системы` `python` `opencv` `нейросеть` `реальное-время` `edge-ai` `tinyml` `мейкер` `diy`

---

<div align="center">

### ⭐ Star this project if you find it useful!

**Made with ❤️ for the maker community**

[⬆ Back to top](#-maixcam-advanced-servo-control)

</div>
