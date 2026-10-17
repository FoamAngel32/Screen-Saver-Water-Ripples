import random
import pygame
from pygame._sdl2 import video
import math
import sys
import numpy as np

MIN_STRENGTH = 5


class Water_source:
    def __init__(self, pos, strength, decade_method, decade, speed):
        self.radius = 0
        self.pos = pos
        self.speed = speed
        self.strength = strength
        self.decade_method = decade_method
        self.decade = decade

    def update(self, world, width, height, delta):
        self.strength = self.decade_method(self.strength, self.decade, delta)
        if int(self.strength) == MIN_STRENGTH:
            return None
        self.radius += self.speed * delta
        if self.radius > 0:
            take_points = 100
            points = []
            for i in range(take_points):
                theta = 2.0 * math.pi * i / take_points
                x = int(self.pos[0] + self.radius * math.cos(theta))
                y = int(self.pos[1] + self.radius * math.sin(theta))
                points.append((x, y))
            for point_id in range(take_points):
                x0 = points[point_id][0]
                y0 = points[point_id][1]
                x1 = points[(point_id + 1) % take_points][0]
                y1 = points[(point_id + 1) % take_points][1]
                dx = abs(x1 - x0)
                dy = abs(y1 - y0)
                sx = 1 if x0 < x1 else -1
                sy = 1 if y0 < y1 else -1
                err = dx - dy
                while True:
                    if 0 <= x0 < width and 0 <= y0 < height:
                        world[y0][x0] += self.strength
                    if x0 == x1 and y0 == y1:
                        break
                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        x0 += sx
                    if e2 < dx:
                        err += dx
                        y0 += sy
        return world


def water_cal(water_sources, w, h, delta):
    world = np.zeros((h, w), dtype=np.float32)
    removing = []
    for water_source in water_sources:
        new_world = water_source.update(world, w, h, delta)
        if new_world is None:
            removing.append(water_source)
            continue
        world = new_world
    return world, removing


def linear_decade(original, minuend, delta):
    return max(MIN_STRENGTH, original - (minuend * delta))


def lerp_decade(original, minuend, delta):
    return max(MIN_STRENGTH, original - ((original - minuend) / 64 * delta))


if __name__ == "__main__":
    boot = 0
    if len(sys.argv) > 1 and sys.argv[1].lower().startswith('/p'):
        boot = 2
        hwnd = int(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1].lower().startswith('/s'):
        boot = 1
    if boot > 0:
        pygame.init()
        # resolution = (640, 480)
        window = None
        renderer = None
        if boot == 1:
            resolution = pygame.display.get_desktop_sizes()[0]
            window = pygame.display.set_mode(resolution, flags=pygame.FULLSCREEN | pygame.SCALED)

        if boot == 2:
            win = video.Window.from_existing_window(hwnd)
            renderer = video.Renderer(win)
            win.size = (320, 240)

        clock = pygame.time.Clock()
        all_water_sources = []
        timer = 30
        last_area1 = 1
        last_area2 = 1
        delta = 0
        mouse_motion_timer = 0
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    rel = pygame.mouse.get_rel()
                    speed = rel[0] ** 2 + rel[1] ** 2
                    if speed > 15:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.KEYDOWN:
                    pygame.quit()
                    sys.exit()
            my_water, gonna_removes = water_cal(all_water_sources, *resolution, delta)
            for gonna_remove in gonna_removes:
                all_water_sources.remove(gonna_remove)
            # surface = pygame.surface.Surface(resolution)
            # for x in range(resolution[0]):
            #     for y in range(resolution[1]):
            #         color = max(0, min(my_water[y][x], 255))
            #         window.set_at((x, y), (color, color, color))
            r = np.asarray(my_water, dtype=np.int64)
            r = np.clip(r, 0, 255).astype(np.uint8)
            surface = pygame.surfarray.make_surface(np.stack([r, r, r], axis=-1).transpose(1, 0, 2))
            if renderer is not None:
                texture = video.Texture(renderer, (320, 240), streaming=True)
                texture.update(surface)
                renderer.clear()
                renderer.blit(texture)
                renderer.present()

            if window is not None:
                window.blit(surface)
                pygame.display.update()
            delta = (clock.tick(60) / 1000.0) * 60
            timer += 1 * delta
            if timer > 30:
                timer = 0
                times = 0
                number = 0
                last_pos = [0, 0]
                while number < 0.65:
                    area1 = last_area1
                    area2 = last_area2
                    retries = 0
                    while area1 == last_area1:
                        retries += 1
                        area1 = random.randint(1, 2)
                        if retries > 3:
                            break
                    while area2 == last_area2:
                        retries += 1
                        area2 = random.randint(1, 2)
                        if retries > 3:
                            break
                    pos = [int(random.random() * (resolution[0] / 2) * area1), int(random.random() * (resolution[1]/2) * area2)]
                    if abs(last_pos[0] - pos[0]) < 100 or abs(last_pos[1] - pos[1]) < 100:
                        continue
                    all_water_sources.append(Water_source(pos, 200, lerp_decade, 0.6, 1))
                    times += 1
                    number = random.random()
                    last_pos = pos
                    last_area1 = area1
                    last_area2 = area2
                    if times >= 2:
                        break

            # print(clock.get_fps())
