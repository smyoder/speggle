# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import os
from math import pi, sin, cos, atan, acos, radians, degrees, sqrt, fabs, copysign
from PIL import Image

####################################################################################################
# Constants
####################################################################################################
# The width of the level
LEVEL_WIDTH = 800
# The height of the level
LEVEL_HEIGHT = 800
# The width of the ball home at the left of the screen
LEFT_WIDTH = 100
# The width of the orange peg indicator at the right of the screen
RIGHT_WIDTH = 100

# The acceleration (in pixels per second squared) due to gravity
G = 0.4
# The initial velocity of the ball upon being shot by the cannon (in pixels per second)
V_0 = 10
# How much velocity gets conserved after bouncing
ENERGY_CONSERVATION = 0.7
# The maximum angle the ball can be launched at in radians from straight down
ANGLE_LIMIT = pi / 2 + 0.1

# The radius of the ball and pegs
BALL_RADIUS = 16
# The diameter of the ball and pegs
BALL_DIAMETER = BALL_RADIUS * 2
# The square of the diameter of ball and pegs
D_SQUARED = BALL_DIAMETER ** 2

# True if the game is in debug mode
DEBUG = False
# True if the game is paused during debug mode
PAUSED = False
# Set to true if in debug mode and user wants to set forward one frame
STEP = False
# The number of frames to wait before holding step advances the game by one frame
STEP_FRAMES = 10

# How many frames ahead the game will calculate the ball's position during debug and zen
FORESIGHT_DEPTH = 600
# The point multiplier corresponding to the number of orange pegs
MULTIPLIERS = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 5, 5, 5, 10, 10, 10, 100]
# The color of the pixel in a peg layout specifiying the top left corner of a peg
PEG_INDICATOR = (255, 0, 255)

####################################################################################################
# Helper functions
####################################################################################################

# The square of the euclidian distance between 2 points
def d_squared(p1, p2):
  dx = p2[0] - p1[0]
  dy = p2[1] - p1[1]
  return dx * dx + dy * dy

message = None
# The position of the ball on the next frame given the position and velocity
def next_ball_pos(x, y, vx, vy):
  global index, ceiling, message
  message = None
  collision = collision_between((x, y), pegs)
  if x < 0 :
    wall_peg.x, wall_peg.y = 0 - BALL_DIAMETER, y
    collision.append(wall_peg)
  elif x + BALL_DIAMETER > LEVEL_WIDTH :
    wall_peg.x, wall_peg.y = LEVEL_WIDTH, y
    collision.append(wall_peg)
  elif y < 0 and ceiling:
    wall_peg.x, wall_peg.y = x, 0 - BALL_DIAMETER
    collision.append(wall_peg)
    
  # If the ball is colliding with any pegs
  num_pegs = len(collision)
  collided = False
  if num_pegs > 0:
    collided = True
    # Take the average position of those pegs and consider it as one peg
    col_x = 0
    col_y = 0
    for peg in collision:
      col_x += peg.x
      col_y += peg.y
    col_x /= num_pegs
    col_y /= num_pegs
    
    dx = col_x - x
    dy = col_y - y
    
    # Theta is the angle of descent from the center of the ball to the center of the peg
    if dx == 0:
      if dy < 0:
        theta = 3 * pi / 2
      else:
        theta = pi / 2
    else:
      theta = atan(dy / dx)
    
    nudge = BALL_DIAMETER - sqrt(dx * dx + dy * dy)
    nudge_x = nudge * cos(theta)
    nudge_y = nudge * sin(theta)
    nudge_x = copysign(nudge_x, -1 * dx)
    nudge_y = copysign(nudge_y, -1 * dy)
    x += nudge_x
    y += nudge_y
      
    # Phi is the line of reflection between the ball and the peg
    phi = theta + pi / 2
    v = sqrt(vx * vx + vy * vy)
    if vx == 0:
      if vy < 0:
        v_theta = 3 * pi / 2
      else:
        v_theta = pi / 2
    else:
      v_theta = atan(vy / vx)
    v_theta = 2 * theta - v_theta
    if vx > 0:
      v_theta += pi
    vx = v * cos(v_theta) * ENERGY_CONSERVATION
    vy = v * sin(v_theta) * ENERGY_CONSERVATION
    
    if DEBUG:
      surface_x = 10 * cos(phi)
      surface_y = 10 * sin(phi)
      pygame.draw.line(screen, (255, 0, 255), (x - surface_x + BALL_RADIUS + LEFT_WIDTH, y - 
        surface_y + BALL_RADIUS), (x + surface_x + BALL_RADIUS + LEFT_WIDTH, y + surface_y + 
        BALL_RADIUS), 5)
      message = debug_font.render('dx: %.5f | dy: %.5f | vx: %.5f | vy: %.5f' % (dx, dy, vx, vy), True, (255, 0, 255))
  ceiling = launching and (ceiling or collided)
  x += vx
  y += vy
  vy += G
  return x, y, vx, vy, collision

def collision_between(point, pegs):
  list = []
  for peg in pegs:
    if d_squared(point, (peg.x, peg.y)) <= D_SQUARED:
      list.append(peg)
  return list

launching = False
ceiling = False

def launch_ball():
  global launching
  objects.remove(indicator)
  cannon.set_frozen(True)
  ball.launch(LEVEL_WIDTH / 2 - BALL_RADIUS, 0 - BALL_RADIUS, V_0 * sin(indicator.angle), 
              V_0 * cos(indicator.angle));
  objects.insert(0, ball)
  launching = True

def finish_launch():
  global launching
  objects.remove(ball)
  objects.insert(0, indicator)
  cannon.set_frozen(False)
  launching = False
  ceiling = False
  

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
    screen.blit(self.sprite, (self.x + LEFT_WIDTH, self.y))
  
  # Calculate some state about the object each frame. By default, calculate nothing
  def tick(self):
    return None

# The class for the cannon which launches the ball
class Cannon(GameObject):
  # The x position for the base of the cannon
  BASE_X = LEVEL_WIDTH / 2 - 125
  # The y position for the base of the cannon
  BASE_Y = 0
  
  # Construct a cannon at the top of the screen facing downwards
  def __init__(self):
    GameObject.__init__(self, LEVEL_WIDTH / 2, 0, 'img/cannon.png')
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
    screen.blit(self.base, (self.BASE_X + LEFT_WIDTH, self.BASE_Y))
    rect = self.sprite.get_rect(center=(self.x + self.dx + LEFT_WIDTH, self.y + self.dy))
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

class Indicator:
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
    mouse_x -= LEFT_WIDTH
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
    mouse_x -= LEFT_WIDTH
    new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
    foresight = 0
    while new_y < mouse_y and (len(collision) == 0 or DEBUG) and foresight < FORESIGHT_DEPTH:
      pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS + LEFT_WIDTH, self.y + 
        BALL_RADIUS ), (new_x + BALL_RADIUS + LEFT_WIDTH, new_y + BALL_RADIUS), 5)
      
      self.x, self.y, self.vx, self.vy = new_x, new_y, new_vx, new_vy
      new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
      foresight += 1
    pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS + LEFT_WIDTH, self.y + BALL_RADIUS)
      , (new_x + BALL_RADIUS + LEFT_WIDTH, new_y + BALL_RADIUS), 5)
    
    hit_pegs = []

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
    if (self.x + BALL_DIAMETER < 0 or self.x > LEVEL_WIDTH or self.y + BALL_DIAMETER < 0 or 
        self.y > LEVEL_HEIGHT):
      finish_launch()
    
  def draw_on(self, screen):
    GameObject.draw_on(self, screen)
    if DEBUG:
      next_pos = next_ball_pos(self.x, self.y, self.vx, self.vy)
      pygame.draw.line(screen, (255, 0, 255), (self.x + BALL_RADIUS + LEFT_WIDTH, self.y + 
        BALL_RADIUS), (next_pos[0] + BALL_RADIUS + LEFT_WIDTH, next_pos[1] + BALL_RADIUS), 5)

class PegTracker(GameObject):
  def __init__(self):
    GameObject.__init__(self, LEVEL_WIDTH, 0)
    self.pegs_hit = 0
    self.indicators = []
    for i in range(26):
      self.indicators.append(pygame.image.load('img/peg_tracker/' + str(i) + '.png'))
    self.sprite = self.indicators[0]
  
  def add_peg(self):
    self.pegs_hit += 1
    self.sprite = self.indicators[self.pegs_hit]


####################################################################################################
# Initialization
####################################################################################################
print("Enter the level name:")
level = input()
background = pygame.image.load('levels/' + level + '/background.png')
layout = Image.open('levels/' + level + '/pegs.png').convert('RGB')\

pygame.font.init()
debug_font = pygame.font.Font(pygame.font.get_default_font(), 24)

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

wall_peg = Peg(-100, -100, Peg.BLUE)

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode((LEVEL_WIDTH + LEFT_WIDTH + RIGHT_WIDTH, LEVEL_HEIGHT));
pygame.display.set_caption("Speggle")

cannon = Cannon()
indicator = Indicator(cannon)
ball = Ball()
peg_tracker = PegTracker()
ball_home = pygame.image.load('img/ball_home.png')

objects.append(indicator)
objects.append(cannon)
objects.append(peg_tracker)

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

step_count = 0
def tick():
  global running, PAUSED, STEP, step_count
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.MOUSEBUTTONDOWN and not launching:
      launch_ball()
    elif event.type == pygame.KEYUP:
      if DEBUG and event.key == pygame.K_SPACE:
        PAUSED = not PAUSED
      elif DEBUG and event.key == pygame.K_s:
        step_count = 0
  keys = pygame.key.get_pressed()
  if DEBUG and keys[pygame.K_s]:
    if step_count == 0:
      STEP = True
      PAUSED = False
    step_count = (step_count + 1) % STEP_FRAMES
  
  if not PAUSED or not DEBUG:
    for object in objects:
      object.tick()
  
  
def render():
  screen.blit(background, (LEFT_WIDTH, 0))
  for object in objects:
    object.draw_on(screen)
  screen.blit(ball_home, (0, 0))
  if DEBUG and message:
    screen.blit(message, (LEVEL_WIDTH / 2 - message.get_width() / 2 + LEFT_WIDTH, 0))
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
