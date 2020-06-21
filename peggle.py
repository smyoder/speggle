# A simplified version of the game "Peggle"
# Author: Spencer Yoder
import pygame
from datetime import datetime
import time
import os

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
    GameObject.__init__(self, 'img/cannon.png', SCREEN_WIDTH / 2 - 40, 0)
    self.base = pygame.image.load('img/cannon_base.png')
    self.angle = 0
  
  def draw_on(self, screen):
    screen.blit(self.base, (self.BASE_X, self.BASE_Y))
    screen.blit(pygame.transform.rotate(self.sprite, self.angle), (self.x, self.y))
  
  def rotate(self, d_theta):
    self.angle = (360 + (self.angle + d_theta) % 360) % 360

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
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
  
  cannon.rotate(0.5)
  
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
