# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import time
import os
from math import sin, cos, atan, radians, degrees

####################################################################################################
# Constants
####################################################################################################
# The width of the screen
SCREEN_WIDTH = 800
# The height of the screen
SCREEN_HEIGHT = 800

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
      self.set_angle(degrees(atan(dx / dy)))

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
objects = [cannon]

####################################################################################################
# Game loop
####################################################################################################
running = True;
color = [255, 0, 0]

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
