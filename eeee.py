import pygame
import sys
import random
import numpy as np
import time
import pickle

# Класс для пуль
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image_name):
        super().__init__()
        image = pygame.image.load(image_name).convert_alpha()
        self.image = pygame.transform.scale(image, (15, 15))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.y -= 5
        if self.rect.y == 0:
            self.kill()

# Класс для игрока
class Player:
    def __init__(self, player_speed):
        super().__init__()
        player_left = pygame.image.load('left.png').convert_alpha()
        left = pygame.transform.scale(player_left, (55, 55))
        player_right = pygame.image.load('right.png').convert_alpha()
        right = pygame.transform.scale(player_right, (55, 55))
        player_up = pygame.image.load('up.png').convert_alpha()
        up = pygame.transform.scale(player_up, (40, 40))
        self.player_pos = [left, right, up]
        self.image = self.player_pos[1]
        self.rect = pygame.Rect(0, 0, 50, 50)
        self.rect.center = (200, 700)  # Устанавливаем игрока внизу по центру
        self.gravity = 0
        self.jump_sound = pygame.mixer.Sound('jump.wav')
        self.jump_sound.set_volume(0.5)
        self.rocket_sound = pygame.mixer.Sound('rocket.mp3')
        self.rocket_sound.set_volume(0.2)
        self.score = 0
        self.fire_timer = time.time()
        self.player_speed = player_speed

    def move(self):
        key = pygame.key.get_pressed()
        # движение
        if key[pygame.K_LEFT] and self.rect.x >= 0:
            self.rect.x -= self.player_speed  # Используем скорость игрока
            self.image = self.player_pos[0]
        if key[pygame.K_RIGHT] and self.rect.x <= 400:
            self.rect.x += self.player_speed  # Используем скорость игрока
            self.image = self.player_pos[1]
        # конечное пространство
        if self.rect.x < 0:
            self.rect.x = 400
        if self.rect.x > 400:
            self.rect.x = 0
        # прыжок
        if key[pygame.K_SPACE] and self.rect.bottom >= 800:
            self.gravity = -20
            self.jump_sound.play()

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 800:
            self.rect.bottom = 800

    def collisions(self):
        # столкновение с платформами
        global platforms_group
        dy = self.gravity
        s = 0
        collision = False

        for platform in platforms_group:

            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, 60, 60):
                if self.rect.bottom <= platform.rect.centery:
                    if self.gravity > 0:
                        collision = True
                        self.jump_sound.play()
                        dy = 0
                        self.gravity = -20

                        # Обрабатывать нарушенную логику платформы
                        if platform.type == 'Brown':
                            image = pygame.image.load('brplatbr.png').convert_alpha()
                            platform.image = pygame.transform.scale(image, (80, 20))
                            type = random.randint(0, 2)
                            x = random.randint(0, 3)
                            y = -800 / max_platforms
                            image_name = images[type]
                            platform_type = platform_types[type]
                            platforms_group.add(Platform(x, y, image_name, platform_type))
                            platform.kill()

        # s stands for scroll
        if self.rect.y <= 500:
            if self.gravity < 0:
                s = -dy
        # столкновение с ускорителем
        rocket_start = time.time()
        global booster
        for booster in boosters:
            if booster.rect.colliderect(self.rect.x, self.rect.y + dy, 60, 60):
                with_rocket = pygame.image.load('with_r.png').convert_alpha()
                self.image = pygame.transform.scale(with_rocket, (60, 60))
                self.gravity -= 100
                rocket_start = time.time()
                self.rocket_sound.play()
                booster.kill()
        # проверка, достаточно ли топлива для полета
        if time.time() - rocket_start > 4:
            self.image = self.player_pos[0]
        # столкновение с монстрами
        global game_active
        for monster in monsters:
            if monster.rect.colliderect(self.rect.x, self.rect.y + dy, 50, 50):
                game_active = False
        # возвращает переменную прокрутки на экран обновления
        return s

    def fire(self):
        key = pygame.key.get_pressed()
        global bullets
        # движение
        if key[pygame.K_UP]:
            self.image = self.player_pos[2]
            if time.time() - self.fire_timer > 0.5:
                self.fire_timer = time.time()
                bullets.add(Bullet(self.rect.x, self.rect.y + 5, 'bullet.png'))

    def draw(self, screen):
        screen.blit(pygame.transform.scale(self.image, (60, 60)), (self.rect.x - 12, self.rect.y - 5))
        pygame.draw.rect(screen, (255, 255, 255), self.rect, -1)

    def update(self, scroll):
        self.collisions()
        self.move()
        self.apply_gravity()
        self.fire()
        # self.draw(screen) - отрисовка перенесена в основной цикл
        self.rect.y += scroll
        if self.score < self.score - self.gravity and self.gravity < 0:
            self.score -= self.gravity

# Класс для ускорителей
class Boosters(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        rocket_image = pygame.image.load('jetpack.png').convert_alpha()
        rocket = pygame.transform.scale(rocket_image, (40, 40))
        self.image = rocket
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def move(self):
        self.rect.y += scroll
        if self.rect.y == 700:
            self.kill()

    def update(self):
        self.move()

# Класс для платформ
class Platform(pygame.sprite.Sprite):
    # 3 типа платформ: статическая (green), движущаяся (blue), сломанная (brown)
    def __init__(self, x, y, image_name, type):
        super().__init__()
        image = pygame.image.load(image_name).convert_alpha()
        self.image = pygame.transform.scale(image, (80, 20))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.type = type
        self.change_x = 1

    def update(self, scroll):
        self.rect.y += scroll
        if self.type == 'Blue':
            if self.rect.x >= 320 or self.rect.x <= 0:
                self.change_x *= -1
            self.rect.x += self.change_x
        else:
            pass

# Класс для монстров
class Monster(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        if type == 'OneEyed':
            monster_1 = pygame.image.load('red.png').convert_alpha()
            self.image = pygame.transform.scale(monster_1, (80, 80))
        elif type == 'LargeBlue':
            monster_2 = pygame.image.load('Blue.png').convert_alpha()
            self.image = pygame.transform.scale(monster_2, (80, 80))
        elif type == 'ButterFly':
            monster_3 = pygame.image.load('Green.png').convert_alpha()
            self.image = pygame.transform.scale(monster_3, (80, 80))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # для движения
        self.pos_change = 0
        self.dx = 1

    # проверьте, нет ли столкновения с пулями
    def dodging_from_bullets(self):
        global bullets
        for bullet in bullets:
            if bullet.rect.colliderect(self.rect.x, self.rect.y, 80, 80):
                self.kill()

    def move(self):
        global scroll
        if self.pos_change < 40:
            self.rect.x += self.dx
            self.pos_change += 1
        else:
            self.dx = -self.dx
            self.pos_change = 0
        self.rect.y += scroll
        if self.rect.y == 700:
            self.kill()

    def update(self):
        self.move()
        self.dodging_from_bullets()


# создать фон
def draw_background(screen, background):
    screen.blit(background, (0, 0))
    screen.blit(background, (0, 800))


def display_score(player, test_font, screen):
    # глобальное время остановки
    # player.score = int(pygame.time.get_ticks() / 1000) - start - stop_time
    player.score += player.collisions()
    score_surf = test_font.render('Счёт: {}'.format(player.score), False, (0, 0, 0))
    score_rect = score_surf.get_rect(center=(320, 20))
    screen.blit(score_surf, score_rect)
    return player.score


# Начальная настройка игры
def floor_collision(player):
    global game_active
    if player.rect.y >= 750:
        game_active = False


# обновление группы платформ при изменении фона
def update_platforms(platforms_group, platform_types, images, boosters, max_platforms):
    global rocket_x, rocket_y
    for platform in platforms_group:
        if platform.rect.y >= 800:
            platform.kill()
    if len(platforms_group) < max_platforms:
        type = np.random.randint(0, 3, max_platforms)
        x = np.random.randint(0, 320, max_platforms)
        y = np.arange(-800, 0, 800 / max_platforms)
        rocket_index = random.randint(max_platforms, 2 * max_platforms)
        for i in range(1, len(type) - 1):
            if type[i] == 2 and type[i] == type[i + 1] and type[i] == type[i - 1]:
                type[i] = random.randint(0, 1)
        for i in range(len(type)):
            platforms_group.add(Platform(x[i], y[i], images[type[i]], platform_types[type[i]]))
            if i == rocket_index and type[i] == 0:
                rocket_x = x[i]
                rocket_y = y[i]
                boosters.add(Boosters(rocket_x, rocket_y - 20))

# Функция для спавна монстров
def spawn_monsters():
    global monsters, monster_types, monster_timer
    if time.time() - monster_timer > 30:
        monster_timer = time.time()
        m_type = random.randint(0, 2)
        m_x = random.randint(0, 320)
        m_y = random.randint(0, 700)
        monsters.add(Monster(m_x, m_y, monster_types[m_type]))

# Функция для обработки паузы
def catch_pause():
    key = pygame.key.get_pressed()
    global pause, game_active
    if key[pygame.K_p]:
        pause = True
        game_active = False

# Функция для возобновления игры
def catch_continue():
    key = pygame.key.get_pressed()
    global pause, game_active, saved, loaded
    if key[pygame.K_c]:
        pause = False
        game_active = True
        saved = False
        loaded = False

# Функция для сохранения игры
def catch_save(player,test_font,screen):
    key = pygame.key.get_pressed()
    global saved
    if key[pygame.K_s]:
        data = player.score
        with open("savegame", "wb") as f:
            pickle.dump(data, f)
        saved = True

# Функция для загрузки игры
def load():
    global loaded
    try:
        with open('savegame', "rb") as f:
            data = pickle.load(f)
            return data, True #Return also True if the file is loaded
    except FileNotFoundError:
        print("Сохранение не найдено")
        return 0, False #Return 0 and False if the file is not loaded

# Функция для выбора сложности
def choose_difficulty(screen, background, clock, test_font):
    global difficulty, player_speed

    difficulty = "Easy"
    player_speed = 10  # Default player speed

    easy_text = test_font.render("1. Легко", True, (0, 0, 0))
    easy_rect = easy_text.get_rect(center=(200, 200))
    medium_text = test_font.render("2. Средне", True, (0, 0, 0))
    medium_rect = medium_text.get_rect(center=(200, 250))
    hard_text = test_font.render("3. Сложно", True, (0, 0, 0))
    hard_rect = hard_text.get_rect(center=(200, 300))
    info_text = test_font.render("Выберите сложность:", True, (0, 0, 0))
    info_rect = info_text.get_rect(center=(200, 150))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    difficulty = "Easy"
                    player_speed = 8  # Уменьшение скорости для легкой сложности
                    waiting = False
                if event.key == pygame.K_2:
                    difficulty = "Medium"
                    player_speed = 12  # Увеличение скорости для средней сложности
                    waiting = False
                if event.key == pygame.K_3:
                    difficulty = "Hard"
                    player_speed = 16  # Увеличение скорости для сложной сложности
                    waiting = False
        screen.blit(background, (0, 0))
        screen.blit(easy_text, easy_rect)
        screen.blit(medium_text, medium_rect)
        screen.blit(hard_text, hard_rect)
        screen.blit(info_text, info_rect)
        pygame.display.update()
        clock.tick(60)

    print(f"Выбранная сложность: {difficulty} (Скорость: {player_speed})")
    return player_speed  # Return the selected player_speed


if __name__ == "__main__":

    pygame.init()
    screen = pygame.display.set_mode((400, 800))
    pygame.display.set_caption('Geometry_Jump')
    clock = pygame.time.Clock()
    test_font = pygame.font.Font(None, 30)
    running = True #The game loop runs with True

    while running:
        # Here we set all the global variables (because the game will reset)
        game_active = False
        pause = False
        loaded = False
        saved = False
        start_time = 0
        scroll = 0
        score = 0
        max_platforms = 15
        # Difficulty
        player_speed = 10  # Initial speed
        # Background
        background_pos = 0
        background = pygame.image.load('Site-background-light.png').convert()
        #Initial screen
        doodle = pygame.image.load('right.png').convert_alpha()
        doodle_rect = doodle.get_rect(midbottom=(200, 800))

        game_name = test_font.render('Geometry Jump', False, (0, 0, 0))
        game_name_rect = game_name.get_rect(center=(200, 150))

        game_message = test_font.render('Нажмите пробел, чтобы начать игру', False, (0, 0, 0))
        message_space = game_message.get_rect(center=(200, 450))
        game_message_left = test_font.render('Нажмите стрелку вправо, чтобы переместиться влево', False, (0, 0, 0))
        message_left = game_message.get_rect(center=(150, 500))
        game_message_right = test_font.render('Нажмите l, чтобы загрузить сохраненние', False, (0, 0, 0))
        message_right = game_message.get_rect(center=(150, 550))
        game_message_load = test_font.render('', False, (0, 0, 0))
        message_load = game_message.get_rect(center=(150, 350))
        game_message_pause = test_font.render('Нажмите p для паузы', False, (0, 0, 0))
        message_pause = game_message.get_rect(center=(200, 400))
        #Here is the code to set everything on the screen, I create a different event because is for the main menu
        while not game_active:
            screen.blit(background, (0, 0))
            screen.blit(doodle, doodle_rect)
            screen.blit(game_name, game_name_rect)
            screen.blit(game_message, message_space)
            screen.blit(game_message_left, message_left)
            screen.blit(game_message_right, message_right)
            screen.blit(game_message_load, message_load)
            screen.blit(game_message_pause, message_pause)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        #After pressing on SPACE the difficulty is choosen, and the game starts directly
                        player_speed = choose_difficulty(screen, background, clock, test_font)
                        player = Player(player_speed)
                    #Игрок
                        bullets = pygame.sprite.Group()

                        # Стартовая платформа
                        platforms_group = pygame.sprite.Group()
                        platform = platforms_group.add(Platform(150, 730, 'grplat.png', 'Green'))
                        platform_types = ['Green', 'Blue', 'Brown']
                        images = ['grplat.png',
                                  'blplat.png',
                                  'brplat.png']

                        # Монстры
                        monster_timer = time.time()
                        monsters = pygame.sprite.Group()
                        monster_types = ['OneEyed', 'LargeBlue', 'ButterFly']
                        for i in range(1, max_platforms):
                            type = random.randint(0, 2)
                            x = random.randint(0, 320)
                            y = 600 / max_platforms * i
                            platforms_group.add(Platform(x, y, images[type], platform_types[type]))

                        # Усилитель
                        boosters = pygame.sprite.Group()
                        running = True
                        game_active = True #That should be working, not tested yet
                        break #Select a value and enter the main game section, to create the platforms

                    if event.key == pygame.K_l:
                        #If the game loads we do a similar proccess.
                        var_load, is_loaded = load()
                        if (is_loaded):
                            #Then the player and the loaded parameters will load correctly.
                            player_speed = choose_difficulty(screen, background, clock, test_font)
                            player = Player(player_speed) #After loading the game the score should be the previous
                            player.score = var_load
                            #Игрок
                            bullets = pygame.sprite.Group()

                            # Стартовая платформа
                            platforms_group = pygame.sprite.Group()
                            platform = platforms_group.add(Platform(150, 730, 'grplat.png', 'Green'))
                            platform_types = ['Green', 'Blue', 'Brown']
                            images = ['grplat.png',
                                      'blplat.png',
                                      'brplat.png']

                            # Монстры
                            monster_timer = time.time()
                            monsters = pygame.sprite.Group()
                            monster_types = ['OneEyed', 'LargeBlue', 'ButterFly']
                            for i in range(1, max_platforms):
                                type = random.randint(0, 2)
                                x = random.randint(0, 320)
                                y = 600 / max_platforms * i
                                platforms_group.add(Platform(x, y, images[type], platform_types[type]))

                            # Усилитель
                            boosters = pygame.sprite.Group()
                            running = True
                            game_active = True #That should be working, not tested yet
                            choose = True #Sets to true to run the game code
                            loaded = True #If its loaded is because the variable should be setted to TRUE
                            break #break to avoid load the next game.

        bg_music = pygame.mixer.Sound('gdmus.mp3')
        bg_music.play(loops=-1)
        bg_music.set_volume(0.2)

        while game_active: #While this runs and not stops (and doesn't press the X button the game will go normally
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                    break

            # Отрисовка фона каждый кадр
            draw_background(screen, background)
            score = display_score(player, test_font, screen)

            # Вызов update для player и спрайтов
            scroll = player.collisions()
            player.update(scroll)
            platforms_group.update(scroll)
            monsters.update()
            bullets.update()
            boosters.update()
            floor_collision(player)

            # Отрисовка спрайтов после обновления
            player.draw(screen)
            platforms_group.draw(screen)
            monsters.draw(screen)
            bullets.draw(screen)
            boosters.draw(screen)

            update_platforms(platforms_group, platform_types, images, boosters, max_platforms)
            spawn_monsters()

            catch_pause()
            pygame.display.update()
            clock.tick(55)

        # Game over! When gets out the game loop is because one of the 2 options are setted on false
        #Then we should clear all variables for the game run and run
        bg_music.stop()
        bullets = pygame.sprite.Group()
        monsters = pygame.sprite.Group()
        boosters = pygame.sprite.Group()
        platforms_group = pygame.sprite.Group()
        #Sets here all settings again,

pygame.quit()
sys.exit()