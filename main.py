# подключение необходимых библиотек для работы игры: pygame для графики, pygame_gui для интерфейса, sys и os для системных операций, time для таймеров
import pygame
import pygame_gui
import sys
import os
import time

# инициализация pygame для запуска игрового движка
pygame.init()

# настройка размеров окна игры и создание экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ферма программиста")
clock = pygame.time.Clock()

# начальные координаты игрока по центру экрана и скорость его перемещения (в пикселях в секунду)
player_x = WIDTH // 2
player_y = HEIGHT // 2
player_speed = 300

# параметры тайлового поля: размер одного тайла 32x32 пикселя
TILE_SIZE = 32
GRID_WIDTH, GRID_HEIGHT = 16, 12  # увеличенное поле — 16x12 тайлов (512x384 пикс)
# состояние каждого тайла поля: none — пусто, иначе словарь с типом растения и временем до созревания
farm_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

# смещение для центрирования поля на экране
OFFSET_X = (WIDTH - GRID_WIDTH * TILE_SIZE) // 2
OFFSET_Y = (HEIGHT - GRID_HEIGHT * TILE_SIZE) // 2

# координаты домика (в тайлах — сверху по центру)
HOUSE_TILE_X = GRID_WIDTH // 2
HOUSE_TILE_Y = 0
HOUSE_PX = OFFSET_X + HOUSE_TILE_X * TILE_SIZE + TILE_SIZE // 2
HOUSE_PY = OFFSET_Y + HOUSE_TILE_Y * TILE_SIZE + TILE_SIZE // 2

# начальная позиция робота в тайловых координатах (по центру поля)
robot_tile_x, robot_tile_y = GRID_WIDTH // 2, GRID_HEIGHT // 2

# анимация перемещения робота
animating = False
animation_start_x = 0
animation_start_y = 0
animation_target_x = 0
animation_target_y = 0
animation_start_time = 0
ANIMATION_DURATION = 2  # секунды

robot_size = 30


# функция получения текущей пиксельной позиции робота (с учётом анимации)
def get_robot_pixel_pos():
    global animating
    if animating:
        # рассчитываем текущую позицию робота во время анимации перемещения
        elapsed = time.time() - animation_start_time
        t = min(elapsed / ANIMATION_DURATION, 1.0)
        current_x = animation_start_x + (animation_target_x - animation_start_x) * t
        current_y = animation_start_y + (animation_target_y - animation_start_y) * t
        if t >= 1.0:
            animating = False
        return current_x, current_y
    else:
        # робот стоит на месте — возвращаем пиксельную позицию по текущим тайловым координатам
        x = OFFSET_X + robot_tile_x * TILE_SIZE + TILE_SIZE // 2
        y = OFFSET_Y + robot_tile_y * TILE_SIZE + TILE_SIZE // 2
        return x, y


# глобальная переменная для хранения очков игрока
player_score = 0

# инвентарь семян
seeds = {"wheat": 5, "carrot": 5, "potato": 5}

# переменные для хранения программы робота и истории его действий (пока не используются активно)
robot_program = None
robot_history = []

# флаг и ссылки на элементы редактора кода (открыт/закрыт)
code_editor_open = False
code_editor = None

# загрузка пользовательской темы интерфейса из файла theme.json с обработкой возможной ошибки
theme_path = os.path.join(os.path.dirname(__file__), 'theme.json')
try:
    manager = pygame_gui.UIManager((WIDTH, HEIGHT), theme_path=theme_path)
except Exception as e:
    print(f"ошибка загрузки theme.json: {e}")
    manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# текущая сцена игры: главное меню, игровой процесс или настройки
current_screen = "main_menu"

# путь к файлу с кодом робота
CODE_FILE = "robot_code.py"


# загрузка кода робота из файла
def load_robot_code():
    try:
        with open(CODE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "class FarmerBot(BaseRobot):\n    def work(self):\n        pass"


# сохранение кода робота в файл
def save_robot_code(code):
    try:
        with open(CODE_FILE, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ код робота сохранён в robot_code.py")
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
        print("✅ очки сохранены!")
    except Exception as e:
        print("⚠️ не удалось сохранить очки     :", e)


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


load_score()
load_inventory()


# базовый класс робота, от которого должны наследоваться все пользовательские программы
class BaseRobot:
    def __init__(self):
        self.tile_x = robot_tile_x
        self.tile_y = robot_tile_y
        self.log = []

    # метод перемещения робота на dx тайлов по горизонтали и dy по вертикали с проверкой границ поля
    def move(self, dx, dy):
        self.tile_x += dx
        self.tile_y += dy
        self.tile_x = max(0, min(GRID_WIDTH - 1, self.tile_x))
        self.tile_y = max(0, min(GRID_HEIGHT - 1, self.tile_y))
        self.log.append(f"move({dx}, {dy}) → ({self.tile_x}, {self.tile_y})")
        print(f"[robot] переместился на ({dx}, {dy}) → тайл ({self.tile_x}, {self.tile_y})")

    # метод посадки растения в текущей клетке с проверкой занятости и допустимых типов культур
    def plant(self, crop):
        global farm_grid, seeds
        if not (0 <= self.tile_x < GRID_WIDTH and 0 <= self.tile_y < GRID_HEIGHT):
            print("[robot] ошибка: вне поля!")
            return
        cell = farm_grid[self.tile_y][self.tile_x]
        if cell is not None:
            print("[robot] клетка занята!")
            return
        valid_crops = {"wheat", "carrot", "potato"}
        if crop not in valid_crops:
            print(f"[robot] неизвестная культура: {crop}. используй: wheat, carrot, potato")
            return
        if seeds[crop] <= 0:
            print(f"[robot] нет семян {crop}! зайди в домик за припасами.")
            return
        seeds[crop] -= 1
        farm_grid[self.tile_y][self.tile_x] = {"crop": crop, "ready_in": 25}
        self.log.append(f"plant({crop})")
        print(f"[robot] посадил {crop} на ({self.tile_x}, {self.tile_y}). осталось: {seeds[crop]}")

    # метод сбора урожая, если он созрел; добавляет очки игроку и очищает клетку
    def harvest(self):
        global farm_grid, player_score
        if not (0 <= self.tile_x < GRID_WIDTH and 0 <= self.tile_y < GRID_HEIGHT):
            print("[robot] ошибка: вне поля!")
            return
        cell = farm_grid[self.tile_y][self.tile_x]
        if cell is None:
            print("[robot] нечего собирать!")
            return
        if cell.get("ready_in", 0) > 0:
            print("[robot] урожай ещё не созрел!")
            return
        crop = cell["crop"]
        points = {"wheat": 10, "carrot": 15, "potato": 20}.get(crop, 5)
        player_score += points
        farm_grid[self.tile_y][self.tile_x] = None
        self.log.append(f"harvest() → +{points}")
        print(f"[robot] собрал {crop}! +{points} очков. всего: {player_score}")


# переменные для управления редактором кода (ссылки на ui-элементы)
code_editor = None
run_button = None
close_button = None
code_editor_open = False

# переменные для управления окном справочника
help_window_open = False
help_window = None

# домик фермера
house_open = False
house_window = None
buy_wheat_button = None
buy_carrot_button = None
buy_potato_button = None

# таймер для автоматического созревания растений каждую секунду
last_growth_update = time.time()
GROWTH_INTERVAL = 1.0

# глобальные ссылки на метки информации
score_label = None
wheat_label = None
carrot_label = None
potato_label = None


def open_house():
    global house_open, house_window, buy_wheat_button, buy_carrot_button, buy_potato_button
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
        buy_wheat_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 50), (280, 30)),
            text="Пшеница (10 очков)",
            manager=manager,
            container=house_window
        )
        buy_carrot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 90), (280, 30)),
            text="Морковь (15 очков)",
            manager=manager,
            container=house_window
        )
        buy_potato_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 130), (280, 30)),
            text="Картофель (20 очков)",
            manager=manager,
            container=house_window
        )
        house_open = True


def close_house():
    global house_open, house_window, buy_wheat_button, buy_carrot_button, buy_potato_button
    if house_open:
        house_window.kill()
        house_open = False


# создание элементов главного меню: заголовок и три кнопки
def create_main_menu():
    global title_label, play_button, settings_button, quit_button
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
    settings_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WIDTH // 2 - 100, 270), (200, 50)),
        text="Настройки",
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
            "<b>Справочник по API робота</b>\n\n"
            "<b>class FarmerBot(BaseRobot):</b>\n"
            "Все программы должны наследоваться от BaseRobot.\n\n"

            "<b>self.move(dx, dy)</b>\n"
            "Перемещает робота на dx тайлов вправо и dy тайлов вниз.\n"
            "Пример: self.move(1, 0) → вправо на 1 тайл.\n\n"

            "<b>self.plant(crop)</b>\n"
            "Сажает растение на текущей клетке. Доступно: 'wheat', 'carrot', 'potato'.\n\n"

            "<b>self.harvest()</b>\n"
            "Собирает урожай, если он созрел. Приносит очки!\n\n"

            "<b>Циклы</b>\n"
            "Можно использовать: <b>for i in range(N):</b>\n"
            "Пример: for i in range(3): self.move(1, 0)\n\n"

            "<b>Правила:</b>\n"
            "- Все команды пишутся внутри метода <b>work(self)</b>.\n"
            "- Нельзя использовать import, open, exec, eval и другие опасные команды.\n"
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
    global code_editor_open, code_editor, run_button, close_button
    if code_editor_open:
        code_editor.kill()
        run_button.kill()
        close_button.kill()
        code_editor = run_button = close_button = None
        code_editor_open = False


# выполнение пользовательского кода в изолированном окружении с ограниченным набором функций
def execute_robot_code():
    global robot_program, robot_tile_x, robot_tile_y, player_score, animating, animation_start_x, animation_start_y, animation_target_x, animation_target_y, animation_start_time
    try:
        user_code = code_editor.get_text()
        save_robot_code(user_code)  # СОХРАНЯЕМ КОД В ФАЙЛ!
        # разрешенные функции
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
            "BaseRobot": BaseRobot
        }
        local_vars = {}

        exec(user_code, safe_globals, local_vars)

        if "FarmerBot" not in local_vars:
            print("ошибка: класс 'FarmerBot' не найден.")
            return

        bot_class = local_vars["FarmerBot"]
        if not isinstance(bot_class, type) or not issubclass(bot_class, BaseRobot):
            print("ошибка: FarmerBot должен наследоваться от BaseRobot.")
            return

        # Сохраняем исходную позицию для анимации
        start_tile_x, start_tile_y = robot_tile_x, robot_tile_y

        robot_program = bot_class()
        if not hasattr(robot_program, 'work'):
            print("ошибка: у FarmerBot нет метода 'work'.")
            return

        robot_program.work()

        # Обновляем целевую позицию
        robot_tile_x = robot_program.tile_x
        robot_tile_y = robot_program.tile_y

        # Запускаем анимацию
        animating = True
        animation_start_x = OFFSET_X + start_tile_x * TILE_SIZE + TILE_SIZE // 2
        animation_start_y = OFFSET_Y + start_tile_y * TILE_SIZE + TILE_SIZE // 2
        animation_target_x = OFFSET_X + robot_tile_x * TILE_SIZE + TILE_SIZE // 2
        animation_target_y = OFFSET_Y + robot_tile_y * TILE_SIZE + TILE_SIZE // 2
        animation_start_time = time.time()

        print("программа робота успешно выполнена! анимация запущена.")

    except Exception as e:
        print(f"ошибка выполнения кода: {e}")
        import traceback
        traceback.print_exc()


# открытие редактора кода с пустым шаблоном для пользователя
def open_code_editor():
    global code_editor_open, code_editor, run_button, close_button
    if not code_editor_open:
        initial_code = load_robot_code()  # ← ЗАГРУЖАЕМ КОД ИЗ ФАЙЛА!
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

            # проверка входа в домик
            distance_to_house = ((player_x - HOUSE_PX) ** 2 + (player_y - HOUSE_PY) ** 2) ** 0.5
            if distance_to_house < 40 and not house_open:
                open_house()

        # обработка клика по роботу для открытия редактора кода
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and current_screen == "game"
                and not code_editor_open):
            robot_x, robot_y = get_robot_pixel_pos()
            mouse_x, mouse_y = event.pos
            if (robot_x - robot_size // 2 <= mouse_x <= robot_x + robot_size // 2 and
                    robot_y - robot_size // 2 <= mouse_y <= robot_y + robot_size // 2):
                open_code_editor()

        # закрытие редактора или справочника по нажатию esc
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if code_editor_open:
                close_code_editor()
            elif help_window_open:
                close_help_window()
            elif house_open:
                close_house()

        # обработка нажатий на кнопки интерфейса: переходы между экранами и действия в редакторе
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
                if event.ui_element == buy_wheat_button:
                    if player_score >= 10:
                        player_score -= 10
                        seeds["wheat"] += 5
                        print("куплено 5 пшеницы")
                elif event.ui_element == buy_carrot_button:
                    if player_score >= 15:
                        player_score -= 15
                        seeds["carrot"] += 5
                        print("куплено 5 моркови")
                elif event.ui_element == buy_potato_button:
                    if player_score >= 20:
                        player_score -= 20
                        seeds["potato"] += 5
                        print("куплено 5 картофеля")

        manager.process_events(event)

    manager.update(time_delta)

    # отрисовка игрового поля, игрока, растений и робота только на игровом экране
    if current_screen == "game":
        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (255, 255, 255), (player_x, player_y, 20, 20))
        # отрисовка поля с центрированием и сеткой
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                px = OFFSET_X + x * TILE_SIZE
                py = OFFSET_Y + y * TILE_SIZE
                cell = farm_grid[y][x]
                if cell:
                    color = (100, 200, 100) if cell["ready_in"] <= 0 else (150, 150, 50)
                    pygame.draw.rect(screen, color, (px, py, TILE_SIZE, TILE_SIZE))
                # тонкая серая сетка для удобства
                pygame.draw.rect(screen, (50, 50, 50), (px, py, TILE_SIZE, TILE_SIZE), 1)
        # домик фермера
        pygame.draw.rect(screen, (139, 69, 19), (HOUSE_PX - 15, HOUSE_PY - 15, 30, 30))  # коричневый дом
        pygame.draw.polygon(screen, (220, 20, 60), [
            (HOUSE_PX - 25, HOUSE_PY - 15),
            (HOUSE_PX + 25, HOUSE_PY - 15),
            (HOUSE_PX, HOUSE_PY - 40)
        ])  # красная крыша
        # робот с анимацией
        robot_x, robot_y = get_robot_pixel_pos()
        robot_points = [
            (robot_x, robot_y - robot_size // 2),
            (robot_x - robot_size // 2, robot_y + robot_size // 2),
            (robot_x + robot_size // 2, robot_y + robot_size // 2)
        ]
        pygame.draw.polygon(screen, (255, 255, 255), robot_points)
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
pygame.quit()
sys.exit()