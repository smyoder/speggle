# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import os
from math import pi, sin, cos, atan, acos, radians, degrees, sqrt, fabs, copysign
from PIL import Image
import random

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
DEBUG = True
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

# How many frames to wait between deleting each peg
PEG_DELETE_FRAMES = 5
# The maximum amount in pixels the ball can move and be considered 'still'
STILL_BALL = 2
# The number of frames the ball can be still before deleting the pegs
STILL_BALL_FRAMES = 60

# How many possible shots get checked by the zen shot
ZEN_SHOTS = 300

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
      if launching and peg != wall_peg:
        peg.hit()
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
      message = debug_font.render('dx: %.5f | dy: %.5f | vx: %.5f | vy: %.5f' % (dx, dy, vx, vy), 
                                  True, (255, 0, 255))
  ceiling = (launching or predicting) and (ceiling or collided)
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
zen_shots = 0

def launch_angle(x, y):
  dx = x - cannon.x
  dy = y - cannon.y
  if dy == 0:
    return pi / -2 if dx < 0 else pi / 2
  else:
    flag = False
    if dx < 0:
      flag = True
      dx = -1 * dx
    top_term = dy - (G * dx * dx / (V_0 * V_0))
    bottom_term = sqrt(dx * dx + dy * dy)
    ratio = top_term / bottom_term
    if ratio < -1 or ratio > 1:
      return None
    
    side_term = atan(dx / dy)
    angle = (acos(ratio) + atan(dx / dy)) / 2
    if angle > ANGLE_LIMIT:
      return None
    if flag:
      angle = -1 * angle
    return angle

predicting = False
def predict_shot(angle):
  global predicting, ceiling
  x = cannon.x - BALL_RADIUS
  y = cannon.y - BALL_RADIUS
  vx = V_0 * sin(angle)
  vy = V_0 * cos(angle)
  foresight = 0
  hit_pegs = []
  predicting = True
  while y < LEVEL_HEIGHT and foresight < FORESIGHT_DEPTH:
    x, y, vx, vy, collision = next_ball_pos(x, y, vx, vy)
    for peg in collision:
      if hit_pegs.count(peg) == 0:
        hit_pegs.append(peg)
    foresight += 1
  predicting = False
  ceiling = False
  return len(hit_pegs)

def launch_ball():
  global launching, zen_shots
  objects.remove(indicator)
  cannon.set_frozen(True)
  objects.insert(0, ball)
  if zen_shots > 0:
    zen_shots -= 1
    max_angle = None
    max_pegs_hit = -1
    for i in range(ZEN_SHOTS):
      peg = pegs[random.randrange(len(pegs))]
      x = peg.x
      y = peg.y
      x += random.randrange(BALL_DIAMETER) - BALL_RADIUS
      y += random.randrange(BALL_DIAMETER) - BALL_RADIUS
      angle = launch_angle(x, y)
      if angle:
        pegs_hit = predict_shot(angle)
        if pegs_hit > max_pegs_hit:
          max_pegs_hit = pegs_hit
          max_angle = angle
    ball.launch(LEVEL_WIDTH / 2 - BALL_RADIUS, 0 - BALL_RADIUS, V_0 * sin(max_angle), 
                V_0 * cos(max_angle));
  else:
    ball.launch(LEVEL_WIDTH / 2 - BALL_RADIUS, 0 - BALL_RADIUS, V_0 * sin(indicator.angle), 
                V_0 * cos(indicator.angle));
  launching = True
    

def finish_launch():
  global launching, ball_stasis, purple_peg
  ball_stasis = 0
  objects.insert(0, indicator)
  cannon.set_frozen(False)
  ceiling = False
  blue_pegs_left = False
  num_pegs = len(pegs)
  if not DEBUG:
    blue_idx = random.randrange(num_pegs)
    blue_count = -1
    idx = 0
    while blue_count < blue_idx:
      if pegs[idx].type == Peg.BLUE:
        blue_count += 1
        blue_pegs_left = True
      idx += 1
      if idx >= num_pegs:
        if not blue_pegs_left:
          return None
        else:
          idx = 0
    
    purple_peg.set_type(Peg.BLUE)
    purple_peg = pegs[idx - 1]
    purple_peg.set_type(Peg.PURPLE)
      

deleting = False
def delete_pegs():
  global deleting, launching
  deleting = True
  launching = False
  objects.remove(ball)

def deleting_pegs(hit_pegs, frame_idx):
  if frame_idx == 0:
    if len(hit_pegs) > 0:
      peg = hit_pegs.pop(0)
      objects.remove(peg)
      pegs.remove(peg)
  return len(hit_pegs) > 0

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
    angle = launch_angle(mouse_x - LEFT_WIDTH, mouse_y)
    if angle:
      self.angle = angle
    self.ball_start()
  
  def draw_on(self, screen):
    global predicting, ceiling
    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse_x -= LEFT_WIDTH
    predicting = True
    new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
    foresight = 0
    while new_y < mouse_y and (len(collision) == 0 or DEBUG) and foresight < FORESIGHT_DEPTH:
      pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS + LEFT_WIDTH, self.y + 
        BALL_RADIUS ), (new_x + BALL_RADIUS + LEFT_WIDTH, new_y + BALL_RADIUS), 5)
      self.x, self.y, self.vx, self.vy = new_x, new_y, new_vx, new_vy
      new_x, new_y, new_vx, new_vy, collision = next_ball_pos(self.x, self.y, self.vx, self.vy)
      foresight += 1
    predicting = False
    ceiling = False
    pygame.draw.line(screen, (0, 255, 255), (self.x + BALL_RADIUS + LEFT_WIDTH, self.y + BALL_RADIUS)
      , (new_x + BALL_RADIUS + LEFT_WIDTH, new_y + BALL_RADIUS), 5)

class Peg(GameObject):
  BLUE = 0
  ORANGE = 1
  GREEN = 2
  PURPLE = 3
  SPRITES = [pygame.image.load("img/blue_peg.png"), pygame.image.load("img/orange_peg.png"), 
    pygame.image.load("img/green_peg.png"), pygame.image.load("img/purple_peg.png")]
  HIT_SPRITES = [pygame.image.load("img/blue_peg_hit.png"), 
    pygame.image.load("img/orange_peg_hit.png"), pygame.image.load("img/green_peg_hit.png"), 
    pygame.image.load("img/purple_peg_hit.png")]
  POINTS = [10, 100, 10, 500]
  
  def __init__(self, x, y, type):
    GameObject.__init__(self, x, y)
    self.set_type(type)
    self.is_hit = False
  
  def set_type(self, type):
    self.sprite = self.SPRITES[type]
    self.type = type
  
  def hit(self):
    global zen_shots
    if not self.is_hit:
      self.sprite = self.HIT_SPRITES[self.type]
      hit_pegs.append(self)
      self.is_hit = True
      if self.type == self.ORANGE:
        peg_tracker.add_peg()
      elif self.type == self.GREEN:
        zen_shots += 1
  
  def point_value(self):
    return self.POINTS[self.type]

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
    if (self.y > LEVEL_HEIGHT):
      delete_pegs()
    
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
hit_pegs = []
for x in range(width):
  for y in range(height):
    color = layout.getpixel((x, y))
    if (color[0], color[1], color[2]) == PEG_INDICATOR:
      peg = Peg(x, y, Peg.BLUE)
      objects.append(peg)
      pegs.append(peg)

if not DEBUG:
  if len(pegs) < 27:
    raise SystemExit("There must be at least 27 pegs. Please add pegs to the level.")

  num_pegs = len(pegs)
  random_pegs = list(range(num_pegs))
  for i in range(num_pegs):
    idx = random.randrange(i, num_pegs)
    temp = random_pegs[i]
    random_pegs[i] = random_pegs[idx]
    random_pegs[idx] = temp

  for i in range(25):
    pegs[random_pegs[i]].set_type(Peg.ORANGE)

  for i in range(25, 27):
    pegs[random_pegs[i]].set_type(Peg.GREEN)

  purple_peg = pegs[random_pegs[27]]
  purple_peg.set_type(Peg.PURPLE)

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
ball_statis = 0
delete_frame_idx = 0
def tick():
  global running, PAUSED, STEP, step_count, deleting, delete_frame_idx, ball_stasis
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.MOUSEBUTTONDOWN and not (launching or deleting):
      if event.button == 1:
        launch_ball()
    elif event.type == pygame.KEYUP:
      if DEBUG and event.key == pygame.K_SPACE:
        PAUSED = not PAUSED
      elif DEBUG and event.key == pygame.K_s:
        step_count = 0
    elif DEBUG and event.type == pygame.MOUSEBUTTONUP and event.button == 3:
      mouse_x, mouse_y = pygame.mouse.get_pos()
      mouse_x -= LEFT_WIDTH
      on_peg = False
      for peg in pegs:
        if d_squared((mouse_x, mouse_y), (peg.x + BALL_RADIUS, peg.y + BALL_RADIUS)) < D_SQUARED:
          on_peg = True
          peg.set_type((peg.type + 1) % 4)
          break
      if not on_peg:
        peg = Peg(mouse_x - BALL_RADIUS, mouse_y - BALL_RADIUS, Peg.BLUE)
        pegs.append(peg)
        objects.append(peg)
        
  keys = pygame.key.get_pressed()
  if DEBUG and keys[pygame.K_s]:
    if step_count == 0:
      STEP = True
      PAUSED = False
    step_count = (step_count + 1) % STEP_FRAMES
  
  if not PAUSED or not DEBUG:
    for object in objects:
      object.tick()
    if deleting:
      if deleting_pegs(hit_pegs, delete_frame_idx):
        delete_frame_idx = (delete_frame_idx + 1) % PEG_DELETE_FRAMES
      else:
        deleting = False
        delete_frame_idx = 0
        if not launching:
          finish_launch()
    elif launching:
      if sqrt(ball.vx * ball.vx + ball.vy * ball.vy) <= STILL_BALL:
        ball_stasis += 1
        if ball_stasis >= STILL_BALL_FRAMES:
          deleting = True
      else:
        ball_stasis = 0
  
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
