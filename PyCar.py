import pygame
import os
import math
import sys
import random
import neat

screen_width = 1500
screen_height = 800
generation = 0

class Car:
    def __init__(self):
        self.surface = pygame.image.load("car.png")
        self.surface = pygame.transform.scale(self.surface, (100, 100))
        self.rotate_surface = self.surface
        self.pos = [700, 650]
        self.angle = 0
        self.speed = 0
        self.center = [self.pos[0] + 50, self.pos[1] + 50]
        self.radars = []
        self.radars_for_draw = []
        self.is_alive = True
        self.goal = False
        self.distance = 0
        self.time_spent = 0

    def draw(self, screen):
        screen.blit(self.rotate_surface, self.pos)
        self.draw_radar(screen)

    def draw_radar(self, screen):
         for r in self.radars:
             pos, dist = r
             pygame.draw.line(screen, (0, 255, 0), self.center, pos, 1) #the number coordinates denote green colour and 1 is the size
             pygame.draw.circle(screen, (0, 255, 0), pos, 5)

    def check_collision(self, map):
        self.is_alive = True
        for p in self.four_points:
            if map.get_at((int(p[0]), int(p[1]))) == (255, 255, 255, 255):
                self.is_alive = False #if map.get_at checks whether the colour at of the pixel at point p is white and if white the car is considered not alive.
                break

    def check_radar(self, degree, map): #degree is the angle relative to car's position to check for obstacles. Map is a pygame surface obj.
        len = 0 #begins with 0 denoting the start of radar scanning from car's center.
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len) #mathematical method to calculate x,y coords
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)

        while not map.get_at((x, y)) == (255, 255, 255, 255) and len < 300: #300 is max pixel range.
            len = len + 1 #As len increases the x,y coordinates of the radar are recalculated.
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)

        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))  #Computes the Euclidean distance from the vehicle’s center to the point (x, y) where the radar detected an obstacle. This distance is calculated using the Pythagorean theorem.
        
        self.radars.append([(x, y), dist]) #updates the radar coords

    def update(self, map): #Updates the car's state based on its current position, orientation, and speed.
        
        #speed check
        self.speed = 10 #Sets the car's speed to a constant value of 15 units per frame
        #position check
        self.rotate_surface = self.rot_center(self.surface, self.angle)
        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        #if the car's X-coordinate goes beyond the left boundary (< 20), it's set to 20. If it exceeds the right boundary (> screen_width - 120), it's set to screen_width - 120.
        if self.pos[0] < 20: 
            self.pos[0] = 20
        elif self.pos[0] > screen_width - 120:
            self.pos[0] = screen_width - 120
            
        #Dist and Time update
        self.distance += self.speed
        self.time_spent += 1
        
        #Position Update (Y-axis) and Boundary Check (Y-axis)
        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        if self.pos[1] < 20:
            self.pos[1] = 20
        elif self.pos[1] > screen_height - 120:
            self.pos[1] = screen_height - 120

        # calculate 4 collision points
        #These points are intended to represent the corners of the car for collision detection purposes.
        self.center = [int(self.pos[0]) + 50, int(self.pos[1]) + 50]
        len = 40
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * len]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * len]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * len]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * len]
        self.four_points = [left_top, right_top, left_bottom, right_bottom]
        #30,150,210,330 degrees are added to the car's angle to compute the respective corners coords
        self.check_collision(map) #detects if any of the 4 pts have collided with the obstacles/boundaries on the map.
        
        #Clear and check radars
        self.radars.clear() #Clears the existing radar data to ensure that the radar readings are fresh each time they are checked.
        for d in range(-90, 120, 45):
            self.check_radar(d, map) 

    def get_data(self):
        radars = self.radars
        ret = [0, 0, 0, 0, 0]
        for i, r in enumerate(radars):
            ret[i] = int(r[1] /5)

        return ret

    def get_alive(self):
        return self.is_alive

    def get_reward(self):
        return self.distance / 50.0

    def rot_center(self, image, angle):
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        return rot_image

def run_car(genomes, config):

    # Init NEAT
    nets = []
    cars = []

    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        car= Car()
        car.pos= [random.randint(100,screen_width-200), random.randint(100,screen_height-200)]
        cars.append(Car())

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    frame_rate= 30
    generation_font = pygame.font.SysFont("Fixedsys", 70)
    font = pygame.font.SysFont("Fixedsys", 30)
    map = pygame.image.load('map3.png')


    global generation
    generation += 1
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)


        for index, car in enumerate(cars):
            output = nets[index].activate(car.get_data())
            i = output.index(max(output))
            if i == 0:
                car.angle += 10
            else:
                car.angle -= 10

        remain_cars = 0
        for i, car in enumerate(cars):
            if car.get_alive():
                remain_cars += 1
                car.update(map)
                genomes[i][1].fitness += car.get_reward()

        if remain_cars == 0:
            break

        screen.blit(map, (0, 0))
        for car in cars:
            if car.get_alive():
                car.draw(screen)

        text = generation_font.render("Generation : " + str(generation), True, (0, 255, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, 100)
        screen.blit(text, text_rect)

        text = font.render("Remaining cars : " + str(remain_cars), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, 200)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(35)

if __name__ == "__main__":
    config_path = "./config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    pygame.time.delay(10000)
    p.run(run_car, 50)