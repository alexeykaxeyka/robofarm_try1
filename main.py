# подключение необходимых библиотек для работы игры: pygame для графики, pygame_gui для интерфейса, sys и os для системных операций, time для таймеров
import pygame
import pygame_gui
import sys
import os
import time
import random

# инициализация pygame для запуска игрового движка
pygame.init()

# настройка размеров окна игры и создание экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ферма программиста")
clock = pygame.time.Clock()

# параметры тайлового поля: размер одного тайла 32x32 пикселя
TILE_SIZE = 32
GRID_WIDTH, GRID_HEIGHT = 16, 12  # увеличенное поле — 16x12 тайлов (512x384 пикс)

# --- ЗАГРУЗКА СПРАЙТОВ И ФОНА ---
try:
    sprite_harvester = pygame.image.load("sprite_harvester.png").convert_alpha()
    sprite_planter = pygame.image.load("sprite_planter.png").convert_alpha()

    # масштабируем спрайты роботов до нужного размера (30x30 пикселей)
    robot_sprite_size = 30
    sprite_harvester = pygame.transform.scale(sprite_harvester, (robot_sprite_size, robot_sprite_size))
    sprite_planter = pygame.transform.scale(sprite_planter, (robot_sprite_size, robot_sprite_size))

    # загружаем фоновое изображение (200x200)
    background_tile = pygame.image.load("background_tile.png").convert()
    # масштабируем до 200x200 на всякий случай
    background_tile = pygame.transform.scale(background_tile, (200, 200))

    # загружаем спрайт земли для клеток поля (32x32)
    ground_tile = pygame.image.load("ground_tile.png").convert_alpha()
    # масштабируем до размера тайла 32x32
    ground_tile = pygame.transform.scale(ground_tile, (TILE_SIZE, TILE_SIZE))

    # загружаем спрайт домика
    house_sprite = pygame.image.load("house_sprite.png").convert_alpha()
    # масштабируем до размера тайла 32x32
    house_sprite = pygame.transform.scale(house_sprite, (TILE_SIZE, TILE_SIZE))

    # === ВНЕДРЕНИЕ СПРАЙТОВ КУЛЬТУР ===
    # Загружаем три отдельные картинки
    img_potato = pygame.image.load("crop_potato.png").convert_alpha()
    img_carrot = pygame.image.load("crop_carrot.png").convert_alpha()
    img_wheat = pygame.image.load("crop_wheat.png").convert_alpha()

    # Масштабируем их под размер клетки
    crop_potato = pygame.transform.scale(img_potato, (TILE_SIZE, TILE_SIZE))
    crop_carrot = pygame.transform.scale(img_carrot, (TILE_SIZE, TILE_SIZE))
    crop_wheat = pygame.transform.scale(img_wheat, (TILE_SIZE, TILE_SIZE))

    # Создаем словарь для быстрого доступа по названию культуры
    crops_sprites = {
        "potato": crop_potato,
        "carrot": crop_carrot,
        "wheat": crop_wheat
    }

    # Заглушка для растущего растения (зеленый круг), чтобы было видно, что растет
    growing_plant = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(growing_plant, (100, 200, 100), (TILE_SIZE // 2, TILE_SIZE // 2), 8)
    # ==================================

except FileNotFoundError as e:
    print(f"⚠️ Ошибка: Файл не найден! Убедитесь, что картинки лежат в папке с игрой.")
    print(f"Детали: {e}")
    # Создаем запасные варианты (цветные квадраты), если файл не найден
    robot_sprite_size = 30
    sprite_harvester = pygame.Surface((robot_sprite_size, robot_sprite_size))
    sprite_harvester.fill((255, 0, 0))
    sprite_planter = pygame.Surface((robot_sprite_size, robot_sprite_size))
    sprite_planter.fill((0, 255, 0))
    background_tile = pygame.Surface((200, 200))
    background_tile.fill((100, 100, 100))
    ground_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
    ground_tile.fill((139, 69, 19))
    house_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
    house_sprite.fill((139, 69, 19))

    # Запасные квадраты для культур
    crop_potato = pygame.Surface((TILE_SIZE, TILE_SIZE));
    crop_potato.fill((180, 100, 50))
    crop_carrot = pygame.Surface((TILE_SIZE, TILE_SIZE));
    crop_carrot.fill((255, 100, 0))
    crop_wheat = pygame.Surface((TILE_SIZE, TILE_SIZE));
    crop_wheat.fill((255, 255, 0))

    crops_sprites = {"potato": crop_potato, "carrot": crop_carrot, "wheat": crop_wheat}
    growing_plant = pygame.Surface((TILE_SIZE, TILE_SIZE));
    growing_plant.fill((100, 200, 100))
# ---------------------------------

# начальные координаты игрока по центру экрана и скорость его перемещения (в пикселях в секунду)
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 300

# состояние каждого тайла поля: none — пусто, иначе словарь с типом растения и временем до созревания
farm_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# смещение для центрирования поля на экране
OFFSET_X = (WIDTH - GRID_WIDTH * TILE_SIZE) // 2
OFFSET_Y = (HEIGHT - GRID_HEIGHT * TILE_SIZE) // 2

# координаты домиков
HOUSE_1_X = GRID_WIDTH // 2
HOUSE_1_Y = 0
HOUSE_2_X = GRID_WIDTH - 1
HOUSE_2_Y = GRID_HEIGHT - 1

# позиции роботов
planter_x, planter_y = GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2  # посадчик
harvester_x, harvester_y = GRID_WIDTH // 2 + 2, GRID_HEIGHT // 2  # сборщик

# анимация для каждого робота
animating_planter = False
animation_planter_start_x = 0
animation_planter_start_y = 0
animation_planter_target_x = 0
animation_planter_target_y = 0
animation_planter_start_time = 0

animating_harvester = False
animation_harvester_start_x = 0
animation_harvester_start_y = 0
animation_harvester_target_x = 0
animation_harvester_target_y = 0
animation_harvester_start_time = 0

ANIMATION_DURATION = 2  # секунды (исправлено с 5 на 0.5 для более быстрой анимации)

# глобальная переменная для хранения очков игрока
player_score = 0

# инвентарь семян
seeds = {"wheat": 5, "carrot": 5, "potato": 5}

# флаг и ссылки на элементы редактора кода (открыт/закрыт)
code_editor_open = False
code_editor = None
current_robot = None  # "planter" или "harvester"

# загрузка пользовательской темы интерфейса из файла theme.json с обработкой возможной ошибки
theme_path = os.path.join(os.path.dirname(__file__), 'theme.json')
try:
    manager = pygame_gui.UIManager((WIDTH, HEIGHT), theme_path=theme_path)
except Exception as e:
    print(f"ошибка загрузки theme.json: {e}")
    manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# текущая сцена игры: главное меню, игровой процесс или настройки
current_screen = "main_menu"

# пути к файлам кода роботов
CODE_FILE_PLANTER = "robot_code_planter.py"
CODE_FILE_HARVESTER = "robot_code_harvester.py"


# загрузка кода робота из файла
def load_robot_code(robot_type):
    code_file = CODE_FILE_PLANTER if robot_type == "planter" else CODE_FILE_HARVESTER
    try:
        with open(code_file, "r", encoding="utf-8") as f:
            return f.read()
    except:
        if robot_type == "planter":
            return "class FarmerBot(BaseRobot):\n    def work(self):\n        self.move(1, 0)\n        self.plant('wheat')"
        else:
            return "class FarmerBot(BaseRobot):\n    def work(self):\n        self.move(-1, 0)\n        self.harvest()"


# сохранение кода робота в файл
def save_robot_code(code, robot_type):
    code_file = CODE_FILE_PLANTER if robot_type == "planter" else CODE_FILE_HARVESTER
    try:
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✅ код сохранён в {code_file}")
    except Exception as e:
        print("⚠️ не удалось сохранить код робота:", e)


# функция загрузки сохранённого счёта из файла при запуске игры
def load_score():
    global player_score
    try:
        with open("score.txt", "r") as f:
            player_score = int(f.read().strip())
        print(f"✅ очки загружены: {player_score}")
    except:
        player_score = 0


# функция сохранения текущего счёта в файл при выходе или возврате в меню
def save_score():
    try:
        with open("score.txt", "w") as f:
            f.write(str(player_score))
        save_inventory()
        save_game_state()
        print("✅ очки сохранены!")
    except Exception as e:
        print("⚠️ не удалось сохранить очки:", e)


# сохранение инвентаря
def save_inventory():
    try:
        with open("inventory.txt", "w") as f:
            f.write(f"{seeds['wheat']},{seeds['carrot']},{seeds['potato']}")
        print("✅ инвентарь сохранён")
    except Exception as e:
        print("⚠️ не удалось сохранить инвентарь:", e)


# загрузка инвентаря
def load_inventory():
    global seeds
    try:
        with open("inventory.txt", "r") as f:
            w, c, p = f.read().strip().split(',')
            seeds["wheat"] = int(w)
            seeds["carrot"] = int(c)
            seeds["potato"] = int(p)
        print(f"✅ инвентарь загружен: {seeds}")
    except:
        seeds = {"wheat": 5, "carrot": 5, "potato": 5}
        print("🆕 стартовый инвентарь")


def save_game_state():
    try:
        # сохраняем позиции роботов
        with open("robot_positions.txt", "w") as f:
            f.write(f"{planter_x},{planter_y},{harvester_x},{harvester_y}")

        # сохраняем состояние поля
        field_data = []
        for y in range(GRID_HEIGHT):
            row = []
            for x in range(GRID_WIDTH):
                cell = farm_grid[y][x]
                if cell is None:
                    row.append("0")
                else:
                    crop = cell.get("crop", "0")
                    ready = cell.get("ready_in", 0)
                    row.append(f"{crop}:{ready}")
            field_data.append(",".join(row))

        with open("field_state.txt", "w") as f:
            f.write("\n".join(field_data))

        print("✅ состояние игры сохранено")
    except Exception as e:
        print("⚠️ ошибка сохранения поля:", e)


def load_game_state():
    global planter_x, planter_y, harvester_x, harvester_y, farm_grid

    # загружаем позиции роботов
    try:
        with open("robot_positions.txt", "r") as f:
            data = f.read().strip().split(',')
            if len(data) == 4:
                planter_x = int(data[0])
                planter_y = int(data[1])
                harvester_x = int(data[2])
                harvester_y = int(data[3])
                print(
                    f"✅ позиции роботов загружены: посадчик=({planter_x},{planter_y}), сборщик=({harvester_x},{harvester_y})")
    except:
        planter_x, planter_y = GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2
        harvester_x, harvester_y = GRID_WIDTH // 2 + 2, GRID_HEIGHT // 2
        print("🆕 стартовые позиции роботов")

    # загружаем состояние поля
    try:
        with open("field_state.txt", "r") as f:
            lines = f.read().strip().split('\n')
            if len(lines) == GRID_HEIGHT:
                for y in range(GRID_HEIGHT):
                    cells = lines[y].split(',')
                    if len(cells) == GRID_WIDTH:
                        for x in range(GRID_WIDTH):
                            cell_data = cells[x]
                            if cell_data == "0":
                                farm_grid[y][x] = None
                            else:
                                parts = cell_data.split(':')
                                if len(parts) >= 2:
                                    crop = parts[0]
                                    ready = int(parts[1])
                                    farm_grid[y][x] = {"crop": crop, "ready_in": ready}
                print("✅ состояние поля загружено")
    except:
        farm_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        print("🆕 чистое поле")


load_score()
load_inventory()
load_game_state()


# базовый класс робота
class BaseRobot:
    def __init__(self, x, y):
        self.tile_x = x
        self.tile_y = y
        self.log = []


# робот-посадчик — только move и plant
class PlanterRobot(BaseRobot):
    def move(self, dx, dy):
        self.tile_x += dx
        self.tile_y += dy
        self.tile_x = max(0, min(GRID_WIDTH - 1, self.tile_x))
        self.tile_y = max(0, min(GRID_HEIGHT - 1, self.tile_y))
        print(f"[посадчик] переместился на ({dx}, {dy}) → ({self.tile_x}, {self.tile_y})")

    def plant(self, crop):
        global farm_grid, seeds
        if not (0 <= self.tile_x < GRID_WIDTH and 0 <= self.tile_y < GRID_HEIGHT):
            print("[посадчик] ошибка: вне поля!")
            return
        cell = farm_grid[self.tile_y][self.tile_x]
        if cell is not None:
            print("[посадчик] клетка занята!")
            return
        valid_crops = {"wheat", "carrot", "potato"}
        if crop not in valid_crops:
            print(f"[посадчик] неизвестная культура: {crop}. используй: wheat, carrot, potato")
            return
        if seeds[crop] <= 0:
            print(f"[посадчик] нет семян {crop}! зайди в домик за припасами.")
            return
        seeds[crop] -= 1
        farm_grid[self.tile_y][self.tile_x] = {"crop": crop, "ready_in": 25}
        print(f"[посадчик] посадил {crop} на ({self.tile_x}, {self.tile_y}). осталось: {seeds[crop]}")


# робот-сборщик — только move и harvest
class HarvesterRobot(BaseRobot):
    def move(self, dx, dy):
        self.tile_x += dx
        self.tile_y += dy
        self.tile_x = max(0, min(GRID_WIDTH - 1, self.tile_x))
        self.tile_y = max(0, min(GRID_HEIGHT - 1, self.tile_y))
        print(f"[сборщик] переместился на ({dx}, {dy}) → ({self.tile_x}, {self.tile_y})")

    def harvest(self):
        global farm_grid, player_score
        if not (0 <= self.tile_x < GRID_WIDTH and 0 <= self.tile_y < GRID_HEIGHT):
            print("[сборщик] ошибка: вне поля!")
            return
        cell = farm_grid[self.tile_y][self.tile_x]
        if cell is None:
            print("[сборщик] нечего собирать!")
            return
        if cell.get("ready_in", 0) > 0:
            print("[сборщик] урожай ещё не созрел!")
            return
        crop = cell["crop"]
        points = {"wheat": 10, "carrot": 15, "potato": 20}.get(crop, 5)
        player_score += points
        farm_grid[self.tile_y][self.tile_x] = None
        print(f"[сборщик] собрал {crop}! +{points} очков. всего: {player_score}")


# переменные для управления редактором кода (ссылки на ui-элементы)
run_button = None
close_button = None

# переменные для управления окном справочника
help_window_open = False
help_window = None

# домик фермера
house_open = False
house_window = None

# таймер для автоматического созревания растений каждую секунду
last_growth_update = time.time()
GROWTH_INTERVAL = 1.0

# глобальные ссылки на метки информации
score_label = None
wheat_label = None
carrot_label = None
potato_label = None


def open_house():
    global house_open, house_window
    if not house_open:
        house_window = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((WIDTH // 2 - 150, 100), (300, 250)),
            manager=manager,
            anchors={'center': 'center'}
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (280, 30)),
            text="🛒 Магазин семян",
            manager=manager,
            container=house_window
        )
        buy_wheat = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 50), (280, 30)),
            text="Пшеница (10 очков)",
            manager=manager,
            container=house_window
        )
        buy_carrot = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 90), (280, 30)),
            text="Морковь (15 очков)",
            manager=manager,
            container=house_window
        )
        buy_potato = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 130), (280, 30)),
            text="Картофель (20 очков)",
            manager=manager,
            container=house_window
        )
        house_open = True


def close_house():
    global house_open, house_window
    if house_open:
        house_window.kill()
        house_open = False


# создание элементов главного меню: заголовок и три кнопки
def create_main_menu():
    global title_label, play_button, quit_button
    title_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((WIDTH // 2 - 200, 50), (400, 60)),
        text="Ферма программиста",
        manager=manager,
        object_id="#title_label"
    )
    play_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WIDTH // 2 - 100, 200), (200, 50)),
        text="Играть",
        manager=manager
    )
    quit_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WIDTH // 2 - 100, 340), (200, 50)),
        text="Выход",
        manager=manager
    )


# создание элементов игрового экрана: кнопки возврата, справочника и отображения очков
def create_game_screen():
    global back_to_menu_button, help_button, score_label, wheat_label, carrot_label, potato_label
    back_to_menu_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((20, 20), (150, 40)),
        text="Вернуться в меню",
        manager=manager
    )
    help_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WIDTH - 170, 20), (150, 40)),
        text="Справочник",
        manager=manager
    )

    # Панель информации справа
    info_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((WIDTH - 220, 80), (200, 180)),
        manager=manager
    )

    # Метки внутри панели
    score_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 10), (180, 30)),
        text=f"Очки: {player_score}",
        manager=manager,
        container=info_panel
    )
    pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 50), (180, 30)),
        text="Семена:",
        manager=manager,
        container=info_panel
    )
    wheat_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((20, 80), (160, 25)),
        text=f"Пшеница: {seeds['wheat']}",
        manager=manager,
        container=info_panel
    )
    carrot_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((20, 105), (160, 25)),
        text=f"Морковь: {seeds['carrot']}",
        manager=manager,
        container=info_panel
    )
    potato_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((20, 130), (160, 25)),
        text=f"Картофель: {seeds['potato']}",
        manager=manager,
        container=info_panel
    )


# создание и открытие окна справочника с html-форматированным текстом api робота
def open_help_window():
    global help_window_open, help_window
    if not help_window_open:
        help_text = (
            "<b>Робот-посадчик</b>\n"
            "- self.move(dx, dy)\n"
            "- self.plant('wheat'/'carrot'/'potato')\n\n"
            "<b>Робот-сборщик</b>\n"
            "- self.move(dx, dy)\n"
            "- self.harvest()\n\n"
            "<b>Циклы:</b> for i in range(N)\n"
            "<b>Важно:</b> каждый робот видит только свои методы!"
        )

        help_window = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((100, 80), (600, 440)),
            manager=manager,
            anchors={'center': 'center'}
        )

        help_label = pygame_gui.elements.UITextBox(
            html_text=help_text,
            relative_rect=pygame.Rect((10, 10), (580, 380)),
            manager=manager,
            container=help_window,
        )
        help_window_open = True


# закрытие окна справочника и освобождение ресурсов
def close_help_window():
    global help_window_open, help_window
    if help_window_open:
        help_window.kill()
        help_window_open = False


# полная очистка всех ui-элементов при смене сцены
def clear_screen():
    global manager
    manager.clear_and_reset()


# инициализация главного меню при запуске
clear_screen()
create_main_menu()


# закрытие редактора кода и удаление его элементов из памяти
def close_code_editor():
    global code_editor_open, code_editor, run_button, close_button, current_robot
    if code_editor_open:
        code_editor.kill()
        run_button.kill()
        close_button.kill()
        code_editor = run_button = close_button = None
        code_editor_open = False
        current_robot = None


# функция получения текущей пиксельной позиции робота (с учётом анимации)
def get_robot_pixel_pos(robot_type):
    global animating_planter, animating_harvester

    current_time = time.time()

    if robot_type == "planter" and animating_planter:
        elapsed = current_time - animation_planter_start_time
        t = min(elapsed / ANIMATION_DURATION, 1.0)
        x = animation_planter_start_x + (animation_planter_target_x - animation_planter_start_x) * t
        y = animation_planter_start_y + (animation_planter_target_y - animation_planter_start_y) * t
        if t >= 1.0:
            animating_planter = False
        return x, y
    elif robot_type == "harvester" and animating_harvester:
        elapsed = current_time - animation_harvester_start_time
        t = min(elapsed / ANIMATION_DURATION, 1.0)
        x = animation_harvester_start_x + (animation_harvester_target_x - animation_harvester_start_x) * t
        y = animation_harvester_start_y + (animation_harvester_target_y - animation_harvester_start_y) * t
        if t >= 1.0:
            animating_harvester = False
        return x, y
    else:
        if robot_type == "planter":
            x = OFFSET_X + planter_x * TILE_SIZE + TILE_SIZE // 2
            y = OFFSET_Y + planter_y * TILE_SIZE + TILE_SIZE // 2
        else:
            x = OFFSET_X + harvester_x * TILE_SIZE + TILE_SIZE // 2
            y = OFFSET_Y + harvester_y * TILE_SIZE + TILE_SIZE // 2
        return x, y


# выполнение пользовательского кода в изолированном окружении с ограниченным набором функций
def execute_robot_code():
    global planter_x, planter_y, harvester_x, harvester_y, player_score, current_robot
    global animating_planter, animation_planter_start_x, animation_planter_start_y, animation_planter_target_x, animation_planter_target_y, animation_planter_start_time
    global animating_harvester, animation_harvester_start_x, animation_harvester_start_y, animation_harvester_target_x, animation_harvester_target_y, animation_harvester_start_time

    try:
        user_code = code_editor.get_text()
        save_robot_code(user_code, current_robot)

        safe_builtins = {
            'range': range,
            'len': len,
            'int': int,
            'str': str,
            'max': max,
            'min': min,
            '__build_class__': __build_class__,
            '__name__': '__main__',
        }
        safe_globals = {
            "__builtins__": safe_builtins,
            "BaseRobot": BaseRobot,
            "PlanterRobot": PlanterRobot,
            "HarvesterRobot": HarvesterRobot
        }
        local_vars = {}

        exec(user_code, safe_globals, local_vars)

        if "FarmerBot" not in local_vars:
            print("ошибка: класс 'FarmerBot' не найден.")
            return

        bot_class = local_vars["FarmerBot"]
        if current_robot == "planter" and not issubclass(bot_class, PlanterRobot):
            print("ошибка: посадчик должен наследоваться от PlanterRobot")
            return
        if current_robot == "harvester" and not issubclass(bot_class, HarvesterRobot):
            print("ошибка: сборщик должен наследоваться от HarvesterRobot")
            return

        # сохраняем начальную позицию для анимации
        if current_robot == "planter":
            start_x, start_y = planter_x, planter_y
        else:
            start_x, start_y = harvester_x, harvester_y

        # создаём робота с текущей позицией
        if current_robot == "planter":
            bot = bot_class(planter_x, planter_y)
        else:
            bot = bot_class(harvester_x, harvester_y)

        if not hasattr(bot, 'work'):
            print("ошибка: у FarmerBot нет метода 'work'.")
            return

        bot.work()

        # обновляем глобальные позиции
        if current_robot == "planter":
            planter_x, planter_y = bot.tile_x, bot.tile_y
            # запускаем анимацию
            animating_planter = True
            animation_planter_start_x = OFFSET_X + start_x * TILE_SIZE + TILE_SIZE // 2
            animation_planter_start_y = OFFSET_Y + start_y * TILE_SIZE + TILE_SIZE // 2
            animation_planter_target_x = OFFSET_X + planter_x * TILE_SIZE + TILE_SIZE // 2
            animation_planter_target_y = OFFSET_Y + planter_y * TILE_SIZE + TILE_SIZE // 2
            animation_planter_start_time = time.time()
        else:
            harvester_x, harvester_y = bot.tile_x, bot.tile_y
            # запускаем анимацию
            animating_harvester = True
            animation_harvester_start_x = OFFSET_X + start_x * TILE_SIZE + TILE_SIZE // 2
            animation_harvester_start_y = OFFSET_Y + start_y * TILE_SIZE + TILE_SIZE // 2
            animation_harvester_target_x = OFFSET_X + harvester_x * TILE_SIZE + TILE_SIZE // 2
            animation_harvester_target_y = OFFSET_Y + harvester_y * TILE_SIZE + TILE_SIZE // 2
            animation_harvester_start_time = time.time()

        print(f"✅ программа {current_robot} выполнена!")

    except Exception as e:
        print(f"ошибка выполнения кода: {e}")
        import traceback
        traceback.print_exc()


# открытие редактора кода с пустым шаблоном для пользователя
def open_code_editor(robot_type):
    global code_editor_open, code_editor, run_button, close_button, current_robot
    if not code_editor_open:
        current_robot = robot_type
        initial_code = load_robot_code(robot_type)
        code_editor = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect((100, 100), (600, 350)),
            initial_text=initial_code,
            manager=manager
        )
        run_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((100, 460), (150, 40)),
            text="Запустить",
            manager=manager
        )
        close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((260, 460), (150, 40)),
            text="Закрыть",
            manager=manager
        )
        code_editor_open = True


# основной игровой цикл: обработка событий, обновление логики, отрисовка
running = True
while running:
    time_delta = clock.tick(60) / 1000.0

    # автоматическое обновление состояния растений каждую секунду (уменьшение таймера созревания)
    current_time = time.time()
    if current_time - last_growth_update > GROWTH_INTERVAL:
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell = farm_grid[y][x]
                if cell and "ready_in" in cell:
                    cell["ready_in"] = max(0, cell["ready_in"] - 1)
        last_growth_update = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_score()
            running = False

        # управление игроком с помощью клавиш wasd или стрелок, если редактор закрыт
        if current_screen == "game" and not code_editor_open:
            keys = pygame.key.get_pressed()
            dt = time_delta
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                player_y -= player_speed * dt
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                player_y += player_speed * dt
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                player_x -= player_speed * dt
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                player_x += player_speed * dt

            # ограничение движения игрока в пределах экрана
            player_x = max(10, min(WIDTH - 30, player_x))
            player_y = max(10, min(HEIGHT - 30, player_y))

            # проверка входа в домик 1 (верхний центр)
            hx1 = OFFSET_X + HOUSE_1_X * TILE_SIZE + TILE_SIZE // 2
            hy1 = OFFSET_Y + HOUSE_1_Y * TILE_SIZE + TILE_SIZE // 2
            if ((player_x - hx1) ** 2 + (player_y - hy1) ** 2) ** 0.5 < 40 and not house_open:
                open_house()

        # обработка клика по роботам для открытия редактора кода
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and current_screen == "game"
                and not code_editor_open):
            mouse_x, mouse_y = event.pos

            # позиция посадчика
            px, py = get_robot_pixel_pos("planter")
            if abs(mouse_x - px) < 20 and abs(mouse_y - py) < 20:
                open_code_editor("planter")

            # позиция сборщика
            hx, hy = get_robot_pixel_pos("harvester")
            if ((mouse_x - hx) ** 2 + (mouse_y - hy) ** 2) ** 0.5 < 20:
                open_code_editor("harvester")

        # закрытие редактора или справочника по нажатию esc
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if code_editor_open:
                close_code_editor()
            elif help_window_open:
                close_help_window()
            elif house_open:
                close_house()

        # обработка нажатий на кнопки интерфейса
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if current_screen == "main_menu":
                if event.ui_element == play_button:
                    clear_screen()
                    create_game_screen()
                    current_screen = "game"
                elif event.ui_element == quit_button:
                    save_score()
                    running = False
            elif current_screen == "game":
                if event.ui_element == back_to_menu_button:
                    save_score()
                    clear_screen()
                    create_main_menu()
                    current_screen = "main_menu"
                elif event.ui_element == help_button:
                    open_help_window()

            if code_editor_open:
                if event.ui_element == run_button:
                    execute_robot_code()
                elif event.ui_element == close_button:
                    close_code_editor()

            if house_open:
                if "Пшеница" in event.ui_element.text and player_score >= 10:
                    player_score -= 10
                    seeds["wheat"] += 5
                elif "Морковь" in event.ui_element.text and player_score >= 15:
                    player_score -= 15
                    seeds["carrot"] += 5
                elif "Картофель" in event.ui_element.text and player_score >= 20:
                    player_score -= 20
                    seeds["potato"] += 5

        manager.process_events(event)

    manager.update(time_delta)

    # отрисовка игрового поля, игрока, растений и роботов
    if current_screen == "game":
        # === ОТРИСОВКА ФОНА (САМЫЙ ЗАДНИЙ ПЛАН) ===
        # Рисуем фон тайлами 4x3 (800/200 = 4, 600/200 = 3)
        for row in range(3):
            for col in range(4):
                x = col * 200
                y = row * 200
                screen.blit(background_tile, (x, y))
        # ===========================================

        pygame.draw.rect(screen, (255, 255, 255), (player_x, player_y, 20, 20))

        # === ОТРИСОВКА ПОЛЯ С НОВЫМИ СПРАЙТАМИ ЗЕМЛИ И РАСТЕНИЙ ===
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                px = OFFSET_X + x * TILE_SIZE
                py = OFFSET_Y + y * TILE_SIZE

                # Рисуем спрайт земли для каждой клетки
                screen.blit(ground_tile, (px, py))

                # Если в клетке есть растение, рисуем его поверх земли
                cell = farm_grid[y][x]
                if cell:
                    # Получаем тип культуры и статус зрелости
                    crop_type = cell.get("crop")
                    ready_time = cell.get("ready_in", 0)

                    if ready_time <= 0:
                        # Растение созрело: выбираем спрайт из словаря по типу культуры
                        plant_sprite_to_draw = crops_sprites.get(crop_type, crop_wheat)
                    else:
                        # Растение еще растет: рисуем заглушку (зеленый росток)
                        plant_sprite_to_draw = growing_plant

                    # Рисуем растение в центре клетки
                    screen.blit(plant_sprite_to_draw, (px, py))
        # ===================================================

        # === ОТРИСОВКА ДОМИКОВ (ТОЛЬКО СПРАЙТ, БЕЗ КВАДРАТОВ И ТРЕУГОЛЬНИКОВ) ===
        # Домик 1 (верхний центр)
        h1x = OFFSET_X + HOUSE_1_X * TILE_SIZE
        h1y = OFFSET_Y + HOUSE_1_Y * TILE_SIZE
        screen.blit(house_sprite, (h1x, h1y))

        # Домик 2 (нижний правый угол)
        h2x = OFFSET_X + HOUSE_2_X * TILE_SIZE
        h2y = OFFSET_Y + HOUSE_2_Y * TILE_SIZE
        screen.blit(house_sprite, (h2x, h2y))
        # ======================================================================

        # робот-посадчик с анимацией (спрайт)
        px, py = get_robot_pixel_pos("planter")
        screen.blit(sprite_planter, (px - robot_sprite_size // 2, py - robot_sprite_size // 2))

        # робот-сборщик с анимацией (спрайт)
        hx, hy = get_robot_pixel_pos("harvester")
        screen.blit(sprite_harvester, (hx - robot_sprite_size // 2, hy - robot_sprite_size // 2))
    else:
        screen.fill((20, 20, 20))

    # динамическое обновление текста счёта и инвентаря
    if current_screen == "game":
        if score_label:
            score_label.set_text(f"Очки: {player_score}")
        if wheat_label:
            wheat_label.set_text(f"Пшеница: {seeds['wheat']}")
        if carrot_label:
            carrot_label.set_text(f"Морковь: {seeds['carrot']}")
        if potato_label:
            potato_label.set_text(f"Картофель: {seeds['potato']}")

    # отрисовка всех ui-элементов поверх игровой сцены
    manager.draw_ui(screen)
    pygame.display.flip()

# корректное завершение работы pygame и программы
save_score()
save_game_state()
pygame.quit()
sys.exit()
