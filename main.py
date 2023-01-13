import pygame
import math
import pytmx


# Базовые константы
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 0, 0
FPS = 30
MAPS_DIR = 'maps'
SPRITES_DIR = 'sprites'
TILE_SIZE = 25
MOVE_SPEED = 5
ENEMY_EVENT_TYPE = 30
ENEMY_DELAY = 200

# Вспомогательные переменные для игры
map_number = 1
bullets = []
enemies = []

# Константы с цветами
BLACK, WHITE, RED = (0, 0, 0), (255, 255, 255), (255, 0, 0)
GREEN, BLUE, YELLOW = (0, 255, 0), (0, 0, 255), (255, 255, 0)

# Вспомогательные настройки
hex = False
person_hitbox_view = False


class Map:
    """
    Класс Map создает карту из указанного файла формата *.tmx...

    TODO: Переделать описание класса да и ваще всего кода

    Так-же в инициализатор передается список ID тайлов, по которым можно ходить и тайлы-триггеры.
    """

    def __init__(self, map_filename, free_tiles, trigger_tiles, spawn_pos):
        self.map = pytmx.load_pygame(f'{MAPS_DIR}/{map_filename}')
        self.spawn_pos = spawn_pos
        self.height = self.map.height
        self.width = self.map.width
        self.free_tiles = free_tiles
        self.trigger_tiles = trigger_tiles
        self.spawn_enemies()

    def render(self, screen):  # Отрисовка карты на холсте
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (x * TILE_SIZE, y * TILE_SIZE))
                if hex:  # Белая сетка
                    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, WHITE, rect, 1)

    def get_tile_id(self, pos):  # Возвращает ID тайла по координатам (x, y). Помогает понять его тип
        return self.map.tiledgidmap[self.map.get_tile_gid(*pos, 0)] - 1

    def get_tile_coords(self, pos):  # Возвращает пиксельные координаты тайла
        return pos[0] * TILE_SIZE, pos[1] * TILE_SIZE

    def set_spawn_pos(self, pos):
        self.spawn_pos = pos

    def spawn_enemies(self):          # Спавнит врагов на тайлах спавна мобов. Все объекты создаются в списке enemies,
        for y in range(self.height):  # там они рендерятся и обрабабатываются.
            for x in range(self.width):
                if self.get_tile_id((x, y)) == 3:
                    enemies.append(Enemy((x, y), 'enemy_tex.png'))

    def is_free(self, pos):  # Проверка на проходимость тайла
        return self.get_tile_id(pos) in self.free_tiles

    def find_path_step(self, start, target):  # Алгоритм поиска кратчайшего пути из тайла start в тайл target.
        INF = 1000                            # Применяется для объектов врага
        x, y = start
        distance = [[INF] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (0, 1), (1, 0), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 < next_x < self.width and 0 < next_y < self.height and \
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == INF:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        x, y = target
        if distance[y][x] == INF or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y


class Person:
    """
    Класс Person создаёт сущностей на карте. При инициализации прописывается начальная точка появления
    и текстуру
    """

    def __init__(self, pos, texture):
        super().__init__()
        self.person_texture = pygame.sprite.Sprite()
        self.person_texture.image = pygame.image.load(f'{SPRITES_DIR}/{texture}')
        self.person_texture.rect = self.person_texture.image.get_rect()
        self.x, self.y = pos
        self.pixel_pos = (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)
        self.hitbox = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def get_pos(self):
        return round(self.pixel_pos[0] / TILE_SIZE), round(self.pixel_pos[1] / TILE_SIZE)

    def set_pos(self, pos):
        self.x, self.y = pos[0], pos[1]
        self.set_pixel_pos((self.x * TILE_SIZE, self.y * TILE_SIZE))
        self.hitbox = pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def set_pixel_pos(self, pixel_pos):
        self.pixel_pos = pixel_pos
        self.hitbox = pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def get_pixel_pos(self):
        return self.pixel_pos

    def get_rect(self):
        return pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def render(self, screen):  # Отрисовка существа на холсте
        screen.blit(self.person_texture.image, self.pixel_pos)
        if person_hitbox_view:  # Hitbox существа
            pygame.draw.rect(screen, RED, self.hitbox, 1)


class Enemy(Person):  # TODO: дать врагам возможность убивать и умирать, а также пофиксить стак врагов в одном тайле

    def __init__(self, pos, texture):
        super().__init__(pos, texture)
        self.pos = pos


class Hero(Person):  # TODO: создать разнообразные пушки для игрока :)
    """
    Класс Игрока, наследуется от Person. Имеет допольнительный атрибут ammo - количество патрон / and smth more...
    """

    def __init__(self, pos, texture, ammo):
        super().__init__(pos, texture)
        self.pos = pos
        self.ammo = ammo
        self.aiming = False

    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            pos = self.get_pixel_pos()
            bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))
        elif self.ammo == 0:
            print('No ammo')  # TODO: Сделать что-то с патронами

    def aim(self):
        self.aiming = not self.aiming

    def update_bullets(self, screen):
        for bullet in bullets[:]:
            bullet.update()
            if not screen.get_rect().collidepoint(bullet.pos):
                bullets.remove(bullet)


class Bullet:
    """
    TODO: Сделать описание класса пули
    """
    def __init__(self, x, y):
        self.pos = (x, y)
        mx, my = pygame.mouse.get_pos()
        self.dir = (mx - x, my - y)
        length = math.hypot(*self.dir)
        if length == 0.0:
            self.dir = (0, -1)
        else:
            self.dir = (self.dir[0] / length, self.dir[1] / length)
        angle = math.degrees(math.atan2(-self.dir[1], self.dir[0]))

        self.bullet = pygame.Surface((10, 4)).convert_alpha()
        self.bullet.fill(YELLOW)
        self.bullet = pygame.transform.rotate(self.bullet, angle)
        self.speed = 20
        self.rect = self.bullet.get_rect()

    def get_pos(self):
        return self.pos

    def get_rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.bullet.get_width(), self.bullet.get_height())

    def update(self):
        self.pos = (self.pos[0] + self.dir[0] * self.speed,
                    self.pos[1] + self.dir[1] * self.speed)

    def draw(self, screen):
        bullet_rect = self.bullet.get_rect(center=self.pos)
        screen.blit(self.bullet, bullet_rect)

    def get_tile_pos(self, pos):
        bullet_rect = self.bullet.get_rect(center=pos)
        return bullet_rect[0] // TILE_SIZE, bullet_rect[1] // TILE_SIZE


class Game:
    """
    Класс Game управляет логикой и ходом игры. При инициализации получает объект карты и объекты существ.
    """

    def __init__(self, map, hero):
        self.map = map
        self.hero = hero

    def render(self, screen):  # Синхронизированная отрисовка
        self.map.render(screen)
        self.hero.render(screen)
        for enemy in enemies:
            if self.check_enemy_for_bullet(enemy):
                enemy.render(screen)
            else:
                enemies.remove(enemy)
        self.hero.update_bullets(screen)
        for bullet in bullets:
            if self.check_wall_for_bullet(bullet):
                bullet.draw(screen)
            else:
                bullets.remove(bullet)

    def check_enemy_for_bullet(self, enemy):
        for bullet in bullets:
            if bullet.get_rect().colliderect(enemy.get_rect()):
                return False
        return True

    def check_wall_for_bullet(self, bullet):  # Проверка на стену для пули
        if self.map.get_tile_id(bullet.get_tile_pos(bullet.get_pos())) not in self.map.free_tiles:
            return False
        return True

    def check_wall_for_player(self, next_pixel_x, next_pixel_y):  # Проверка на стену для игрока
        tile = (round(next_pixel_x / TILE_SIZE), round(next_pixel_y / TILE_SIZE))
        player_hitbox_rect = self.hero.get_rect()
        for y in range(tile[1] - 1, tile[1] + 2):
            for x in range(tile[0] - 1, tile[0] + 2):
                if self.map.get_tile_id((x, y)) not in self.map.free_tiles:
                    wall_tile = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if wall_tile.colliderect(player_hitbox_rect):
                        if wall_tile.collidepoint(player_hitbox_rect.midleft):
                            next_pixel_x += MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midright):
                            next_pixel_x -= MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midtop):
                            next_pixel_y += MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midbottom):
                            next_pixel_y -= MOVE_SPEED
        return next_pixel_x, next_pixel_y

    def update_hero(self):  # Передвижение Игрока
        global map_number
        next_pixel_x, next_pixel_y = self.hero.get_pixel_pos()
        if pygame.key.get_pressed()[pygame.K_a] or pygame.key.get_pressed()[pygame.K_LEFT]:
            next_pixel_x -= MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_pixel_x += MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_UP]:
            next_pixel_y -= MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_DOWN]:
            next_pixel_y += MOVE_SPEED
        self.hero.set_pixel_pos(self.check_wall_for_player(next_pixel_x, next_pixel_y))
        if self.map.get_tile_id(self.hero.get_pos()) in self.map.trigger_tiles:  # Если игрок активировал триггер карты
            triggger_id = self.map.get_tile_id(self.hero.get_pos())
            if triggger_id == 2:  # Смена карты
                map_number += 1
                self.map.set_spawn_pos((9, 6))
                self.change_map(self.map, f'map{map_number}.tmx', [0, 2, 3], [2, 3], self.map.spawn_pos)

    def move_enemies(self):  # Функция для перемещения всех врагов по алгоритму find_path_step()
        for enemy in enemies:
            self.move_enemy(enemy)

    def move_enemy(self, enemy):
        enemy_pos = enemy.get_pos()
        enemy_pixel_pos = list(enemy.get_pixel_pos())
        next_pos = self.map.find_path_step(enemy_pos, self.hero.get_pos())
        direction = 'stay'
        if next_pos[0] > enemy_pos[0]:
            direction = 'right'
        elif next_pos[0] < enemy_pos[0]:
            direction = 'left'
        elif next_pos[1] > enemy_pos[1]:
            direction = 'down'
        elif next_pos[1] < enemy_pos[1]:
            direction = 'up'
        dt = 5
        for i in range(5):
            if direction == 'right':
                enemy_pixel_pos[0] += dt
            elif direction == 'left':
                enemy_pixel_pos[0] -= dt
            elif direction == 'down':
                enemy_pixel_pos[1] += dt
            elif direction == 'up':
                enemy_pixel_pos[1] -= dt
            enemy.set_pixel_pos(enemy_pixel_pos)

    def change_map(self, map_object, map_filename, free_tiles, trigger_tiles, spawn_pos):
        bullets.clear()
        enemies.clear()
        print(f'''
            ########################
            # map{map_number - 1} changed to map{map_number} #
            ########################''')
        map_object.__init__(map_filename, free_tiles, trigger_tiles, spawn_pos)
        self.hero.set_pos(spawn_pos)


def main():
    pygame.init()
    clock = pygame.time.Clock()
    pygame.time.set_timer(ENEMY_EVENT_TYPE, ENEMY_DELAY)
    pygame.display.set_caption('Hot Rooms')
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.FULLSCREEN)

    map = Map(f'map{map_number}.tmx', [0, 2, 3], [2], (1, 1))
    hero = Hero(map.spawn_pos, 'player1.png', 1000)

    game = Game(map, hero)

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    hero.shoot()
                if event.button == 3:
                    hero.aim()
            if event.type == ENEMY_EVENT_TYPE:
                game.move_enemies()
        game.update_hero()
        screen.fill((0, 0, 0))
        game.render(screen)
        if hero.aiming:
            pygame.draw.line(screen, pygame.Color(0, 255, 0), hero.get_rect().center, pygame.mouse.get_pos(), 1)
        pygame.display.flip()
        # print('FPS:', int(clock.get_fps()))


if __name__ == '__main__':
    main()
    pygame.quit()
