import random
import sys
import time
import pygame


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
        if self.rect.y < 0:  # Пуля уходит с экрана
            self.kill()


class Player:
    def __init__(self, difficulty):
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
        self.rect.center = (150, 750)  # Начальная позиция
        self.gravity = 0
        self.jump_sound = pygame.mixer.Sound('jump.wav')
        self.jump_sound.set_volume(0.5)
        self.rocket_sound = pygame.mixer.Sound('rocket.mp3')
        self.rocket_sound.set_volume(0.5)
        self.score = 0
        self.fire_timer = time.time()
        self.max_height = 750  # Максимальная высота
        self.difficulty = difficulty
        self.speed = 5 + difficulty * 2  # Скорость зависит от сложности
        self.jump_power = -20  # Сила прыжка
        self.horizontal_speed = 10 + difficulty * 2
        self.rocket_duration = 4  # Длительность ракеты
        self.rocket_boost = -100  # Сила ракеты
        self.last_platform = None  # Последняя платформа, с которой спрыгнули

    def move(self):
        key = pygame.key.get_pressed()
        # движение
        if key[pygame.K_LEFT]:
            self.rect.x -= self.horizontal_speed  # Движение влево
            self.image = self.player_pos[0]
        if key[pygame.K_RIGHT]:
            self.rect.x += self.horizontal_speed  # Движение вправо
            self.image = self.player_pos[1]

        # Перенос с края на край экрана
        if self.rect.x < 0:
            self.rect.x = 400 - self.rect.width
        if self.rect.x > 400 - self.rect.width:
            self.rect.x = 0

        # прыжок
        if key[pygame.K_SPACE] and self.on_ground():
            self.gravity = self.jump_power
            self.jump_sound.play()

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 800:
            self.rect.bottom = 800
            self.gravity = 0  # Обнуляем гравитацию на земле

    def on_ground(self):
        return self.rect.bottom >= 800 or any(
            platform.rect.colliderect(self.rect.x, self.rect.bottom, self.rect.width, 1)
            for platform in platforms_group
        )

    def collisions(self):
        global platforms_group
        dy = self.gravity
        s = 0
        collision = False

        for platform in platforms_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.rect.bottom <= platform.rect.centery and self.gravity > 0:
                    collision = True
                    self.jump_sound.play()
                    dy = 0
                    self.gravity = self.jump_power
                    if platform.type == 'Brown':
                        platform.start_destroy()

                    # Увеличиваем счёт, если это новая платформа
                    if platform != self.last_platform:
                        self.score += 1
                        self.last_platform = platform  # Запоминаем эту платформу

        # Прокрутка экрана
        if self.rect.y <= 500:
            if self.gravity < 0:
                s = -dy

        global booster
        for booster in boosters:
            if booster.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                with_rocket = pygame.image.load('with_r.png').convert_alpha()
                self.image = pygame.transform.scale(with_rocket, (60, 60))
                self.gravity = self.rocket_boost  # Увеличиваем гравитацию для ракеты
                self.rocket_start = time.time()
                self.rocket_sound.play()
                booster.kill()
                break

        if hasattr(self, 'rocket_start') and time.time() - self.rocket_start > self.rocket_duration:
            self.image = self.player_pos[1]  # Возвращаем стандартный спрайт

        global game_active
        for monster in monsters:
            if monster.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                game_active = False

        return s

    def fire(self):
        key = pygame.key.get_pressed()
        global bullets
        if key[pygame.K_UP]:
            self.image = self.player_pos[2]
            if time.time() - self.fire_timer > 0.5:
                self.fire_timer = time.time()
                bullets.add(Bullet(self.rect.x + self.rect.width // 2 - 7, self.rect.y, 'bullet.png'))

    def draw(self, screen):
        screen.blit(pygame.transform.scale(self.image, (60, 60)), (self.rect.x - 5, self.rect.y - 5))

    def update(self, scroll):
        self.collisions()
        self.move()
        self.apply_gravity()
        self.fire()
        self.rect.y += scroll

        if self.rect.y < self.max_height:
            self.max_height = self.rect.y


class Boosters(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        rocket_image = pygame.image.load('jetpack.png').convert_alpha()
        rocket = pygame.transform.scale(rocket_image, (40, 40))
        self.image = rocket
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        self.rect.y += scroll
        if self.rect.top > 800:
            self.kill()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, image_name, type):
        super().__init__()
        self.original_image = pygame.image.load(image_name).convert_alpha()
        if type == 'Blue':  # Синие платформы во всю ширину
            self.image = pygame.transform.scale(self.original_image, (80, 20))
        else:
            self.image = pygame.transform.scale(self.original_image, (80, 20))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.type = type
        self.change_x = 2  # Скорость синей платформы
        self.destroying = False
        self.destroy_frame = 0
        self.destroy_images = []
        for i in range(1, 5):
            img = pygame.image.load(f'brplatbr.png').convert_alpha()
            self.destroy_images.append(pygame.transform.scale(img, (80, 20)))

    def start_destroy(self):
        if self.type == 'Brown':
            self.destroying = True
            self.destroy_frame = 0

    def update(self, scroll, game_speed):
        self.rect.y += scroll
        if self.type == 'Blue':
            self.rect.x += self.change_x
            if self.rect.x <= 0:
                self.change_x = abs(self.change_x)
            elif self.rect.x + self.rect.width >= 400:
                self.change_x = -abs(self.change_x)
        if self.destroying:
            if self.destroy_frame < len(self.destroy_images):
                self.image = self.destroy_images[self.destroy_frame]
                self.destroy_frame += 1
            else:
                self.kill()


class Monster(pygame.sprite.Sprite):
    def __init__(self, x, y, type, game_speed):  # Добавлена скорость игры
        super().__init__()
        if type == 'OneEyed':
            monster_1 = pygame.image.load('red.png').convert_alpha()
            self.image = pygame.transform.scale(monster_1, (70, 70))  # Размеры монстра
        elif type == 'LargeBlue':
            monster_2 = pygame.image.load('Blue.png').convert_alpha()
            self.image = pygame.transform.scale(monster_2, (70, 70))  # Размеры монстра
        elif type == 'ButterFly':
            monster_3 = pygame.image.load('Green.png').convert_alpha()
            self.image = pygame.transform.scale(monster_3, (70, 70))  # Размеры монстра
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.pos_change = 0
        self.dx = 1 + game_speed  # Скорость зависит от игры
        self.game_speed = game_speed

    def dodging_from_bullets(self):
        global bullets
        for bullet in bullets:
            if bullet.rect.colliderect(self.rect.x, self.rect.y, 70, 35):
                self.kill()
                bullet.kill()  # Убиваем пулю

    def update(self, scroll):
        if self.pos_change < 40:
            self.rect.x += self.dx
            self.pos_change += 1
        else:
            self.dx = -self.dx
            self.pos_change = 0

        self.rect.y += scroll
        if self.rect.top > 800:
            self.kill()

        self.dodging_from_bullets()


def draw_background(screen, background):
    screen.blit(background, (0, 0))
    screen.blit(background, (0, 0))


def display_score(screen, font, score):
    score_surf = font.render('Счёт: {}'.format(score), False, (0, 0, 0))
    score_rect = score_surf.get_rect(center=(320, 20))
    screen.blit(score_surf, score_rect)
    return score


def floor_collision(player):
    if player.rect.y >= 750:
        return True
    return False


def update_platforms(platforms_group, platform_types, images, boosters, difficulty, game_speed):
    platform_gap = 800 // max_platforms
    # Удаляем платформы за экраном
    for platform in list(platforms_group):
        if platform.rect.top > 800:
            platforms_group.remove(platform)

    # Добавляем платформы чтобы было нужное кол-во
    while len(platforms_group) < max_platforms:
        last_platform_y = 0
        if platforms_group:
            last_platform_y = min(platform.rect.y for platform in platforms_group)

        y = last_platform_y - platform_gap
        platform_type_index = random.randint(0, 2)
        image_name = images[platform_type_index]
        platform_type = platform_types[platform_type_index]

        # Синие платформы всегда во всю ширину
        if platform_type == 'Blue':
            x = 0  # Всегда слева
        else:
            x = random.randint(0, 320)

        new_platform = Platform(x, y, image_name, platform_type)
        platforms_group.add(new_platform)

        # Рандомно добавляем ракету - Реже
        if random.random() < 0.05:  # Вероятность
            boosters.add(Boosters(x, y - 20))


def spawn_monsters(monsters, monster_types, monster_timer, game_speed):
    if time.time() - monster_timer > 5 - game_speed:
        m_type = random.randint(0, 2)
        m_x = random.randint(0, 320)
        m_y = -50  # Над экраном
        monster = Monster(m_x, m_y, monster_types[m_type], game_speed)
        monsters.add(monster)
        return time.time()  # Перезапускаем таймер
    return monster_timer


def display_win_screen(screen, font, score):
    screen.fill((0, 0, 0))
    win_text = font.render("Ты выйграл!", True, (255, 255, 255))
    score_text = font.render(f"Финальный счёт: {score}", True, (255, 255, 255))
    restart_text = font.render("Нажми SPACE чтобы начать заного", True, (255, 255, 255))

    win_rect = win_text.get_rect(center=(400 // 2, 800 // 4))
    score_rect = score_text.get_rect(center=(400 // 2, 800 // 2))
    restart_rect = restart_text.get_rect(center=(400 // 2, 800 * 3 // 4))

    screen.blit(win_text, win_rect)
    screen.blit(score_text, score_rect)
    screen.blit(restart_text, restart_rect)


# Выбор сложности
def show_difficulty_screen(screen, font):
    screen.fill((0, 0, 0))  # Чёрный фон
    title_text = font.render("Выбери сложность", True, (255, 255, 255))
    easy_text = font.render("1. Лёгкий", True, (0, 255, 0))
    medium_text = font.render("2. Средний", True, (255, 255, 0))
    hard_text = font.render("3. Сложный", True, (255, 0, 0))

    title_rect = title_text.get_rect(center=(400 // 2, 800 // 6))
    easy_rect = easy_text.get_rect(center=(400 // 2, 800 // 3))
    medium_rect = medium_text.get_rect(center=(400 // 2, 800 // 2))
    hard_rect = hard_text.get_rect(center=(400 // 2, 800 * 2 // 3))

    screen.blit(title_text, title_rect)
    screen.blit(easy_text, easy_rect)
    screen.blit(medium_text, medium_rect)
    screen.blit(hard_text, hard_rect)

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 1  # Лёгкий
                elif event.key == pygame.K_2:
                    return 2  # Средний
                elif event.key == pygame.K_3:
                    return 3  # Сложный
        pygame.time.Clock().tick(60)  # FPS


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((400, 800))
    pygame.display.set_caption('Geometry_Jump')
    clock = pygame.time.Clock()
    test_font = pygame.font.Font(None, 30)

    # Состояния игры
    game_active = False  # Игра активна
    pause = False  # Игра на паузе
    loaded = False  # Загружено сохранение
    saved = False  # Игра сохранена
    win = False  # Игра выйграна
    start_time = 0  # Время начала
    scroll = 0  # Прокрутка
    score = 0  # Счет

    max_platforms = 10  # Кол-во платформ

    # Музыка
    bg_music = pygame.mixer.Sound('gdmus.mp3')
    bg_music.play(loops=-1)
    bg_music.set_volume(0.2)

    # Фон
    background = pygame.image.load('Site-background-light.png').convert()

    # Загрузка картинок проигрыша и выигрыша
    lose_image = pygame.image.load('lose.png').convert_alpha()  # Загрузка картинки проигрыша
    lose_image = pygame.transform.scale(lose_image, (400, 800))  # Растягиваем на весь экран

    win_image = pygame.image.load('win.png').convert_alpha()  # Загружаем картинку выигрыша
    win_image = pygame.transform.scale(win_image, (400, 800))  # resize win image

    lose_image_rect = lose_image.get_rect()  # Получаем прямоугольник
    win_image_rect = win_image.get_rect()  # Получаем прямоугольник

    lose_image_duration = 5  # Длительность отображения картинки проигрыша (в секундах)
    win_image_duration = 5  # Длительность отображения картинки выигрыша (в секундах)

    lose_image_start_time = 0  # Время начала отображения картинки проигрыша
    win_image_start_time = 0  # Время начала отображения картинки выигрыша

    # Списки
    platform_types = ['Green', 'Blue', 'Brown']
    images = ['grplat.png', 'blplat.png', 'brplat.png']
    monster_types = ['OneEyed', 'LargeBlue', 'ButterFly']

    # Начальный экран
    doodle = pygame.image.load('right.png').convert_alpha()
    doodle_rect = doodle.get_rect(midbottom=(200, 750))  #Позиция

    game_name = test_font.render('Geometry Jump', False, (0, 0, 0))
    game_name_rect = game_name.get_rect(center=(200, 150))

    game_message = test_font.render('Нажми SPACE чтобы начать', False, (0, 0, 0))
    message_space = game_message.get_rect(center=(200, 450))
    game_message_left = test_font.render('Используй стрелки для движения', False, (0, 0, 0))
    message_left = game_message.get_rect(center=(200, 500))
    game_message_right = test_font.render('Нажми L чтобы загрузить сохранение', False, (0, 0, 0))
    message_right = game_message.get_rect(center=(200, 550))
    game_message_pause = test_font.render('Нажми P чтобы поставить паузу', False, (0, 0, 0))
    message_pause = game_message.get_rect(center=(200, 400))

    # Игровой цикл
    difficulty = show_difficulty_screen(screen, test_font)
    game_speed = difficulty * 0.5  # Скорость зависит от сложности

    # Инициализация групп
    platforms_group = pygame.sprite.Group()
    boosters = pygame.sprite.Group()
    monsters = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    player = Player(difficulty)

    # Стартовая платформа
    start_platform = Platform(150, 730, 'grplat.png', 'Green')  # Создаём
    platforms_group.add(start_platform)  # Добавляем

    #Ставим игрока на платформу
    player.rect.bottom = start_platform.rect.top  #Позиция

    monster_timer = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # KEYDOWN events for more reliable pausing/resuming
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l and not game_active and not pause:
                    try:
                        score = player.score
                        loaded = True
                    except FileNotFoundError:
                        print("Сохранение не найдено.")
                elif event.key == pygame.K_SPACE and not game_active and (
                        not pause or win_image_start_time > 0 or lose_image_start_time > 0):
                    if not loaded:
                        player.score = 0
                        score = 0
                        start_time = int(pygame.time.get_ticks() / 1000)
                    else:
                        loaded = False  # Сброс загрузки
                    win = False  # Сброс выйгрыша
                    game_active = True  # Игра активна
                    player = Player(difficulty)  # Создаём игрока
                    monsters = pygame.sprite.Group()  # Монстры
                    platforms_group = pygame.sprite.Group()  # Платформы
                    boosters = pygame.sprite.Group()  # Ускорители
                    start_platform = Platform(150, 730, 'grplat.png', 'Green')
                    platforms_group.add(start_platform)
                    player.rect.bottom = start_platform.rect.top  #Опять на платформу
                    monster_timer = time.time()  # Таймер монстров
                    lose_image_start_time = 0  # Сброс Таймер проигрыша
                    win_image_start_time = 0  # Сброс таймера выигрыша
                # Pause the game
                elif event.key == pygame.K_p:
                    pause = not pause  # Переключение паузы

        #Drawing functions.
        if game_active and not pause:  # Если игра активна и не на паузе
            draw_background(screen, background)  # Рисуем фон
            scroll = player.collisions()  # Прокручиваем экран
            player.update(scroll)  # Обновляем игрока

            # Условие выйгрыша
            if player.score >= 5000:
                score = player.score  # Текущий счет
                game_active = False  # Игра не активна
                win = True  # Выйгрыш
                win_image_start_time = time.time()  # Ставим таймер

            # Обновление объектов
            for platform in platforms_group:  # Для каждой платформы
                platform.update(scroll, game_speed)  # Обновляем платформу
            for booster in boosters:  # Для каждого ускорителя
                booster.update(scroll)  # Обновляем ускоритель
            monster_timer = spawn_monsters(monsters, monster_types, monster_timer,
                                           game_speed)  # Обновляем таймер монстров
            for monster in monsters:  # Для каждого монстра
                monster.update(scroll)  # Обновляем монстра

            # Обновление и удаление платформ
            update_platforms(platforms_group, platform_types, images, boosters, difficulty,
                             game_speed)  # Обновляем платформы

            for bullet in list(bullets):  # Для каждой пули
                bullet.update()  # Обновляем пулю
                if bullet.rect.bottom < 0:  # Если пуля ушла за экран
                    bullets.remove(bullet)  # Удаляем пулю

            # Коллизия с полом
            if floor_collision(player):  # Если игрок упал
                game_active = False  # Игра не активна
                pause = False  # Пауза не активна
                lose_image_start_time = time.time()  # Ставим таймер проигрыша
                win = False  # Убираем выйгрыш

            # Отрисовка
            display_score(screen, test_font, player.score)  # Отображаем счет
            player.draw(screen)  # Рисуем игрока
            platforms_group.draw(screen)  # Рисуем платформы
            boosters.draw(screen)  # Рисуем ускорители
            monsters.draw(screen)  # Рисуем монстров
            bullets.draw(screen)  # Рисуем пули


        elif pause:  # Если на паузе
            screen.blit(background, (0, 0))  # Рисуем фон
            screen.blit(doodle, doodle_rect)  # Рисуем дудл

            score_message = test_font.render(f'Твой счёт: {score}', False, (0, 0, 0))  # Отображаем счет
            score_message_rect = score_message.get_rect(center=(200, 375))
            screen.blit(score_message, score_message_rect)
            pause_message = test_font.render('Пауза - Нажми P чтобы продолжить', False, (0, 0, 0))  # Сообщение паузы
            pause_message_rect = pause_message.get_rect(center=(200, 475))
            screen.blit(pause_message, pause_message_rect)
        # Отображаем экраны проигрыша и выйгрыша
        elif lose_image_start_time > 0 and time.time() - lose_image_start_time <= lose_image_duration:  # Если проиграл и таймер еще не вышел
            # Рисуем экран проигрыша ограниченное время
            screen.blit(lose_image, (0, 0))
        elif win_image_start_time > 0 and time.time() - win_image_start_time <= win_image_duration:  # Если выйграл и таймер еще не вышел
            # Рисуем экран выйгрыша ограниченное время
            screen.blit(win_image, (0, 0))


        else:  # Начальный экран
            screen.blit(background, (0, 0))  # Рисуем фон
            screen.blit(doodle, doodle_rect)  # Рисуем дудл

            if score == 0:  # Если счет 0
                screen.blit(game_name, game_name_rect)  # Рисуем название игры
                screen.blit(game_message, message_space)  # Рисуем сообщение
                screen.blit(game_message_left, message_left)  # Рисуем сообщение
                screen.blit(game_message_right, message_right)  # Рисуем сообщение
                screen.blit(game_message_pause, message_pause)  # Рисуем сообщение
            else:  # Если счет не 0
                score_message = test_font.render(f'Твой счёт: {score}', False, (0, 0, 0))  # Отображаем счет
                score_message_rect = score_message.get_rect(center=(200, 375))
                screen.blit(score_message, score_message_rect)

            # Очистка списков
            for monster in monsters:  # Для каждого монстра
                monster.kill()  # Убиваем монстра
            for platform in platforms_group:  # Для каждой платформы
                platform.kill()  # Убиваем платформу
            for booster in boosters:  # Для каждого бустера
                booster.kill()  # Убиваем бустер
            for bullet in bullets:  # Для каждой пули
                bullet.kill()  # Убиваем пулю

        pygame.display.update()
        clock.tick(60)  # 60 FPS
