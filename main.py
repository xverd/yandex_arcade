import arcade
import math
import random
import enum

# Константы
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "The Path to Emptiness"

main_sound = arcade.load_sound('sound/glavn_game.mp3', streaming=True)
level_sound = arcade.load_sound("sound/sound_game.mp3", streaming=True)

PLAYER_SPEED = 5
SPRITE_SCALING = 0.5
BULLET_SPEED = 7
GRAVITY = 1.0
PLAYER_JUMP_SPEED = 18

SETTINGS = {
    "brightness": 1.0,  # 0.5 — 1.5
    "filter": "NONE"  # NONE / DARK / COLD / WARM
}


class FaceDirection(enum.Enum):  # класс для направления взгляда персонажа
    LEFT = 0
    RIGHT = 1


class Player(arcade.Sprite):
    def __init__(self, scale=SPRITE_SCALING):
        super().__init__()
        self.scale = scale
        self.idle_texture = arcade.load_texture(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png")  # текстура
        self.texture = self.idle_texture
        # Ходьба
        self.walk_textures = []
        for i in range(8):
            tex_path = f":resources:images/animated_characters/female_person/femalePerson_walk{i}.png"
            self.walk_textures.append(arcade.load_texture(tex_path))
        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1
        self.is_walking = False
        self.face_direction = FaceDirection.RIGHT

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.walk_textures[self.current_texture]
                else:
                    self.texture = self.walk_textures[self.current_texture].flip_horizontally()
        else:
            self.texture = self.idle_texture if self.face_direction == FaceDirection.RIGHT else self.idle_texture.flip_horizontally()


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, speed=BULLET_SPEED, scale=1):
        super().__init__()
        self.texture = arcade.load_texture(":resources:images/space_shooter/laserBlue01.png")
        self.scale = scale
        self.center_x = start_x
        self.center_y = start_y

        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.angle = math.degrees(-angle)

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y
        # Удаление за экраном делается в LevelView с учётом камеры


class PostEffectMixin:  # Эфекты и яркость
    def draw_post_effects(self):
        brightness = SETTINGS["brightness"]
        filter_mode = SETTINGS["filter"]
        if brightness < 1.0:
            alpha = int((1.0 - brightness) * 220)
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, alpha))
        if filter_mode == "COLD":
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (80, 140, 255, 70))
        elif filter_mode == "WARM":
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (255, 160, 80, 70))
        elif filter_mode == "DARK":
            arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 120))


class LevelView(arcade.View, PostEffectMixin):
    def __init__(self, level_num):
        super().__init__()
        self.level_num = level_num
        self.game_ = arcade.play_sound(level_sound, volume=1, loop=True)

        # Игровые объекты
        self.player_sprite = None
        self.player_list = None
        self.wall_list = None
        self.door_list = None
        self.enemy_list = None
        self.player_bullet_list = None
        self.enemy_bullet_list = None
        self.key_list = None
        self.has_key = False
        self.lives = 3
        self.physics_engine = None

        # Камера 
        self.camera_sprites = arcade.Camera2D()
        self.camera_gui = arcade.Camera2D()

        # HUD: иконка ключа
        self.key_hud_list = arcade.SpriteList()
        self.key_hud_sprite = arcade.Sprite(":resources:images/items/keyYellow.png", 0.4)
        self.key_hud_sprite.position = (40, SCREEN_HEIGHT - 50)
        self.key_hud_list.append(self.key_hud_sprite)

        # Фон
        self.background_list = None
        self.background_sprite = None

    def on_show_view(self):
        if self.player_list is None:
            self.setup()
        # Привязываем камеры к окну
        if self.window:
            self.camera_sprites.match_window()
            self.camera_gui.match_window()

    def setup(self):
        self.lives = 3
        self.has_key = False
        self.key_hud_sprite.alpha = 100

        # Фон
        self.background_list = arcade.SpriteList()
        bg_map = {1: "images/office.png",
                  2: "images/winter.png",
                  3: "images/military_base.png"}

        bg_path = bg_map.get(self.level_num, ":resources:images/backgrounds/abstract_1.jpg")
        self.background_sprite = arcade.Sprite(bg_path, 1.0)
        scale_x = SCREEN_WIDTH / self.background_sprite.width
        scale_y = SCREEN_HEIGHT / self.background_sprite.height
        self.background_sprite.scale = max(scale_x, scale_y)
        self.background_sprite.center_x = SCREEN_WIDTH // 2
        self.background_sprite.center_y = SCREEN_HEIGHT // 2
        self.background_list.append(self.background_sprite)

        # Пол и стены
        self.wall_list = arcade.SpriteList()
        for x in range(0, SCREEN_WIDTH + 64, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", SPRITE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)

        # Стены по краям
        for y in range(0, SCREEN_HEIGHT, 64):
            # Левая стена

            wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING)
            wall.left = 0
            wall.center_y = y
            self.wall_list.append(wall)
            # Правая стена
            wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING)
            wall.right = SCREEN_WIDTH
            wall.center_y = y
            self.wall_list.append(wall)

        # Игрок
        self.player_list = arcade.SpriteList()
        self.player_sprite = Player(SPRITE_SCALING)
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 200
        self.player_list.append(self.player_sprite)

        # Физика
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, GRAVITY)

        # Дверь
        self.door_list = arcade.SpriteList()
        self.door_sprite = arcade.Sprite(":resources:images/tiles/doorClosed_mid.png", SPRITE_SCALING)
        self.door_sprite.center_x = 1180
        self.door_sprite.center_y = 100
        self.door_list.append(self.door_sprite)

        # Ключ на карте
        self.key_list = arcade.SpriteList()
        self.key_sprite = arcade.Sprite(":resources:images/items/keyYellow.png", SPRITE_SCALING)
        self.key_sprite.center_x = 600
        self.key_sprite.center_y = 200
        self.key_list.append(self.key_sprite)

        # Пули
        self.player_bullet_list = arcade.SpriteList()
        self.enemy_bullet_list = arcade.SpriteList()

        # Враги
        self.enemy_list = arcade.SpriteList()
        if self.level_num == 1:
            for i in range(random.randint(3, 7)):
                enemy = arcade.Sprite(":resources:images/enemies/saw.png", SPRITE_SCALING)
                enemy.center_x = random.randint(100, 1000)
                enemy.center_y = random.randint(100, 600)
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)
        elif self.level_num == 2:
            for i in range(6):
                enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", SPRITE_SCALING)
                enemy.center_x = random.randint(100, 1000)
                enemy.center_y = random.randint(100, 600)
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)
        elif self.level_num == 3:
            for i in range(3):
                enemy = arcade.Sprite(":resources:images/enemies/fly.png", SPRITE_SCALING)
                enemy.center_x = random.randint(100, 1000)
                enemy.center_y = random.randint(100, 600)
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)

    # отрисовка
    def on_draw(self):
        self.clear()
        
        # Активируем камеру для игровых объектов
        self.camera_sprites.use()
        
        self.wall_list.draw()
        # Фон
        self.background_list.draw()
        # Игровые объекты
        self.player_list.draw()
        self.door_list.draw()
        self.enemy_list.draw()
        if not self.has_key:
            self.key_list.draw()
        # Пули рисуем поверх всего, чтобы были хорошо видны
        self.player_bullet_list.draw()
        self.enemy_bullet_list.draw()

        # Активируем камеру для HUD (не следует за игроком)
        self.camera_gui.use()
        
        # HUD
        self.key_hud_list.draw()

        for i in range(self.lives):
            # Жизни
            arcade.draw_text("❤️", SCREEN_WIDTH - 50 - i * 40, 20, arcade.color.RED, 24)

        # Задачи
        if not self.has_key:
            arcade.draw_text("Найдите ключ!", 10, SCREEN_HEIGHT - 80, arcade.color.YELLOW, 16)
        elif len(self.enemy_list) > 0:
            arcade.draw_text("Уничтожьте всех врагов!", 10, SCREEN_HEIGHT - 100, arcade.color.WHITE, 16)
        else:
            arcade.draw_text("Идите к двери!", 10, SCREEN_HEIGHT - 120, arcade.color.GREEN, 16)

        self.draw_post_effects()  # фильтры и яркость

    def on_update(self, delta_time):  # физика
        self.physics_engine.update()

        # Камера следует за игроком: в Arcade 3 position — центр вида (как в туториале)
        self.camera_sprites.position = (self.player_sprite.center_x, self.player_sprite.center_y)

        self.player_bullet_list.update(delta_time)
        self.enemy_bullet_list.update(delta_time)

        # Враги стреляют
        for enemy in self.enemy_list:
            enemy.shoot_timer += delta_time
            if enemy.shoot_timer >= random.randint(1, 4):
                bullet = Bullet(enemy.center_x, enemy.center_y, self.player_sprite.center_x,
                                self.player_sprite.center_y)
                self.enemy_bullet_list.append(bullet)
                enemy.shoot_timer = 0

        # Подбор ключа
        if not self.has_key and arcade.check_for_collision(self.player_sprite, self.key_sprite):
            self.has_key = True
            self.key_sprite.remove_from_sprite_lists()
            self.key_hud_sprite.alpha = 255
            key_sound = arcade.load_sound('sound/key.mp3')
            arcade.play_sound(key_sound, volume=1)

        # Пули игрока по врагам
        for bullet in self.player_bullet_list:
            hit_list = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            if hit_list:
                bullet.remove_from_sprite_lists()
                for enemy in hit_list:
                    enemy.remove_from_sprite_lists()

        # Пули врагов по игроку
        for bullet in self.enemy_bullet_list:
            if arcade.check_for_collision(bullet, self.player_sprite):
                bullet.remove_from_sprite_lists()
                self.lives -= 1
                if self.lives <= 0:
                    self.setup()

        # Пули за экраном
        cam_cx, cam_cy = self.camera_sprites.position[0], self.camera_sprites.position[1]
        screen_left = cam_cx - SCREEN_WIDTH / 2
        screen_right = cam_cx + SCREEN_WIDTH / 2
        screen_bottom = cam_cy - SCREEN_HEIGHT / 2
        screen_top = cam_cy + SCREEN_HEIGHT / 2

        for bullet_list in [self.player_bullet_list, self.enemy_bullet_list]:
            to_remove = [b for b in bullet_list if (b.bottom > screen_top or b.top < screen_bottom or
                         b.right < screen_left or b.left > screen_right)]
            for b in to_remove:
                b.remove_from_sprite_lists()

        # Анимация
        self.player_sprite.is_walking = self.player_sprite.change_x != 0
        self.player_sprite.update_animation(delta_time)

        # Переход к двери
        if arcade.check_for_collision(self.player_sprite, self.door_sprite) and self.has_key and len(
                self.enemy_list) == 0:
            if self.level_num == 3:
                self.window.show_view(EndView())
            else:
                next_level = LevelView(self.level_num + 1)
                next_level.setup()
                self.window.show_view(next_level)

    # движение
    def on_key_press(self, key, modifiers):
        if key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_SPEED
            self.player_sprite.face_direction = FaceDirection.LEFT
        elif key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_SPEED
            self.player_sprite.face_direction = FaceDirection.RIGHT
        elif key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.A, arcade.key.D):
            self.player_sprite.change_x = 0

    # стрельба
    def on_mouse_press(self, x, y, button, modifiers):
        # Преобразуем экранные координаты мыши в мировые
        world = self.camera_sprites.unproject((x, y))
        world_x, world_y = world.x, world.y

        bullet = Bullet(self.player_sprite.center_x, self.player_sprite.center_y, world_x, world_y)
        self.player_bullet_list.append(bullet)
        arcade.play_sound(arcade.load_sound(":resources:/sounds/laser1.wav"), 0.2)


# настройки
class MainMenuView(arcade.View, PostEffectMixin):
    def __init__(self):
        super().__init__()
        self.play_main = False
        # Музыка лоби
        if not self.play_main:
            self.play_main = arcade.play_sound(main_sound, volume=1, loop=True)
        
        self.background_list = arcade.SpriteList()
        self.buttons = []
        self.selected_button = 0

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

        # Фон
        self.background_list = arcade.SpriteList()
        bg_path = "images/menu_background.png"
        self.background_sprite = arcade.Sprite(bg_path, 1.0)

        # Масштабирование по экрану
        if self.background_sprite.width > 0 and self.background_sprite.height > 0:
            scale_x = SCREEN_WIDTH / self.background_sprite.width
            scale_y = SCREEN_HEIGHT / self.background_sprite.height
            self.background_sprite.scale = max(scale_x, scale_y)
        else:
            self.background_sprite.scale = 1.0

        self.background_sprite.center_x = SCREEN_WIDTH // 2
        self.background_sprite.center_y = SCREEN_HEIGHT // 2
        self.background_list.append(self.background_sprite)

        # Создание кнопок
        button_y_start = SCREEN_HEIGHT // 2 + 50
        button_spacing = 60
        self.buttons = [
            ("ИГРАТЬ", SCREEN_WIDTH // 2, button_y_start, self.start_game),
            ("НАСТРОЙКИ", SCREEN_WIDTH // 2, button_y_start - button_spacing, self.show_settings),
            ("ПОДПИСКА", SCREEN_WIDTH // 2, button_y_start - 2 * button_spacing, self.podpiska),
            ("ВЫХОД", SCREEN_WIDTH // 2, button_y_start - 3 * button_spacing, self.exit_game),
        ]

    def on_draw(self):
        self.clear()
        self.background_list.draw()
        for i, (text, x, y, _) in enumerate(self.buttons):
            color = arcade.color.YELLOW if i == self.selected_button else arcade.color.WHITE
            arcade.draw_text(text, x, y, color, 30, anchor_x="center", bold=True)
        self.draw_post_effects()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected_button = (self.selected_button - 1) % len(self.buttons)
        elif key == arcade.key.DOWN:
            self.selected_button = (self.selected_button + 1) % len(self.buttons)
        elif key == arcade.key.ENTER:
            _, _, _, callback = self.buttons[self.selected_button]
            callback()

    def start_game(self):
        main_sound.stop(self.play_main)
        self.window.show_view(StoryView(self.window))

    def podpiska(self):
        self.window.show_view(PodpiskaView())

    def show_settings(self):
        self.window.show_view(SettingsView())

    def exit_game(self):
        arcade.exit()


class SettingsView(arcade.View, PostEffectMixin):
    FILTERS = ["NONE", "DARK", "COLD", "WARM"]

    def on_draw(self):
        self.clear()
        arcade.draw_text("НАСТРОЙКИ", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100, arcade.color.WHITE, 36, anchor_x="center")
        arcade.draw_text(f"Яркость: {SETTINGS['brightness']:.1f}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
                         arcade.color.WHITE, 24, anchor_x="center")
        arcade.draw_text(f"Фильтр: {SETTINGS['filter']}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 24,
                         anchor_x="center")
        arcade.draw_text("← → яркость | ↑ ↓ фильтр | ESC назад", SCREEN_WIDTH / 2, 100, arcade.color.GRAY, 16,
                         anchor_x="center")
        self.draw_post_effects()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            SETTINGS["brightness"] = max(0.5, SETTINGS["brightness"] - 0.1)
        elif key == arcade.key.RIGHT:
            SETTINGS["brightness"] = min(1.5, SETTINGS["brightness"] + 0.1)
        elif key == arcade.key.UP:
            i = self.FILTERS.index(SETTINGS["filter"])
            SETTINGS["filter"] = self.FILTERS[(i + 1) % len(self.FILTERS)]
        elif key == arcade.key.DOWN:
            i = self.FILTERS.index(SETTINGS["filter"])
            SETTINGS["filter"] = self.FILTERS[(i - 1) % len(self.FILTERS)]
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MainMenuView())


class EndView(arcade.View, PostEffectMixin):
    def __init__(self, window = None, background_color = None):
        super().__init__(window, background_color)
        win_sound = arcade.load_sound("sound/win.mp3")
        arcade.play_sound(win_sound, volume=1)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text("ПОБЕДА!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.GREEN, 40, anchor_x="center")
        arcade.draw_text("Вы сбежали с корабля!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 24,
                         anchor_x="center")
        arcade.draw_text("Нажмите ESC, чтобы выйти", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50, arcade.color.GRAY, 18,
                         anchor_x="center")
        self.draw_post_effects()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()

class StoryView(arcade.View, PostEffectMixin):
    IMAGE_PATHS = [
        "history/1.jpg",
        "history/2.jpeg",
        "history/3.jpg",
        "history/4.jpeg",
        "history/5.jpg.avif",
    ]
    HISTORY_TEXTS = ["123", "321", "132", "213", "231"]

    def __init__(self, window=None):
        super().__init__(window)
        self._game_window = window
        self.panels = arcade.SpriteList()
        self.current_panel = 0
        self.timer = 0
        self.switch_time = 2.0
        self._transition_done = False
        self._pending_go_to_level = False
        self._panels_loaded = False
        self.total_panels = 0
        self.history = list(self.HISTORY_TEXTS)

    def on_show_view(self):
        if self._panels_loaded:
            return
        self._panels_loaded = True
        for path in self.IMAGE_PATHS:
            try:
                panel = arcade.Sprite(path)
                panel.center_x = SCREEN_WIDTH // 2
                panel.center_y = SCREEN_HEIGHT // 2
                scale_x = SCREEN_WIDTH / panel.width
                scale_y = SCREEN_HEIGHT / panel.height
                panel.scale = min(scale_x, scale_y) * 0.8
                panel.alpha = 0
                self.panels.append(panel)
            except Exception:
                pass
        self.total_panels = len(self.panels)

    def on_draw(self):
        self.clear()

        if self.current_panel < len(self.panels):
            temp_list = arcade.SpriteList()
            temp_list.append(self.panels[self.current_panel])
            temp_list.draw()

        # Счётчик не больше total_panels
        num = min(self.current_panel + 1, self.total_panels) if self.total_panels else 0
        arcade.draw_text(
            f"История {num}/{self.total_panels}",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 150,
            arcade.color.WHITE,
            20,
            anchor_x="center"
        )

        arcade.draw_text(
            "ENTER — далее | SPACE — пропустить",
            SCREEN_WIDTH // 2,
            100,
            arcade.color.GRAY,
            16,
            anchor_x="center"
        )

        if self.current_panel < len(self.history):
            arcade.draw_text(
                self.history[self.current_panel],
                SCREEN_WIDTH // 2,
                140,
                arcade.color.WHITE,
                20,
                anchor_x="center",
                align="center"
            )

        self.draw_post_effects()

    def on_update(self, delta_time):
        if self.current_panel >= self.total_panels:
            return

        panel = self.panels[self.current_panel]
        panel.alpha = min(255, panel.alpha + 300 * delta_time)
        self.timer += delta_time

        if self.timer >= self.switch_time:
            self.timer = 0
            self.current_panel += 1

            if self.current_panel >= self.total_panels:
                game_view = LevelView(1)
                game_view.setup()
                self.window.show_view(game_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.current_panel += 1
            self.timer = 0

            if self.current_panel >= self.total_panels:
                game_view = LevelView(1)
                game_view.setup()
                self.window.show_view(game_view)

        if key == arcade.key.SPACE:
            game_view = LevelView(1)
            game_view.setup()
            self.window.show_view(game_view)

class PodpiskaView(arcade.View, PostEffectMixin):
    def __init__(self):
        super().__init__()
        self.background_list = arcade.SpriteList()

        bg = arcade.Sprite("images/podpiska.jpg")
        bg.width = SCREEN_WIDTH
        bg.height = SCREEN_HEIGHT
        bg.center_x = SCREEN_WIDTH // 2
        bg.center_y = SCREEN_HEIGHT // 2
        self.background_list.append(bg)

    def on_draw(self):
        self.clear()
        self.background_list.draw()
        self.draw_post_effects()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MainMenuView())


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()