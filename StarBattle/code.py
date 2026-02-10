import pygame
import math
import random

# globals for user interface
WIDTH = 1280
HEIGHT = 960

score = 0
lives = 3
started = False

# --- Rock spawning controls ---
MAX_ROCKS = 12
ROCK_SPAWN_INTERVAL_MS = 700  # spawn 1 rock every 0.7s (tune this)
last_rock_spawn_ms = 0

# Information of Image
class ImageInfo:
    def __init__(self, center, size, radius = 0, lifespan = None, animated = False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated
    
# define general helper function
def angle_to_vector(ang):
    rad = math.radians(ang)
    return [math.cos(rad), math.sin(rad)]

def dist(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

# Ship class
class Ship:
    def __init__(self, pos, vel, angle, image, info):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = 0
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()       
    
    def draw(self, screen):
        if self.thrust:
            fired_ship = self.image.subsurface(
                pygame.Rect(self.image_size[0], 0, self.image_size[0], self.image_size[1])).copy()
            rotated_image = pygame.transform.rotate(fired_ship, -self.angle)
        else:
            stopped_ship = self.image.subsurface(
                pygame.Rect(0, 0, self.image_size[0], self.image_size[1])).copy()
            rotated_image = pygame.transform.rotate(stopped_ship, -self.angle)
        
        rotated_rect = rotated_image.get_rect(center=(self.pos[0], self.pos[1]))
        screen.blit(rotated_image, rotated_rect)    

    def update(self):
        # update angle
        self.angle += self.angle_vel
        # update position
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT
        # update velocity
        if self.thrust:
            acc = angle_to_vector(self.angle)
            self.vel[0] += acc[0] * 0.1
            self.vel[1] += acc[1] * 0.1
        self.vel[0] *= 0.99
        self.vel[1] *= 0.99

    def set_thrust(self, on):
        self.thrust = on
        # play sound
        if on:
            pass
        else:
            pass
    
    def increment_angle_vel(self):
        self.angle_vel += 0.05
        
    def decrement_angle_vel(self):
        self.angle_vel -= 0.05
        
    def get_position(self):
        return self.pos
    
    def get_radius(self):
        return self.radius

    # shoot missile
    def shoot(self):
        global missile_group
        forward = angle_to_vector(self.angle)
        missile_pos = [self.pos[0] + self.radius * forward[0], self.pos[1] + self.radius * forward[1]]
        missile_vel = [self.vel[0] + 6 * forward[0], self.vel[1] + 6 * forward[1]]
        missile = Sprite(missile_pos, missile_vel, self.angle, 0, missile_image, missile_info)
        missile_group.append(missile)

# Sprite class (currently use for missile and rock)
class Sprite:
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound = None):
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        
        if sound:
            sound.play()
    
    def draw(self, screen):
        if self.animated:
            frame = min(self.age, 23)
            curr_stage = self.image.subsurface(pygame.Rect(60 * frame, 0, 60, 60)).copy()
            rotated_image = pygame.transform.rotate(curr_stage, -self.angle)
        else:
            rotated_image = pygame.transform.rotate(self.image, -self.angle)
        
        rotated_rect = rotated_image.get_rect(center=(self.pos[0], self.pos[1]))
        screen.blit(rotated_image, rotated_rect)
    
    def update(self):
        # update angle
        self.angle += self.angle_vel
        
        # update position
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT

        # update age
        self.age += 1

        # check if we still want it
        if self.age >= self.lifespan:
            return True
        elif self.age % 24 == 0 and self.animated:
            self.animated = False
            return True
        else:
            return False       

    def get_position(self):
        return self.pos
    
    def get_radius(self):
        return self.radius
    
    def collide(self, another_obj):
        if dist(self.get_position(), another_obj.get_position()) > (self.get_radius() + another_obj.get_radius()):
            return False
        else:
            return True


def move(ship):
    keys = pygame.key.get_pressed()

    ship.set_thrust(keys[pygame.K_w])

    # fixed rotation speed (no acceleration ramp)
    if keys[pygame.K_a] and not keys[pygame.K_d]:
        ship.increment_angle_vel()
    elif keys[pygame.K_d] and not keys[pygame.K_a]:
        ship.decrement_angle_vel()
    else:
        ship.angle_vel = 0.0

def rock_generator(now_ms):
    global rock_group, last_rock_spawn_ms, started

    if not started:
        return

    if len(rock_group) >= MAX_ROCKS:
        return

    if now_ms - last_rock_spawn_ms < ROCK_SPAWN_INTERVAL_MS:
        return

    # Try a few times to avoid spawning on top of the ship
    for i in range(10):
        rock_pos = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]
        if dist(rock_pos, ship_A.get_position()) > 150:  # avoid immediate collision
            break

    rock_vel = [random.random() * 0.6 - 0.3, random.random() * 0.6 - 0.3]
    rock_avel = random.random() * 0.2 - 0.1
    rock = Sprite(rock_pos, rock_vel, 0, rock_avel, rock_image, rock_info)
    rock_group.append(rock)
    last_rock_spawn_ms = now_ms

# update and draw for each sprite in the group
def process_sprite_group(sprite_group, screen):
    for sprite in sprite_group:
        sprite.draw(screen)
        if sprite.update():
            sprite_group.remove(sprite)

# exposion animation
def spawn_explosion(pos):
    # explosion lasts 24 frames
    exp = Sprite(pos, [0, 0], 0, 0, explosion_image, explosion_info)
    explosion_group.append(exp)     

# check collision of group and a object
def group_collide(group, other_object):
    collided = False
    for obj in group[:]:
        if obj.collide(other_object):
            spawn_explosion(obj.get_position())
            group.remove(obj)
            collided = True
    return collided

# check collision of group and group
def group_group_colide(group1, group2):
    collide = False
    for object1 in set(group1):
        if group_collide(group2, object1):
            group1.remove(object1)
            collide = collide + 1
    return collide

def draw(screen):
    global started, ship_A, rock_group, missile_group
    global explosion_group, score, lives, last_rock_spawn_ms

    running = True
    while running:
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not started:
                # start game
                started = True
                score = 0
                lives = 3
                rock_group.clear()
                missile_group.clear()
                explosion_group.clear()
                ship_A = Ship([WIDTH / 4, HEIGHT / 2], [0, 0], 0, ship_image, ship_info)
                last_rock_spawn_ms = now_ms  # avoid instant spawn flood

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and started:
                ship_A.shoot()
        
        screen.fill((0, 0, 0))
        screen.blit(space_image, (0, 0))

        if started:
            move(ship_A)
            rock_generator(now_ms)
            ship_A.update()
            ship_A.draw(screen)
            process_sprite_group(rock_group, screen)
            process_sprite_group(explosion_group, screen)
            process_sprite_group(missile_group, screen)

            group_collide(rock_group, ship_A)
            group_group_colide(missile_group, rock_group)
        else:
            screen.blit(opening_image, (320, 240))           

        pygame.display.flip()
        clock.tick(60)
    


# initial screen set up
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RiceRocks")
clock = pygame.time.Clock()

# image upload
rock_info = ImageInfo((60, 60), (120, 120), 60)
original_rock_image = pygame.image.load("rock.png").convert_alpha()
rock_image = pygame.transform.scale(original_rock_image, (120, 120))

original_space_image = pygame.image.load("space.png").convert()
space_image = pygame.transform.scale(original_space_image, (1280, 960))

original_debris_image = pygame.image.load("debris.png").convert_alpha()

ship_info = ImageInfo((60, 60), (120, 120), 60)
original_ship_image = pygame.image.load("ship.png").convert_alpha()
ship_image = pygame.transform.scale(original_ship_image, (240, 120))

opening_info = ImageInfo((320, 240), (640, 480))
original_opening_image = pygame.image.load("opening.png").convert_alpha()
opening_image = pygame.transform.scale(original_opening_image, (640, 480))

missile_info = ImageInfo([5,5], [10, 10], 3, 50)
original_missile_image = pygame.image.load("missile.png").convert_alpha()
missile_image = pygame.transform.scale(original_missile_image, (10, 10))

explosion_info = None
original_explosion_image = pygame.image.load("explosion.png").convert_alpha()
explosion_image = pygame.transform.scale(original_explosion_image, (1440, 60))


# initialization
ship_A = Ship([WIDTH / 4, HEIGHT / 2], [0, 0], 0, ship_image, ship_info)

rock_group = []
rock_num = len(rock_group)
missile_group = []
explosion_group = []

draw(screen)
pygame.quit()