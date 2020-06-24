# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import time
import os
from math import sin, cos, atan, acos, radians, degrees, sqrt

####################################################################################################
# Constants
####################################################################################################
# The width of the screen
SCREEN_WIDTH = 800
# The height of the screen
SCREEN_HEIGHT = 800
# The acceleration (in pixels per second squared) due to gravity
G = 1
# The initial velocity of the ball upon being shot by the cannon (in pixels per second)
V_0 = 15

####################################################################################################
# Helper functions
####################################################################################################
def ball_pos(t, angle, cannon):
  y = 0.5 * G * t * t + V_0 * cos(angle) * t + cannon.y
  x = V_0 * sin(angle) * t + cannon.x
  return x, y;


####################################################################################################
# Classes
####################################################################################################
# The parent class for all game objects
# Fields: sprite, x, y
# Methods: __init__
class GameObject:
  # The constructor for this class
  # Parameter: spritePath the path to the image file containing the sprite for this GameObject
  # Parameter: x the x coordinate of the top left corner of this GameObject on the screen
  # Parameter: y the y coordinate of the top left corner of this GameObject on the screen
  def __init__(self, spritePath, x, y):
    self.sprite = pygame.image.load(spritePath)
    self.x = x
    self.y = y
  
  def draw_on(self, screen):
    screen.blit(self.sprite, (self.x, self.y))

class Cannon(GameObject):
  BASE_X = SCREEN_WIDTH / 2 - 125
  BASE_Y = 0
  
  def __init__(self):
    GameObject.__init__(self, 'img/cannon.png', SCREEN_WIDTH / 2, 0)
    self.base = pygame.image.load('img/cannon_base.png')
    
    self.width = self.sprite.get_width() / 2
    self.height = self.sprite.get_height() / 2
    self.angle = 0
    self.dx = 0
    self.dy = 0
    
  def rot_center(self, rect, angle):
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(self.sprite, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect
  
  def draw_on(self, screen):
    screen.blit(self.base, (self.BASE_X, self.BASE_Y))
    rect = self.sprite.get_rect(center=(self.x + self.dx, self.y + self.dy))
    image, rect = self.rot_center(rect, self.angle)
    screen.blit(image, rect)
  
  def set_angle(self, angle):
    self.angle = (360 + angle % 360) % 360
    rads = radians(self.angle)
    self.dx = (self.width + 20) * sin(rads)
    self.dy = (self.height - 40) * cos(rads)
  
  def path_to_mouse(self):
    v_0x = V_0 * sin(radians(angle))
    v_0y = V_0 * cos(radians(angle))
  
  def tick(self):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - self.x
    dy = mouse_y - self.y
    if(dy == 0):
      if(dx < 0):
        self.set_angle(270)
      else:
        self.set_angle(90)
    else:
      flag = False
      if(dx < 0):
        flag = True
        dx = -1 * dx
      top_term = dy - (G * dx * dx / (V_0 * V_0))
      bottom_term = sqrt(dx * dx + dy * dy)
      side_term = atan(dx / dy)
      angle = (acos(top_term / bottom_term) + atan(dx / dy)) / 2
      if(flag):
        angle = -1 * angle
      self.set_angle(degrees(angle))

class Indicator():
  delta_t = 1
  def tick(self):
    return None
  
  def draw_on(self, screen):
    global cannon
    x = cannon.x
    y = cannon.y
    t = 1
    new_x, new_y = ball_pos(t, radians(cannon.angle), cannon)
    while((x >= 0) & (x < SCREEN_WIDTH) & (y >= 0) & (y < SCREEN_HEIGHT)):
      pygame.draw.line(screen, (0, 255, 255), (x, y), (new_x, new_y), 5)
      t += 1
      x, y = new_x, new_y
      new_x, new_y = ball_pos(t, radians(cannon.angle), cannon)

####################################################################################################
# Initialization
####################################################################################################
print("Enter the level name:")
background = pygame.image.load('levels/' + input() + "/background.png")

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT));
pygame.display.set_caption("Speggle")

cannon = Cannon()
indicator = Indicator()
objects = [cannon, indicator]

####################################################################################################
# Game loop
####################################################################################################
running = True;

def time_check():
  global now
  earlier = now
  later = datetime.now()
  if((later - earlier).microseconds > 16667):
    now = later
    return True
  return False

def tick():
  global running
  global cannon
  global objects
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
  
  for object in objects:
    object.tick()
  
  
def render():
  global objects
  screen.blit(background, (0, 0))
  for object in objects:
    object.draw_on(screen)
  
  pygame.display.update()

now = datetime.now()
while running:
  if(time_check()):
    tick()
    render()
