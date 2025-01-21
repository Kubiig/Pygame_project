import pygame
import random

# Инициализация Pygame.
pygame.init()

# Константы.
WIDTH, HEIGHT = 400, 600
FPS = 60
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 50
PLATFORM_WIDTH, PLATFORM_HEIGHT = 80, 10
GRAVITY = 0.5
JUMP_STRENGTH = -10

# Цвета.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Настройка экрана.
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Doodle Jump")
clock = pygame.time.Clock()

# Шрифт для текста.
font = pygame.font.Font(None, 36)

# Класс игрока.
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Загрузка изображения вместо прямоугольника.
        self.image = pygame.image.load("player.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (PLAYER_WIDTH, PLAYER_HEIGHT))  # Масштабирование изображения.
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.vel_y = 0
        self.alive = True  # Флаг, чтобы отслеживать, жив ли игрок.
    def update(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Ограничение движения игрока по горизонтали.
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= 5
        if keys[pygame.K_RIGHT]:
            self.rect.x += 5

        # Цикличное движение через края экрана.
        if self.rect.left > WIDTH:
            self.rect.right = 0
        elif self.rect.right < 0:
            self.rect.left = WIDTH

        # Если игрок падает ниже экрана, он умирает.
        if self.rect.top > HEIGHT:
            self.alive = False

    def jump(self):
        self.vel_y = JUMP_STRENGTH


# Класс обычной платформы.
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


# Класс платформы, которая ломается.
class BreakablePlatform(Platform):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(RED)
        self.is_broken = False

    def break_platform(self):
        self.is_broken = True
        self.kill()


# Функция для перезапуска игры.
def restart_game():
    global all_sprites, platforms, player
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    # Создание игрока.
    player = Player()
    all_sprites.add(player)

    # Создание начальных платформ.
    for i in range(6):
        x = random.randint(0, WIDTH - PLATFORM_WIDTH)
        y = random.randint(i * HEIGHT // 6, (i + 1) * HEIGHT // 6)
        if random.random() > 0.7:  # 30% шанс на создание ломаемой платформы.
            platform = BreakablePlatform(x, y)
        else:
            platform = Platform(x, y)
        all_sprites.add(platform)
        platforms.add(platform)


# Отображение экрана "Game Over".
def game_over_screen():
    screen.fill(WHITE)
    text = font.render("Game Over", True, BLACK)
    restart_text = font.render("Restart", True, WHITE)
    restart_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2, 100, 50)

    # Рисуем текст и кнопку.
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
    pygame.draw.rect(screen, BLUE, restart_button)
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    waiting = False


# Запуск игры.
restart_game()

# Основной игровой цикл.
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление.
    all_sprites.update()

    # Проверка на столкновение с платформами.
    if player.vel_y > 0:
        hits = pygame.sprite.spritecollide(player, platforms, False)
        if hits:
            platform_hit = hits[0]
            player.rect.bottom = platform_hit.rect.top
            player.jump()

            # Если это ломаемая платформа, она ломается.
            if isinstance(platform_hit, BreakablePlatform):
                platform_hit.break_platform()

    # Если игрок умер, показать экран "Game Over".
    if not player.alive:
        game_over_screen()
        restart_game()

    # Отрисовка.
    screen.fill(WHITE)
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()