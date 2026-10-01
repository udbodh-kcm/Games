
import pygame
import random

pygame.init()

# =========================
# GAME WINDOW
# =========================

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodger-Anjila,Dakshyata")

clock = pygame.time.Clock()


# =========================
# COLORS
# =========================

BLACK = (5, 5, 25)
WHITE = (255, 255, 255)

PINK = (255, 80, 180)
DARK_PINK = (220, 40, 140)

BLUE = (60, 190, 255)

RED = (230, 50, 50)
DARK_RED = (170, 30, 30)

YELLOW = (255, 230, 70)
ORANGE = (255, 150, 30)


# =========================
# PLAYER / SPACESHIP
# =========================

player = pygame.Rect(375, 500, 50, 60)

player_speed = 7


# =========================
# ASTEROIDS
# =========================

asteroids = []

for i in range(6):

    asteroid = {
        "x": random.randint(20, WIDTH - 20),
        "y": random.randint(-700, -50),
        "speed": random.randint(3, 6),
        "size": random.randint(18, 28)
    }

    asteroids.append(asteroid)


# =========================
# STARS
# =========================

stars = []

for i in range(15):

    star = {
        "x": random.randint(10, WIDTH - 10),
        "y": random.randint(-700, HEIGHT),
        "speed": random.randint(2, 5),
        "size": random.randint(5, 10)
    }

    stars.append(star)


# =========================
# SCORE
# =========================

score = 0

font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 60)


# =========================
# GAME STATE
# =========================

running = True
game_over = False


# =========================
# GAME LOOP
# =========================

while running:

    # -------------------------
    # EVENTS
    # -------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # Restart
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r and game_over:

                player.x = 375
                player.y = 500

                score = 0

                game_over = False

                # Reset asteroids
                for asteroid in asteroids:

                    asteroid["x"] = random.randint(
                        20,
                        WIDTH - 20
                    )

                    asteroid["y"] = random.randint(
                        -700,
                        -50
                    )

                # Reset stars
                for star in stars:

                    star["x"] = random.randint(
                        10,
                        WIDTH - 10
                    )

                    star["y"] = random.randint(
                        -700,
                        HEIGHT
                    )


    # =========================
    # GAMEPLAY
    # =========================

    if not game_over:

        # -------------------------
        # PLAYER MOVEMENT
        # -------------------------

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            player.x -= player_speed

        if keys[pygame.K_RIGHT]:
            player.x += player_speed


        # Keep spaceship inside screen

        if player.left < 0:
            player.left = 0

        if player.right > WIDTH:
            player.right = WIDTH


        # =========================
        # MOVE STARS
        # =========================

        for star in stars:

            star["y"] += star["speed"]

            if star["y"] > HEIGHT:

                star["x"] = random.randint(
                    10,
                    WIDTH - 10
                )

                star["y"] = random.randint(
                    -200,
                    -20
                )


        # =========================
        # MOVE ASTEROIDS
        # =========================

        for asteroid in asteroids:

            asteroid["y"] += asteroid["speed"]

            # Asteroid leaves screen

            if asteroid["y"] > HEIGHT + 50:

                asteroid["x"] = random.randint(
                    20,
                    WIDTH - 20
                )

                asteroid["y"] = random.randint(
                    -300,
                    -50
                )

                asteroid["speed"] = random.randint(
                    3,
                    7
                )

                score += 1


            # Asteroid collision

            asteroid_rect = pygame.Rect(
                asteroid["x"] - asteroid["size"],
                asteroid["y"] - asteroid["size"],
                asteroid["size"] * 2,
                asteroid["size"] * 2
            )

            if player.colliderect(asteroid_rect):

                game_over = True


    # =========================
    # DRAW BACKGROUND
    # =========================

    screen.fill(BLACK)


    # =========================
    # DRAW STARS
    # =========================

    for star in stars:

        x = star["x"]
        y = star["y"]
        size = star["size"]

        # Four-point star

        pygame.draw.polygon(
            screen,
            YELLOW,
            [
                (x, y - size),
                (x + size // 3, y - size // 3),
                (x + size, y),
                (x + size // 3, y + size // 3),
                (x, y + size),
                (x - size // 3, y + size // 3),
                (x - size, y),
                (x - size // 3, y - size // 3)
            ]
        )


    # =========================
    # DRAW ASTEROIDS
    # =========================

    for asteroid in asteroids:

        x = asteroid["x"]
        y = asteroid["y"]
        size = asteroid["size"]

        # Main asteroid

        pygame.draw.circle(
            screen,
            RED,
            (x, y),
            size
        )

        # Dark spots

        pygame.draw.circle(
            screen,
            DARK_RED,
            (x - size // 3, y - size // 4),
            size // 4
        )

        pygame.draw.circle(
            screen,
            DARK_RED,
            (x + size // 3, y + size // 4),
            size // 5
        )


    # =========================
    # DRAW PINK SPACESHIP
    # =========================

    # Main body

    pygame.draw.ellipse(
        screen,
        PINK,
        (
            player.x + 8,
            player.y + 5,
            34,
            48
        )
    )


    # Top nose

    pygame.draw.polygon(
        screen,
        PINK,
        [
            (player.centerx, player.y - 5),
            (player.x + 10, player.y + 18),
            (player.right - 10, player.y + 18)
        ]
    )


    # Blue window

    pygame.draw.circle(
        screen,
        BLUE,
        (
            player.centerx,
            player.y + 18
        ),
        9
    )


    # Window shine

    pygame.draw.circle(
        screen,
        WHITE,
        (
            player.centerx - 3,
            player.y + 15
        ),
        3
    )


    # Left wing

    pygame.draw.polygon(
        screen,
        DARK_PINK,
        [
            (player.x + 10, player.y + 32),
            (player.x - 5, player.y + 52),
            (player.x + 15, player.y + 45)
        ]
    )


    # Right wing

    pygame.draw.polygon(
        screen,
        DARK_PINK,
        [
            (player.right - 10, player.y + 32),
            (player.right + 5, player.y + 52),
            (player.right - 15, player.y + 45)
        ]
    )


    # Engine flame

    pygame.draw.polygon(
        screen,
        ORANGE,
        [
            (player.x + 18, player.bottom - 2),
            (player.centerx, player.bottom + 20),
            (player.x + 32, player.bottom - 2)
        ]
    )


    # =========================
    # SCORE
    # =========================

    score_text = font.render(
        "Score: " + str(score),
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (20, 20)
    )


    # =========================
    # GAME OVER
    # =========================

    if game_over:

        game_over_text = big_font.render(
            "GAME OVER",
            True,
            PINK
        )

        restart_text = font.render(
            "Press R to restart",
            True,
            WHITE
        )

        screen.blit(
            game_over_text,
            (300, 250)
        )

        screen.blit(
            restart_text,
            (300, 320)
        )


    # =========================
    # UPDATE SCREEN
    # =========================

    pygame.display.flip()

    clock.tick(60)


pygame.quit()
