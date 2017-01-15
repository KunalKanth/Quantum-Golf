import os, sys
import pygame
from pygame.locals import *
import random
import time
import math

pygame.init()
pygame.font.init()
thefont = pygame.font.SysFont(pygame.font.get_default_font(),30,True)

TIMESCALE = 0.00000001
TIMESTEP = 30 #(milliseconds)
SUBITERS = 20
W = 640
H = 480
W2 = W/2
H2 = H/2

#constants
HBAR = 3.0
MASS = 0.1
A = 1.0

#amount to scale wavefunction height by
HSCALE = 0.2*H2/A

#width, height of perturbation
PHMAX = 100000*HBAR
PW = 0.2*A
PW2 = PW/2
PH = 0.3*PHMAX
#speed of player's perturbation
PSPEED = 0.0001/TIMESCALE
PCHANGE = 0.0005/TIMESCALE*PHMAX

#target properties
TARGW = 0.1*A
TARGW2 = TARGW/2

#number of spatial subdivisions to use for rendering, collapsing
Ns = 100

#quickly check for stability 
#(borrowed from wave equation... is this even valid?)
c = math.sqrt(HBAR/(2.0*MASS))
dt = TIMESTEP*TIMESCALE/SUBITERS
dx = A/Ns
if(c/(dx/dt) > 1):
    print "WARNING: numerical scheme is likely unstable"

#set up array of position coefficients (initialize to zeros)
c = []
dc = []
for i in range(0,Ns+1):
    c.append(complex(0.0,0.0))
    dc.append(complex(0.0,0.0))

#set up an array for use while collapsing the wavefunction
colarray = []
for i in range(0,Ns+1):
    colarray.append(0.0)

#function to normalize the c array
def normalizec():
    s = 0.0
    for i in c:
        s += (i*i.conjugate()).real*A/Ns
    s = math.sqrt(s)
    for i in range(0,Ns+1):
        c[i] = c[i]/s

#gaussian
def gaussian(x,a):
    return math.exp(-((x/a)**2))

#function to get a normalized gaussian (what the wave function collapses to
#when position is measured at x)
def setasgauss(x):
    for i in range(1,Ns):
        xi = i*A/Ns
        c[i] = complex(gaussian(x-xi,A/20),0)
    normalizec()

#get a pixel offset from an x value, assuming that [0,A] covers the whole
#width of the screen
def toscreenx(x):
    return int(x*W/A)
#get the pixel offset from a y value (wavefunction)
def toscreeny(y):
    return int(H2 - y*HSCALE)

#set the wavefunction at time t, render to surface s
def renderwf(t,s):
    lastpos = (toscreenx(0),toscreeny(0))
    for i in range(0,Ns+1):
        x = i*A/Ns
        pos = (toscreenx(x),toscreeny(c[i].real))
        pygame.draw.line(s,(255,255,255), lastpos, pos)
        lastpos = pos

#pick value of x to collapse to, based on current c array
def randomlychooseposition():
    totalsum = 0.0
    for i in range(0,Ns+1):
        i2 = float((c[i]*c[i].conjugate()).real)
        totalsum += i2
        colarray[i] = totalsum
    decider = random.random()*totalsum
    for i in range(0,Ns+1):
        if(colarray[i] > decider):
            return i*A/Ns
    return A

#laplacian operator acting on some index of c (assumed not to be an endpt)
def laplace(i):
    return (c[i+1]-2.0*c[i]+c[i-1])/(A/Ns)**2
#update the c array for a perturbation at x, at time t, for change dt
def updatecoeffs(x,dt):
    sp = x-PW2
    ep = x+PW2
    for i in range(1,Ns):
        dc[i] = complex(0,1)*HBAR*laplace(i)/(2.0*MASS)
        x = i*A/Ns
        if(x>sp and x<ep):
            dc[i] -= complex(0,1)*PH/HBAR*c[i]
    for i in range(1,Ns):
        c[i] += dc[i]*dt
    normalizec()

#draw the perturbation as a grey rectangle at the bottom of the screen and
#two lines extending to the top
def drawperturb(x,s):
    left = toscreenx(x-PW2)
    right = toscreenx(x+PW2)
    w = right-left
    h = PH/PHMAX*H
    top = H - h
    r = pygame.Rect(left, top, w, h)
    c = (100,100,100)
    pygame.draw.rect(s,(80,80,80),r)
    pygame.draw.line(s,c,(left,0),(left,H))
    pygame.draw.line(s,c,(right,0),(right,H))

#draw the target area
def drawtarget(x,s):
    left = toscreenx(x-TARGW2)
    right = toscreenx(x+TARGW2)
    w = right-left
    r = pygame.Rect(left,0,w,H)
    pygame.draw.rect(s,(0,80,0),r)
    pygame.draw.line(s,(0,255,0),(left,0),(left,H))
    pygame.draw.line(s,(0,255,0),(right,0),(right,H))

    #pick an x location for target
def picktarget(lastx):
    while(True):
        x = random.random()*A
        if(x < TARGW2):
            x = TARGW2
        if(x > A-TARGW2):
            x = A-TARGW2
        if(abs(x-lastx) > 2*TARGW):
            return x

#test whether a position is inside of a target
def intarget(x,tx):
    return x < tx + TARGW2 and x > tx - TARGW2

#draw stats to some surface, s
def drawstats(swings, holes, s):
    txts = "SWINGS: %i" %(swings,)
    txth = "HOLES: %i" %(holes,)
    ts = thefont.render(txts, False, (255,255,255))
    th = thefont.render(txth, False, (255,255,255))
    s.blit(ts, (W-220,0))
    s.blit(th, (W-220,ts.get_height()))

#Game LOOP
screen = pygame.display.set_mode((W, H), 0)
pygame.mouse.set_visible(False)
t=0.0
lt = 0.0
left = False
right = False
up = False
down = False
dopause = False

px = PW2
tx = picktarget(px+PW)
setasgauss(px+PW)
holes = 0
swings = 0
while(True):

    screen.fill((0,0,0))

    for event in pygame.event.get():
        if(event.type == QUIT):
            pygame.quit()
            
        elif(event.type == KEYDOWN):
            
            if(event.key == K_LEFT):
                left = True
            elif(event.key == K_RIGHT):
                right = True
            elif(event.key == K_UP):
                up = True
            elif(event.key == K_DOWN):
                down = True
            elif(event.key == K_SPACE):
                swings += 1
                x = randomlychooseposition()
                if(intarget(x,tx)):
                    holes += 1
                    dopause = True
                setasgauss(x)

            if(event.key == K_ESCAPE):
                pygame.quit()
                
        elif(event.type == KEYUP):
                    
            if(event.key == K_LEFT):
                left = False
            elif(event.key == K_RIGHT):
                right = False
            elif(event.key == K_UP):
                up = False
            elif(event.key == K_DOWN):
                down = False

    t = pygame.time.get_ticks()
    if(t >= lt):
        n=0
        while(t >= lt):
            lt += TIMESTEP
            n += 1
        #if(n > 1):
        #    print "WARNING: insufficient framerate"
        dt = float(n*TIMESTEP*TIMESCALE)
        if(left):
            px = max(px-PSPEED*dt,PW2)
        if(right):
            px = min(px+PSPEED*dt,A-PW2)
        if(up):
            PH = min(PH+PCHANGE*dt,PHMAX)
        if(down):
            PH = max(PH-PCHANGE*dt,0)
        #reset coeffs several times, to have smaller timesteps (more stable)
        for i in range(0,SUBITERS):
            updatecoeffs(px,dt/SUBITERS)
        drawperturb(px,screen)
        drawtarget(tx,screen)
        renderwf(t,screen)
        drawstats(swings, holes, screen)
        pygame.display.flip()
        if(dopause):
            time.sleep(1)
            dopause = False
            tx = picktarget(tx)
