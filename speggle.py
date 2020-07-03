# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import os
from math import pi, sin, cos, atan, acos, radians, degrees, sqrt
from PIL import Image

####################################################################################################
# Constants
####################################################################################################
# The width of the screen
SCREEN_WIDTH = 800
# The height of the screen
SCREEN_HEIGHT = 800
# The acceleration (in pixels per second squared) due to gravity
G = 0.4
# The initial velocity of the ball upon being shot by the cannon (in pixels per second)
V_0 = 10
# The maximum angle the ball can be launched at in radians from straight down
ANGLE_LIMIT = pi / 2 + 0.1
# The color of the pixel in a peg layout specifiying the top left corner of a peg
PEG_INDICATOR = (255, 0, 255)
# The radius of the ball and pegs
BALL_RADIUS = 16
# The diameter of the ball and pegs
BALL_DIAMETER = BALL_RADIUS * 2
# The square of the diameter of ball and pegs
D_SQUARED = BALL_DIAMETER ** 2
# How much velocity gets conserved after bouncing off of a peg
PEG_ENERGY_CONSERVATION = 0.9
# True if the game is in debug mode
DEBUG = True
# True if the game is paused during debug mode
PAUSED = False
# Set to true if in debug mode and user wants to set forward one frame
STEP = False

####################################################################################################
# Helper functions
####################################################################################################

# The square of the euclidian distance between 2 points
def d_squared(p1, p2):
  dx = p2[0] - p1[0]
  dy = p2[1] - p1[1]
  return dx * dx + dy * dy

# The position of the ball on the next frame given the position and velocity
def next_ball_pos(x, y, vx, vy):
  old_x = x
  old_y = y
  x += vx
  y += vy
  vy += G
  collision = collision_between((x, y), pegs)
  num_pegs = len(collision)
  # If the ball is colliding with any pegs
  if num_pegs > 0:
    col_x = 0
    col_y = 0
    # Take the average position of those pegs and consider it as one peg
    for peg in collision:
      col_x += peg.x
      col_y += peg.y
    col_x /= num_pegs
    col_y /= num_pegs
    # Theta is the angle of descent from the center of the ball to the center of the peg
    theta = atan((col_y - old_y) / (col_x - old_x))
    # Phi is the line of reflection between the ball and the peg
    phi = theta + pi / 2
    v = sqrt(vx * vx + vy * vy)
    if vx == 0:
      v_theta = 0
    else:
      v_theta = atan(vy / vx)
    attack_theta = pi / 4 - v_theta - phi
    new_v_theta = pi - attack_theta
    if phi % (2 * pi) < pi / 2:
      new_v_theta -= pi / 2
    vx = v * cos(new_v_theta)
    vy = v * sin(new_v_theta)
    
    if DEBUG:
      surface_x = 10 * cos(phi)
      surface_y = 10 * sin(phi)
      pygame.draw.line(screen, (255, 0, 255), (x - surface_x + BALL_RADIUS, y - surface_y + BALL_RADIUS), 
                      (x + surface_x + BALL_RADIUS, y + surface_y + BALL_RADIUS), 5)
      
  
  return x, y, vx, vy, collision

def collision_between(point, pegs):
  list = []
  for peg in pegs:
    if d_squared(point, (peg.x, peg.y)) <= D_SQUARED:
      list.append(peg)
  return list

launching = False

def launch_ball():
  global launching
  objects.remove(indicator)
  cannon.set_frozen(True)
  ball.launch(SCREEN_WIDTH / 2 - BALL_RADIUS, 0 - BALL_RADIUS, V_0 * sin(indicator.angle), 
              V_0 * cos(indicator.angle));
  objects.insert(0, ball)
  launching = True

def finish_launch():
  global launching
  objects.remove(ball)
  objects.insert(0, indicator)
  cannon.set_frozen(False)
  launching = False
  

####################################################################################################
# Classes
####################################################################################################

# The parent class for all game objects
class GameObject:

  # Construct this object with the given position and path to its sprite file
  def __init__(self, x, y, spritePath=None):
    if spritePath:
      self.sprite = pygame.image.load(spritePath)
    self.x = x
    self.y = y
  
  # Draw this object's sprite on the given screen each frame
  def draw_on(self, screen):
    screen.blit(self.sprite, (self.x, self.y))
  
  # Calculate some state about the object each frame. By default, calculate nothing
  def tick(self):
    return None

# The class for the cannon which launches the ball
class Cannon(GameObject):
  # The x position for the base of the cannon
  BASE_X = SCREEN_WIDTH / 2 - 125
  # The y position for the base of the cannon
  BASE_Y = 0
  
  # Construct a cannon at the top of the screen facing downwards
  def __init__(self):
    GameObject.__init__(self, SCREEN_WIDTH / 2, 0, 'img/cannon.png')
    self.base = pygame.image.load('img/cannon_base.png')
    
    self.width = self.sprite.get_width() / 2
    self.height = self.sprite.get_height() / 2
    self.angle = 0
    self.dx = 0
    self.dy = 0
    self.frozen = False

  # Aquired and modified from here: https://www.pygame.org/wiki/RotateCenter
  # For rotating the cannon around its center
  def rot_center(self, rect, angle):
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(self.sprite, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect
  
  # Draw the base of the cannon and then the cannon, rotated around the base and pointed
  # where the ball will shoot
  def draw_on(self, screen):
    screen.blit(self.base, (self.BASE_X, self.BASE_Y))
    rect = self.sprite.get_rect(center=(self.x + self.dx, self.y + self.dy))
    image, rect = self.rot_center(rect, self.angle)
    screen.blit(image, rect)
  
  # 
  def set_angle(self, angle):
    self.angle = (360 + angle % 360) % 360
    rads = radians(self.angle)
    self.dx = (self.width + 20) * sin(rads)
    self.dy = (self.height - 40) * cos(rads)
  
  def tick(self):
    global indicator
    if not self.frozen:
      self.set_angle(indicator.cannon_angle(self))
  
  def set_frozen(self, frozen):
    self.frozen = frozen

class Indicator():
  cannon_t = 7
  
  def __init__(self, cannon):
    self.x = cannon.x - BALL_RADIUS
    self.y = cannon.y - BALL_RADIUS
    self.vx = 0
    self.vy = V_0
    self.angle = 0
    self.cannon = cannon
  
  def cannon_angle(self, cannon):
    dx = self.vx * self.cannon_t
    dy = 0.5 * G * self.cannon_t * self.cannon_t + self.vy * self.cannon_t
    return degrees(atan(dx / dy))
  
  def ball_start(self):
    self.x = self.cannon.x - BALL_RADIUS
    self.y = self.cannon.y - BALL_RADIUS
    self.vx = V_0 * sin(self.angle)
    self.vy = V_0 * cos(self.angle)
  
  def tick(self):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - self.cannon.x
    dy = mouse_y - self.cannon.y
    if dy == 0:
      self.ball_start()
      return
    else:
      flag = False
      if dx < 0:
        flag = True
        dx = -1 * dx
      top_term = dy - (G * dx * dx / (V_0 * V_0))
      bottom_term = sqrt(dx * dx + dy * dy)
      ratio = top_term / bottom_term
      if(ratio < -1) or (ratio > 1):
        self.ball_start()
        return
      
      side_term = atan(dx / dy)
      angle = (acos(ratio) + atan(dx / dy)) / 2
      if angle > ANGLE_LIMIT:
        self.ball_start()
        return
      if flag:
        angle = -1 * angle
      self.angle = angle
      self.ball_start()
  
  def draw_on(self, screen):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
    while new_y < mouse_y and (len(collision) == 0 or DEBUG):
      pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS, self.y + BALL_RADIUS), 
                      (new_x + BALL_RADIUS, new_y + BALL_RADIUS), 5)
      self.x, self.y, self.vx, self.vy = new_x, new_y, new_vx, new_vy
      new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
    pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS, self.y + BALL_RADIUS), 
                    (new_x + BALL_RADIUS, new_y + BALL_RADIUS), 5)

class Peg(GameObject):
  BLUE = 0
  ORANGE = 1
  GREEN = 2
  PURPLE = 3
  SPRITES = [pygame.image.load("img/blue_peg.png"), pygame.image.load("img/orange_peg.png"), 
    pygame.image.load("img/green_peg.png"), pygame.image.load("img/purple_peg.png")]
  
  def __init__(self, x, y, type):
    GameObject.__init__(self, x, y)
    self.set_type(type)
  
  def set_type(self, type):
    self.sprite = self.SPRITES[type]
    self.type = type

class Ball(GameObject):
  def __init__(self):
    GameObject.__init__(self, 0, 0, "img/ball.png")
  
  def launch(self, x, y, vx, vy):
    self.x = x
    self.y = y
    self.vx = vx
    self.vy = vy
  
  def tick(self):
    self.x, self.y, self.vx, self.vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
    if (self.x + BALL_DIAMETER < 0 or self.x > SCREEN_WIDTH or self.y + BALL_DIAMETER < 0 or 
        self.y > SCREEN_HEIGHT):
      finish_launch()
    
  def draw_on(self, screen):
    GameObject.draw_on(self, screen)
    if DEBUG:
      next_pos = next_ball_pos(self.x, self.y, self.vx, self.vy)
      pygame.draw.line(screen, (255, 0, 255), (self.x + BALL_RADIUS, self.y + BALL_RADIUS), 
                      (next_pos[0] + BALL_RADIUS, next_pos[1] + BALL_RADIUS), 5)

####################################################################################################
# Initialization
####################################################################################################
print("Enter the level name:")
level = input()
background = pygame.image.load('levels/' + level + '/background.png')
layout = Image.open('levels/' + level + '/pegs.png').convert('RGB')

print("Loading...")
width, height = layout.size
objects = []
pegs = []
for x in range(width):
  for y in range(height):
    color = layout.getpixel((x, y))
    if (color[0], color[1], color[2]) == PEG_INDICATOR:
      peg = Peg(x, y, Peg.BLUE)
      objects.append(peg)
      pegs.append(peg)

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT));
pygame.display.set_caption("Speggle")

cannon = Cannon()
indicator = Indicator(cannon)
ball = Ball()

objects.append(indicator)
objects.append(cannon)

####################################################################################################
# Game loop
####################################################################################################
running = True;

def time_check():
  global now
  earlier = now
  later = datetime.now()
  if (later - earlier).microseconds > 16667:
    now = later
    return True
  return False

def tick():
  global running, PAUSED, STEP
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.MOUSEBUTTONDOWN and not launching:
      launch_ball()
    elif event.type == pygame.KEYUP:
      if event.key == pygame.K_SPACE and DEBUG:
        PAUSED = not PAUSED
      elif event.key == pygame.K_s and DEBUG:
        STEP = True
        PAUSED = False
  
  if not PAUSED or not DEBUG:
    for object in objects:
      object.tick()
  
  
def render():
  screen.blit(background, (0, 0))
  for object in objects:
    object.draw_on(screen)
  
  pygame.display.update()

now = datetime.now()
while running:
  if time_check():
    tick()
    if not PAUSED or not DEBUG:
      render()
    if DEBUG and STEP:
      STEP = False
      PAUSED = True
