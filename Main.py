import pygame
from pygame.locals import *
import sys 
import math
import numpy
import time

pygame.init()

class RenderData:
    def __init__(self):
        self.width = 900
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.SKY = (84,238,255)
        self.camX = 0
        self.camY = 0

class ObjectRegistry:
    def __init__(self):
        self.registry = []

renderData = RenderData()
objectRegistry = ObjectRegistry()
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Rectangle:
    def __init__(self, x, y, width, height, objectType, color, borderRadius = 3):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.objectType = objectType
        self.color = color
        self.xRel = 0
        self.yRel = 0
        self.borderRadius = borderRadius
        self.vertices = [Point(), Point(), Point(), Point()]
        objectRegistry.registry.append(self)
    def setPose(self, x, y):
        self.x = x
        self.y = y
    def touching(self, item):
        if item.x + item.width/2 > self.x - self.width/2 and item.x - item.width/2 < self.x + self.width/2 and item.y + item.height/2 > self.y - self.height/2 and item.y - item.height/2 < self.y + self.height/2:
            return True
        else:
            return False
    def update(self):
        self.xRel = self.x - renderData.camX
        self.yRel = self.y - renderData.camY
    def convert(self): #converts coordinates to pygame system
        self.xRel += renderData.width/2
        self.yRel = renderData.height/2 - self.yRel
    def clip(self): #if really big rectangles don't get clipped, pygame (being smart) trys to draw all of the parts outside of the screen and makes everything laggy
        self.vertices[0].x = self.xRel - self.width/2
        self.vertices[0].y = self.yRel - self.height/2
        self.vertices[1].x = self.xRel + self.width/2
        self.vertices[1].y = self.yRel - self.height/2
        self.vertices[2].x = self.xRel + self.width/2
        self.vertices[2].y = self.yRel + self.height/2
        self.vertices[3].x = self.xRel - self.width/2
        self.vertices[3].y = self.yRel + self.height/2
        for point in self.vertices:
            if point.x < 0:
                point.x = 0
            if point.x > renderData.width:
                point.x = renderData.width
            if point.y < 0:
                point.y = 0
            if point.y > renderData.height:
                point.y = renderData.height
    def draw_from_vertices(self, top_left, top_right, bottom_right, bottom_left):
        pygame.draw.rect(renderData.screen, self.color, pygame.Rect(top_left.x, top_left.y, top_right.x-top_left.x, bottom_left.y-top_left.y), 0, self.borderRadius)
    def display(self):
        self.update()
        self.convert()
        self.clip()
        self.draw_from_vertices(self.vertices[0], self.vertices[1], self.vertices[2], self.vertices[3])
class GrassBlock:
    def __init__(self, x, y, width, height, objectType = "terrain", color = (0,0,0)):
        grassHeight = 35
        self.bottom = Rectangle(x, y-grassHeight/2, width, height-grassHeight, objectType, (200,100,45), 5)
        self.grass = Rectangle(x, y+height/2-grassHeight/2, width, grassHeight, objectType, (70,240,40), 5)
def repeatObjects(function, iterations):
    i = 0
    while i < iterations:
        function(i)
        i+=1
class timer:
    def __init__(self):
        self.startTimestamp = time.time()
    def elapsedTime(self):
        return time.time()-self.startTimestamp
    def reset(self):
        self.startTimestamp = time.time()

class keyHandlerClass:
    def __init__(self, myKey):
        self.myKey = myKey
    def ifActive(self, pressed): #to be called whenever the kinematics class updates
        if pressed[self.myKey]:
            return 10
        else:
            return 0
        self.reset()
        return elapsedTime
    def reset(self):
        return

class kinematicsClass:
    def __init__(self):
        self.rightKey = keyHandlerClass(pygame.K_RIGHT)
        self.leftKey = keyHandlerClass(pygame.K_LEFT)
        self.upKey = keyHandlerClass(pygame.K_UP)
        self.downKey = keyHandlerClass(pygame.K_DOWN)
        self.xTimer = timer()
        self.yTimer = timer()
        self.camTimer = timer()
        self.fallVel = 0
        self.jumpVel = 0
        self.xDisplacement = 0
        self.yDisplacement = 0
        self.momentum = 0
        self.playerX = 0
        self.playerY = 100
        self.momentumDecayRate = 0.8
        self.camMultiplier = 5
    def getXDisplacement(self):
        pressed = pygame.key.get_pressed()
        dt = self.xTimer.elapsedTime()
        self.momentum = self.momentum * ( (1-self.momentumDecayRate) ** dt)
        self.xDisplacement = ((self.rightKey.ifActive(pressed)-self.leftKey.ifActive(pressed)) + self.momentum)    
        self.momentum = self.xDisplacement
        self.xDisplacement *= dt
        self.xDisplacement = numpy.clip(self.xDisplacement, -700*dt, 700*dt)
        self.xTimer.reset()
    def getYDisplacement(self):
        if self.playerY < -4500:
            self.die()
        pressed = pygame.key.get_pressed()
        self.fallVel += self.yTimer.elapsedTime()*-2000
        self.yDisplacement = self.yTimer.elapsedTime()*(self.fallVel + self.jumpVel)
        self.yTimer.reset()
    def touching(self, player):
        returnValue = "Null"
        for item in objectRegistry.registry:
            if item.objectType != "player":
                if item.touching(player):
                    if item.objectType != "death":
                        return item.objectType
                    else:
                        returnValue = "death"
        return returnValue
    def correct(self, correctionType, player, vel):
        if correctionType == "x":
            self.playerX -= 0.5 * vel/abs(vel)
        else:
            self.playerY -= 0.5 * vel/abs(vel)
        player.setPose(self.playerX, self.playerY)
    def collide(self, player):
        objectType = "Null"
        pressed = pygame.key.get_pressed()
        self.playerX += self.xDisplacement
        player.setPose(self.playerX, self.playerY)
        objectTypeX = self.touching(player)
        if objectTypeX != "Null":
            while self.touching(player) != "Null":
                self.correct("x", player, self.xDisplacement)
            self.playerX = round(self.playerX)
            if pressed[pygame.K_UP]:
                self.momentum = -650*self.xDisplacement/abs(self.xDisplacement)
                self.fallVel = 0
                self.jumpVel = 550
            else:
                self.momentum = 0
        self.playerY += self.yDisplacement
        player.setPose(self.playerX, self.playerY)
        objectTypeY = self.touching(player)
        if objectTypeY != "Null":
            while self.touching(player) != "Null":
                self.correct("y", player, self.yDisplacement)
            if pressed[pygame.K_UP] and self.yDisplacement < 0:
                self.jumpVel = 900
            else:
                self.jumpVel = 0
            self.fallVel = 0
            self.playerY = round(self.playerY)
            player.setPose(self.playerX, self.playerY)
        if objectTypeX == "death" or objectTypeY == "death":
            self.die()
        elif objectTypeY == "bounce":
            self.jumpVel = 1500
    def moveCam(self):
        renderData.camX += (self.playerX - renderData.camX) * self.camTimer.elapsedTime() * self.camMultiplier
        renderData.camY += (self.playerY  - renderData.camY) * self.camTimer.elapsedTime() * self.camMultiplier
        self.camTimer.reset()        
    def reset(self):
        self.rightKey.reset()
        self.leftKey.reset()
        self.upKey.reset()
        self.downKey.reset()
        self.xTimer.reset()
        self.yTimer.reset()
    def die(self):
        self.playerX = 0
        self.playerY = 100
        self.reset()

grassBlock1 = GrassBlock(0, -200, 4000, 500)
grassBlock2 = GrassBlock(-2050, 550, 50, 1000)
repeatObjects(lambda i : Rectangle(400*i - 1900, 75, 50, 50, "terrain", (255,0,0)), iterations = 10)
repeatObjects(lambda i : Rectangle(400*i - 1700, 75, 50, 50, "bounce", (247,104,255)), iterations = 10)
player = Rectangle(0, 0, 50, 50, "player", (100,100,255))
kinematics = kinematicsClass()

def runPhysics():
    kinematics.getXDisplacement()
    kinematics.getYDisplacement()
    kinematics.collide(player)
    kinematics.moveCam()

def displayAll():
    renderData.screen.fill(renderData.SKY)
    for item in objectRegistry.registry:
        item.display()
    pygame.display.update()

def loop():
    runPhysics()
    displayAll()
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

while True:
    loop()
