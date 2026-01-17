import arcade
import math
import random

# Константы
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "The Path to Emptiness"

PLAYER_SPEED = 5
SPRITE_SCALING = 0.5
BULLET_SPEED = 7
ENEMY_SHOOT_INTERVAL = random.randint(1, 4)
GRAVITY = 1.0
PLAYER_JUMP_SPEED = 18


class LevelView(arcade.View):
    def __init__(self, level_num):
        super().__init__()
        self.level_num = level_num
        self.player_sprite = None
        self.player_list = None
        self.wall_list = None
        self.door_sprite = None
        self.door_list = None
        self.enemy_list = None
        self.player_bullet_list = None
        self.enemy_bullet_list = None
        self.key_sprite = None
        self.key_list = None
        self.has_key = False
        self.lives = 3
        self.physics_engine = None

        # HUD: иконка ключа
        self.key_hud_list = arcade.SpriteList()
        self.key_hud_sprite = arcade.Sprite(
            ":resources:images/items/keyYellow.png", 0.4
        )
        self.key_hud_sprite.position = (40, SCREEN_HEIGHT - 50)
        self.key_hud_list.append(self.key_hud_sprite)

        # Фон
        self.background_list = None
        self.background_sprite = None

    def setup(self):
        self.lives = 3
        self.has_key = False
        self.key_hud_sprite.alpha = 100  # прозрачный

        # Загрузка фона
        self.background_list = arcade.SpriteList()
        bg_map = {
            1: "images/office.png",
            2: "images/winter.png",
            3: "images/military_base.png",
        }
        bg_path = bg_map.get(
            self.level_num, ":resources:images/backgrounds/abstract_1.jpg"
        )

        self.background_sprite = arcade.Sprite(bg_path, 1.0)
        scale_x = SCREEN_WIDTH / self.background_sprite.width
        scale_y = SCREEN_HEIGHT / self.background_sprite.height
        self.background_sprite.scale = max(scale_x, scale_y)
        self.background_sprite.center_x = SCREEN_WIDTH // 2
        self.background_sprite.center_y = SCREEN_HEIGHT // 2
        self.background_list.append(self.background_sprite)

        # Пол и стены
        self.wall_list = arcade.SpriteList()

        # Пол
        for x in range(0, SCREEN_WIDTH + 64, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", SPRITE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)

        # Стены по краям
        for y in range(0, SCREEN_HEIGHT, 64):
            # Левая стена
            wall = arcade.Sprite(
                ":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING
            )
            wall.left = 0
            wall.center_y = y
            self.wall_list.append(wall)
            # Правая стена
            wall = arcade.Sprite(
                ":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING
            )
            wall.right = SCREEN_WIDTH
            wall.center_y = y
            self.wall_list.append(wall)

        # Игрок
        self.player_list = arcade.SpriteList()
        self.player_sprite = arcade.Sprite(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            SPRITE_SCALING,
        )
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 200
        self.player_list.append(self.player_sprite)

        # Физика
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, walls=self.wall_list, gravity_constant=GRAVITY
        )

        # Дверь
        self.door_list = arcade.SpriteList()
        self.door_sprite = arcade.Sprite(
            ":resources:images/tiles/doorClosed_mid.png", SPRITE_SCALING
        )
        self.door_sprite.center_x = 1180
        self.door_sprite.center_y = 100
        self.door_list.append(self.door_sprite)

        # Ключ на карте
        self.key_list = arcade.SpriteList()
        self.key_sprite = arcade.Sprite(
            ":resources:images/items/keyYellow.png", SPRITE_SCALING
        )
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
                enemy = arcade.Sprite(
                    ":resources:images/enemies/saw.png", SPRITE_SCALING
                )
                enemy.center_x = random.randint(100, 1000)
                enemy.center_y = random.randint(100, 600)
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)
        elif self.level_num == 2:
            for i in range(6):
                enemy = arcade.Sprite(
                    ":resources:images/enemies/wormGreen.png", SPRITE_SCALING
                )
                enemy.center_x = random.randint(100, 1000)
                enemy.center_y = random.randint(100, 600)
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)
        elif self.level_num == 3:
            for i in range(3):
                enemy = arcade.Sprite(
                    ":resources:images/enemies/fly.png", SPRITE_SCALING
                )
                enemy.center_x = 400 + i * 100
                enemy.center_y = 200
                enemy.shoot_timer = 0
                self.enemy_list.append(enemy)

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        # Фон
        self.background_list.draw()
        # Игровые объекты
        self.player_list.draw()
        self.door_list.draw()
        self.enemy_list.draw()
        self.player_bullet_list.draw()
        self.enemy_bullet_list.draw()
        if not self.has_key:
            self.key_list.draw()
        # HUD
        self.key_hud_list.draw()
        # Жизни
        for i in range(self.lives):
            arcade.draw_text(
                "❤️", SCREEN_WIDTH - 50 - i * 40, 20, arcade.color.RED, font_size=24
            )
        # Задачи
        if not self.has_key:
            arcade.draw_text(
                "Найдите ключ!", 10, SCREEN_HEIGHT - 80, arcade.color.YELLOW, 16
            )
        if len(self.enemy_list) > 0:
            arcade.draw_text(
                "Уничтожьте всех врагов!",
                10,
                SCREEN_HEIGHT - 100,
                arcade.color.WHITE,
                16,
            )
        if self.has_key and len(self.enemy_list) == 0:
            arcade.draw_text(
                "Идите к двери!", 10, SCREEN_HEIGHT - 120, arcade.color.GREEN, 16
            )

    def on_update(self, delta_time):
        # Физика
        self.physics_engine.update()

        # Обновление пуль
        self.player_bullet_list.update()
        self.enemy_bullet_list.update()

        # Враги стреляют
        for enemy in self.enemy_list:
            enemy.shoot_timer += delta_time
            if enemy.shoot_timer >= ENEMY_SHOOT_INTERVAL:
                self.enemy_shoot(enemy)
                enemy.shoot_timer = 0

        # Подбор ключа
        if not self.has_key and arcade.check_for_collision(
            self.player_sprite, self.key_sprite
        ):
            self.has_key = True
            self.key_sprite.remove_from_sprite_lists()
            self.key_hud_sprite.alpha = 255

        # Пули игрока - враги
        for bullet in self.player_bullet_list:
            hit_list = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            if hit_list:
                bullet.remove_from_sprite_lists()
                for enemy in hit_list:
                    enemy.remove_from_sprite_lists()

        # Пули врагов - игрок
        for bullet in self.enemy_bullet_list:
            if arcade.check_for_collision(bullet, self.player_sprite):
                bullet.remove_from_sprite_lists()
                self.lives -= 1
                if self.lives <= 0:
                    self.setup()  # перезапуск уровня

        # Удаление пуль за экраном
        for bullet_list in [self.player_bullet_list, self.enemy_bullet_list]:
            for bullet in bullet_list:
                if (
                    bullet.bottom > SCREEN_HEIGHT
                    or bullet.top < 0
                    or bullet.right < 0
                    or bullet.left > SCREEN_WIDTH
                ):
                    bullet.remove_from_sprite_lists()

        # Переход в дверь
        if (
            arcade.check_for_collision(self.player_sprite, self.door_sprite)
            and self.has_key
            and len(self.enemy_list) == 0
        ):
            if self.level_num == 3:
                end_view = EndView()
                self.window.show_view(end_view)
            else:
                next_level = LevelView(self.level_num + 1)
                next_level.setup()
                self.window.show_view(next_level)

    # Ходьба
    def on_key_press(self, key, modifiers):
        if key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_SPEED
        elif key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_SPEED
        elif key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.A, arcade.key.D):
            self.player_sprite.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):
        bullet = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png", 0.5)
        bullet.center_x = self.player_sprite.center_x
        bullet.center_y = self.player_sprite.center_y

        angle = math.atan2(y - bullet.center_y, x - bullet.center_x)
        bullet.angle = math.degrees(angle)
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        self.player_bullet_list.append(bullet)

    def enemy_shoot(self, enemy):
        bullet = arcade.Sprite(":resources:images/space_shooter/laserRed01.png", 0.5)
        bullet.center_x = enemy.center_x
        bullet.center_y = enemy.center_y

        angle = math.atan2(
            self.player_sprite.center_y - bullet.center_y,
            self.player_sprite.center_x - bullet.center_x,
        )
        bullet.angle = math.degrees(angle)
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        self.enemy_bullet_list.append(bullet)


class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_sprite = None
        self.background_list = None
        self.buttons = []
        self.selected_button = 0

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

        # Загрузка фона
        self.background_list = arcade.SpriteList()
        bg_path = "images/menu_background.png"
        self.background_sprite = arcade.Sprite(bg_path, 1.0)
        if self.background_sprite.width > 0 and self.background_sprite.height > 0:
            scale_x = SCREEN_WIDTH / self.background_sprite.width
            scale_y = SCREEN_HEIGHT / self.background_sprite.height
            self.background_sprite.scale = max(scale_x, scale_y)
        else:
            self.background_sprite.scale = 1.0

        self.background_sprite.center_x = SCREEN_WIDTH // 2
        self.background_sprite.center_y = SCREEN_HEIGHT // 2
        self.background_list.append(self.background_sprite)

        # Создаём кнопки
        button_y_start = SCREEN_HEIGHT // 2 + 50
        button_spacing = 60

        self.buttons = [
            (
                "ИГРАТЬ", 
                SCREEN_WIDTH // 2, 
                button_y_start,
                self.start_game),
            (
                "НАСТРОЙКИ",
                SCREEN_WIDTH // 2,
                button_y_start - button_spacing,
                self.show_settings,
            ),
            (
                "ВЫХОД",
                SCREEN_WIDTH // 2,
                button_y_start - 2 * button_spacing,
                self.exit_game,
            ),
        ]

    def on_draw(self):
        self.clear()
        self.background_list.draw()

        for i, (text, x, y, _) in enumerate(self.buttons):
            color = (arcade.color.YELLOW if i == self.selected_button else arcade.color.WHITE)
            arcade.draw_text(text, x, y, color, font_size=30, anchor_x="center", bold=True)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected_button = (self.selected_button - 1) % len(self.buttons)
        elif key == arcade.key.DOWN:
            self.selected_button = (self.selected_button + 1) % len(self.buttons)
        elif key == arcade.key.ENTER:
            _, _, _, callback = self.buttons[self.selected_button]
            callback()

    def start_game(self):
        game_view = LevelView(1)
        game_view.setup()
        self.window.show_view(game_view)

    def show_settings(self):
        # Пока пусто — можно добавить позже
        pass

    def exit_game(self):
        arcade.exit()


class EndView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "ПОБЕДА!",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 50,
            arcade.color.GREEN,
            font_size=40,
            anchor_x="center",
        )
        arcade.draw_text(
            "Вы сбежали с корабля!",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            font_size=24,
            anchor_x="center",
        )
        arcade.draw_text(
            "Нажмите ESC, чтобы выйти",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 50,
            arcade.color.GRAY,
            font_size=18,
            anchor_x="center",
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
