#Youtube=Yazılımcı Bey
import pygame, sys, random, math
import data.entities as e
import data.lines as line_math
import data.text as text
from data.core_funcs import *

BORDER_WIDTH = 70


mainClock = pygame.time.Clock()
from pygame.locals import *
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(32)
pygame.display.set_caption('Lynez')
screen = pygame.display.set_mode((550 + 2 * BORDER_WIDTH, 800),0,32)

display = pygame.Surface((275, 400))
gui_display = pygame.Surface((275, 400))
gui_display.set_colorkey((0, 0, 0))

e.load_particle_images('data/images/particles')
e.set_global_colorkey((0, 0, 0))

font = text.Font('data/fonts/large_font.png', (255, 255, 255))
font2 = text.Font('data/fonts/large_font.png', (0, 0, 1))

bounce_s = pygame.mixer.Sound('data/sfx/bounce.wav')
death_s = pygame.mixer.Sound('data/sfx/death.wav')
laser_charge_s = pygame.mixer.Sound('data/sfx/laser_charge.wav')
laser_explode_s = pygame.mixer.Sound('data/sfx/laser_explode.wav')
place_s = pygame.mixer.Sound('data/sfx/place.wav')
restart_s = pygame.mixer.Sound('data/sfx/restart.wav')
bounce_s.set_volume(0.7)
place_s.set_volume(0.9)
laser_charge_s.set_volume(0.05)

particles = []
platforms = [[[0, display.get_height() - 1], [display.get_width(), display.get_height() - 1]]]
last_point = [display.get_width() // 2, display.get_height()]
scroll = 0
square_effects = []

background_color = (13, 20, 33)
background_polygon_color = (24, 34, 46)
line_color = (255, 255, 255)
line_placing_color = (90, 140, 170)
line_width = 3

player_pos = [display.get_width() // 2, display.get_height() // 2]
player_velocity = [0, 0]
player_color = (90, 210, 255)
player_gravity = 0.05
player_terminal_velocity = 1
bounce_strength = 1
bounce_cooldown = 0

def check_line_sides(lines, point):
    line_status = []
    for line in lines:
        line_status.append((line[1][0] - line[0][0]) * (point[1] - line[0][1]) - (line[1][1] - line[0][1]) * (point[0] - line[0][0]))
    return line_status

def sign(num):
    if num != 0:
        return num / abs(num)
    else:
        return 1

def mirror_angle(original,base):
    dif = 180-base
    base = 180
    new = original+dif
    new = new % 360
    dif = base-new
    return original + dif * 2

def dis_func(dis):
    return math.sqrt(dis[0] ** 2 + dis[1] ** 2)

lasers = []
line_effects = []
sparks = []
circle_effects = []

player_path = []
game_score = 0

end_game = False
game_text_loc = - 120
end_text_loc = -220

last_place = 50

screen_shake = 0

transition = 30

pygame.mixer.music.load('data/music.wav')
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.7)

# Loop ------------------------------------------------------- #
while True:

    # Background --------------------------------------------- #
    if transition > 0:
        transition -= 1

    if screen_shake > 0:
        screen_shake -= 1

    if not end_game:
        line_color = (255, 255, 255)
        if player_pos[1] - 200 < scroll:
            scroll += (player_pos[1] - 200 - scroll) / 10
    else:
        line_color = (190, 197, 208)

    if (-scroll) - last_place > 50:
        if random.randint(1, 3) <= 2:
            base_y = scroll - 80
            base_x = random.randint(0, display.get_width())
            new_line = [[base_x, base_y], [base_x + random.randint(0, 200) - 100, base_y + random.randint(0, 100) - 50]]
            if dis_func((new_line[1][0] - new_line[0][0], new_line[1][1] - new_line[0][1])) > 30:
                new_line.sort()
                platforms.append(new_line)
        last_place += 50

    game_score = max(game_score, -(player_pos[1] - display.get_height() // 2))

    display.fill((background_color))
    gui_display.fill((0,0,0))

    mx, my = pygame.mouse.get_pos()
    mx -= BORDER_WIDTH
    mx = mx // 2
    my = my // 2

    player_gravity = 0.05 + game_score / 30000
    player_terminal_velocity = 1 + game_score / 3000
    bounce_strength = 1 + game_score / 8000

    if end_game:
        scroll += (- scroll) / 100

    # Square Effects ----------------------------------------- #
    if random.randint(1, 60) == 1:
        square_effects.append([[random.randint(0, display.get_width()), -80 + scroll], random.randint(0, 359), random.randint(10, 30) / 20, random.randint(15, 40), random.randint(10, 30) / 500])

    for i, effect in sorted(enumerate(square_effects), reverse=True): # loc, rot, speed, size, decay
        effect[0][1] += effect[2]
        effect[1] += effect[2] * effect[4]
        effect[3] -= effect[4]
        points = [
            advance(effect[0], math.degrees(effect[1]), effect[3]),
            advance(effect[0], math.degrees(effect[1]) + 90, effect[3]),
            advance(effect[0], math.degrees(effect[1]) + 180, effect[3]),
            advance(effect[0], math.degrees(effect[1]) + 270, effect[3]),
        ]
        points = [[v[0], v[1] - scroll] for v in points]
        if effect[3] < 1:
            square_effects.pop(i)
        else:
            pygame.draw.polygon(display, background_polygon_color, points, 2)

    # Line Effects ------------------------------------------- #
    for i, effect in sorted(enumerate(line_effects), reverse=True): # locs, targets, color, speed, dur
        if len(effect) == 5:
            effect.append(effect[4])
        effect[0][0][0] += (effect[1][0][0] - effect[0][0][0]) / effect[3]
        effect[0][0][1] += (effect[1][0][1] - effect[0][0][1]) / effect[3]
        effect[0][1][0] += (effect[1][1][0] - effect[0][1][0]) / effect[3]
        effect[0][1][1] += (effect[1][1][1] - effect[0][1][1]) / effect[3]
        effect[4] -= 1
        if effect[4] <= 0:
            line_effects.pop(i)
        opacity = 255 * (effect[4] / effect[5])
        color = (effect[2][0], effect[2][1], effect[2][2], opacity)
        #print(effect[0][0], effect[0][1])
        alpha_line(display, color, effect[0][0], effect[0][1])
        #pygame.draw.line(display, effect[2], effect[0][0], effect[0][1])

    # Circle Effects ----------------------------------------- #
    for i, circle in sorted(enumerate(circle_effects), reverse=True): # loc, radius, border_stats, speed_stats, color
        circle[1] += circle[3][0]
        circle[2][0] -= circle[2][1]
        circle[3][0] -= circle[3][1]
        if circle[2][0] < 1:
            circle_effects.pop(i)
        else:
            pygame.draw.circle(display, circle[4], [int(circle[0][0]), int(circle[0][1] - scroll)], int(circle[1]), int(circle[2][0]))

    # Sparks ------------------------------------------------- #
    for i, spark in sorted(enumerate(sparks), reverse=True): # loc, dir, scale, speed
        speed = spark[3]
        scale = spark[2]
        points = [
            advance(spark[0], spark[1], 2 * speed * scale),
            advance(spark[0], spark[1] + 90, 0.3 * speed * scale),
            advance(spark[0], spark[1], -1 * speed * scale),
            advance(spark[0], spark[1] - 90, 0.3 * speed * scale),
        ]
        points = [[v[0], v[1] - scroll] for v in points]
        color = (255, 255, 255)
        if len(spark) > 4:
            color = spark[4]
        pygame.draw.polygon(display, color, points)
        spark[0] = advance(spark[0], spark[1], speed)
        spark[3] -= 0.5
        if spark[3] <= 0:
            sparks.pop(i)

    # Render Drawing Line ------------------------------------ #
    if not end_game:
        pygame.draw.line(display, line_placing_color, [last_point[0], last_point[1] - scroll], [mx, my])
    #if random.randint(1, 10) == 1:
    #    line_effects.append([[[0, 200], [200, 200]], [[50, 100], [150, 100]], (255, 0, 0), 50, 30])
    #    print('boop')

    player_path = player_path[-50:]
    if len(player_path) > 2:
        player_path_mod = [[v[0], v[1] - scroll] for v in player_path]
        pygame.draw.lines(display, line_placing_color, False, player_path_mod)

    # Lasers ------------------------------------------------- #
    if game_score > 300:
        if random.randint(1, 300 * (1 + len(lasers) * 2)) == 1:
            lasers.append([random.randint(0, display.get_width()), random.randint(90, 150), 20])
    for i, laser in sorted(enumerate(lasers), reverse=True):
        left = laser[0] - laser[1] // 2
        if left < 0:
            left = 0
        right = laser[0] + laser[1] // 2
        if right > display.get_width():
            right = display.get_width()
        pygame.draw.line(display, (190, 40, 100), (left, 0), (left, display.get_height()))
        pygame.draw.line(display, (190, 40, 100), (right, 0), (right, display.get_height()))
        center_line = [[laser[0], 0], [laser[0], display.get_height()]]
        if laser[2] % 12 == 0:
            laser_charge_s.play()
            line_effects.append([[[left, 0], [left, display.get_height()]], center_line, (190, 40, 100), 20, 30])
            line_effects.append([[[right, 0], [right, display.get_height()]], center_line, (190, 40, 100), 20, 30])
        laser[2] += 1
        if laser[2] > 180:
            lasers.pop(i)
            laser_explode_s.play()
            if (player_pos[0] > left) and (player_pos[0] < right):
                if player_pos[0] > laser[0]:
                    player_velocity[0] += 4
                else:
                    player_velocity[0] -= 4
                for i in range(30):
                    sparks.append([player_pos, random.randint(0, 359), random.randint(7, 10) / 10 * 3, 9 * random.randint(5, 10) / 10, (170, 170, 170)])
                    a = random.randint(0, 359)
                    s = random.randint(20, 50) / 10
                    x_p = math.cos(math.radians(a)) * s
                    y_p = math.sin(math.radians(a)) * s
                    particles.append(e.particle(player_pos, 'p', [x_p, y_p], 0.1, random.randint(0, 20) / 10, (170, 170, 170)))
                    screen_shake = 8
            for i in range(300):
                if random.randint(1, 2) == 1:
                    pos_x = left
                    vel = [4 + random.randint(0, 20) / 10, random.randint(0, 10) / 10 - 3]
                else:
                    pos_x = right
                    vel = [-(4 + random.randint(0, 20) / 10), random.randint(0, 10) / 10 - 3]
                pos_y = random.randint(0, display.get_height() + 30) + scroll - 30
                particles.append(e.particle([pos_x, pos_y], 'p', vel, 0.2, random.randint(0, 20) / 10, (160, 40, 80)))

    # Render Platforms --------------------------------------- #
    for platform in platforms:
        if (min(platform[0][1], platform[1][1]) < scroll + display.get_height() + 20) and (max(platform[0][1], platform[1][1]) > scroll - 20):
            pygame.draw.line(display, line_color, [platform[0][0], platform[0][1] - scroll], [platform[1][0], platform[1][1] - scroll], line_width)
            pygame.draw.circle(display, line_color, [platform[0][0], platform[0][1] - scroll], 6, 2)
            pygame.draw.circle(display, line_color, [platform[1][0], platform[1][1] - scroll], 6, 2)
            if random.randint(0, 10) == 0:
                color = random.randint(150, 220)
                sparks.append([random.choice(platform), random.randint(0, 359), random.randint(7, 10) / 10, 5 * random.randint(5, 10) / 10, (color, color, color)])

    # Player ------------------------------------------------- #
    particles.append(e.particle(player_pos, 'p', [random.randint(0, 20) / 40 - 0.25, random.randint(0, 10) / 15 - 1], 0.2, random.randint(0, 30) / 10, player_color))
    line_locations = check_line_sides(platforms, player_pos)

    start_pos = player_pos.copy()

    player_velocity[1] = min(player_terminal_velocity, player_velocity[1] + player_gravity)
    player_pos[0] += player_velocity[0]
    player_pos[1] += player_velocity[1]
    player_velocity[1] = normalize(player_velocity[1], 0.02)

    player_path.append(player_pos.copy())

    if bounce_cooldown > 0:
        bounce_cooldown -= 1

    line_locations_post = check_line_sides(platforms, player_pos)
    for i, side in enumerate(line_locations):
        if sign(side) != sign(line_locations_post[i]):
            if sign(side) == -1:
                if line_math.doIntersect([start_pos, player_pos], platforms[i]):
                    if (player_pos[0] < display.get_width()) and (player_pos[0] > 0):
                        if bounce_cooldown == 0:
                            bounce_s.play()
                            angle = math.atan2(platforms[i][1][1] - platforms[i][0][1], platforms[i][1][0] - platforms[i][0][0])
                            normal = angle - math.pi * 0.5
                            bounce_angle = math.radians(mirror_angle(math.degrees(math.atan2(-player_velocity[1], -player_velocity[0])), math.degrees(normal)) % 360)
                            player_velocity[0] = math.cos(bounce_angle) * (dis_func(player_velocity) + 1)
                            player_velocity[1] = math.sin(bounce_angle) * (dis_func(player_velocity) + 1)
                            player_velocity[1] -= 2 * bounce_strength
                            for i in range(random.randint(4, 6)):
                                spark_angle = math.degrees(normal) + random.randint(0, 180) - 90
                                sparks.append([player_pos.copy(), spark_angle, (dis_func(player_velocity) + 1) / 3 * random.randint(7, 10) / 10, (dis_func(player_velocity) + 1) * 2 * random.randint(5, 10) / 10])
                            bounce_cooldown = 3

    if (player_pos[0] < 0) or (player_pos[0] > display.get_width()):
        if end_game == False:
            death_s.play()
            circle_effects.append([player_pos, 6, [6, 0.15], [10, 0.2], (190, 40, 100)])
            circle_effects.append([player_pos, 6, [6, 0.05], [5, 0.04], (190, 40, 100)])
            screen_shake = 12
        end_game = True

    # Particles ---------------------------------------------- #
    for i, particle in sorted(enumerate(particles), reverse=True):
        alive = particle.update(1)
        if not alive:
            particles.pop(i)
        else:
            particle.draw(display, [0, scroll])

    # GUI ---------------------------------------------------- #
    font.render('score: ' + str(int(game_score)), gui_display, (game_text_loc, 4))
    font2.render(str(int(game_score)), gui_display, (display.get_width() // 2 - font.width(str(int(game_score))) // 2, end_text_loc + 4))
    font2.render('press R', gui_display, (display.get_width() // 2 - font.width('press R') // 2, end_text_loc + 28))
    font.render(str(int(game_score)), gui_display, (display.get_width() // 2 - font.width(str(int(game_score))) // 2, end_text_loc))
    font.render('press R', gui_display, (display.get_width() // 2 - font.width('press R') // 2, end_text_loc + 24))

    if end_game:
        game_text_loc += (-120 - game_text_loc) / 20
        end_text_loc += (200 - end_text_loc) / 20
    else:
        game_text_loc += (6 - game_text_loc) / 10
        end_text_loc += (-220 - end_text_loc) / 20

    # Buttons ------------------------------------------------ #
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == K_r:
                if end_game:
                    restart_s.play()
                    transition = 30
                    lasers = []
                    line_effects = []
                    sparks = []
                    player_path = []
                    game_score = 0
                    end_game = False
                    particles = []
                    platforms = [[[0, display.get_height() - 1], [display.get_width(), display.get_height() - 1]]]
                    last_point = [display.get_width() // 2, display.get_height()]
                    scroll = 0
                    player_pos = [display.get_width() // 2, display.get_height() // 2]
                    player_velocity = [0, 0]
                    circle_effects = []
                    last_place = 50
                    square_effects = []
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if not end_game:
                    line = [last_point, [mx, my + scroll]]
                    line.sort()
                    platforms.append(line)
                    last_point = [mx, my + scroll]
                    circle_effects.append([[mx, my + scroll], 4, [4, 0.2], [4, 0.3], (255, 255, 255)])
                    place_s.play()

    # Update ------------------------------------------------- #
    display_background = display.copy()
    display_background.set_alpha(25) # background opacity
    black_surf = pygame.Surface(screen.get_size())
    black_surf.fill(background_color)
    black_surf.set_alpha(85) # blur
    display.set_colorkey((background_color))
    screen.blit(pygame.transform.scale(display_background, (display.get_width() * 2 + 40, display.get_height() * 2 + 40)), (-20 + BORDER_WIDTH, 0))
    screen.blit(black_surf,(0, 0))
    offset = [0, 0]
    if screen_shake:
        offset[0] += random.randint(0, 10) - 5
        offset[1] += random.randint(0, 10) - 5
    screen.blit(pygame.transform.scale(display, (display.get_width() * 2, display.get_height() * 2)), (BORDER_WIDTH + offset[0], offset[1]))
    screen.blit(pygame.transform.scale(gui_display, (display.get_width() * 2, display.get_height() * 2)),(BORDER_WIDTH, 0))
    border_box = pygame.Rect(0, 0, BORDER_WIDTH, screen.get_height())
    pygame.draw.rect(screen, (0, 0, 0), border_box)
    border_box.x = screen.get_width() - BORDER_WIDTH
    pygame.draw.rect(screen, (0, 0, 0), border_box)
    if transition:
        black_surf = pygame.Surface(screen.get_size())
        black_surf.set_alpha(255 * transition / 30)
        screen.blit(black_surf, (0, 0))
    pygame.display.update()
    mainClock.tick(60)
