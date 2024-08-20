# 在全功能版本03的基础上，大修改，改成0-360度转弯
# 在基线01的基础上，增加2个功能：1）离得太近会分开； 2）方向趋同，尽量跟附近的伙伴保持一个方向
import pygame as pg
import sys
from matplotlib import pyplot as pt
from random import randint, choice
from birds_tongyi import average_angle, find_closest_neighbor, goto_neighbor
from pygame.math import Vector2
import math

# 一些常用参数
FLLSCRN = False  # True for Fullscreen, or False for Window
NUMBERS = 150  # (150) How many boids to spawn, too many may slow fps
WRAP = True  # False avoids edges, True wraps to other side
SPEED = 6  # (10) Movement speed
WIDTH = 1920  # (1920) Window Width - full 3480 /1.5 = 2320
HEIGHT = 1080  # (1080) Window Height - full 2160 / 1.5 = 1440
BGCOLOR = (30, 30, 50)  # Background color in RGB
FPS = 30  # (30)
SHOWFPS = True  # frame rate debug
TURN_RATE = 6  # (6)  随机转弯的概率，1-200
SIGHT = 60  # (60) 视力范围，只关心在此范围内的邻居
MARGIN = 20  # 距离边界不能太近，差不多就好转弯了
MIN_DISTANCE = 16  # 小鸟不能靠得太近
ATTEN_TIMES = 5 # (5) 走多少步才趋同一次

# 全局变量
fps_list = []


def trans_angle(angle):
    '''
    方向调整一下，本程序是上面是0度，逆时针旋转；调用的子程序是右边是0度，顺时针旋转
    参照GitHub上下载的pynboids_sp.py，就不需要这个转换子程序了
    '''
    angle += 90
    angle = 360 - angle
    if angle < 0: angle += 360
    elif angle >=360: angle-= 360
    return angle


class Bird(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((15, 15)).convert()
        self.image.fill(BGCOLOR)
        self.color = pg.Color(0)  # preps color so we can use hsva
        self.color.hsva = (randint(0, 360), 90, 90)
        pg.draw.polygon(self.image, self.color, ((7, 0), (13, 14), (7, 11), (1, 14), (7, 0)))
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = Vector2(self.rect.center)
        self.speed = SPEED
        self.angle = randint(0, 359)
        self.dir = Vector2(1, 0)
        # 方向调整一下，本程序是上面是0度，逆时针旋转；调用的子程序是右边是0度，顺时针旋转
        self.orig_image = pg.transform.rotate(self.image.copy(), -90)
        self.image = pg.transform.rotate(self.orig_image, -self.angle)

    def proc_move(self):
        # 大概率朝原来的方向，小概率随机转弯
        if randint(1, 200) <= TURN_RATE:
            # 随机转弯
            self.angle += (choice((1, -1)) * randint(10, 45)) % 360

        # 根据角度和速度更新位置
        self.dir = Vector2(1, 0).rotate(self.angle).normalize()
        self.pos += self.speed * self.dir
        # Actually update position of boid
        self.rect.center = self.pos

        # 边界检测
        if WRAP:
            # 穿墙模式
            if self.pos.x < 0:
                self.pos.x = WIDTH - 1
            elif self.pos.x >= WIDTH:
                self.pos.x = 0
            if self.pos.y < 0:
                self.pos.y = HEIGHT - 1
            elif self.pos.y >= HEIGHT:
                self.pos.y = 0
        else:
            # 反弹回去
            if self.pos.x < MARGIN or self.pos.x > WIDTH - MARGIN:
                self.angle = (180 - self.angle) % 360
                self.pos.x = max(MARGIN, min(WIDTH - MARGIN, round(self.pos.x)))
            if self.pos.y < MARGIN or self.pos.y > HEIGHT - MARGIN:
                self.angle = (360 - self.angle) % 360
                self.pos.y = max(MARGIN, min(HEIGHT - MARGIN, round(self.pos.y)))
        # 调整小鸟的角度
        self.image = pg.transform.rotate(self.orig_image, -self.angle)

    def update(self, birds):
        # 找出距离小于SIGHT_VIEW的邻居，离自身最近的邻居以及这个邻居的距离
        neighbors, closest_neighbor, distance_of_closest_neighbor = find_closest_neighbor(self, birds)
        if len(neighbors) > 0:
            if distance_of_closest_neighbor < MIN_DISTANCE:
                # 远离最近的邻居
                self.angle = goto_neighbor(self, closest_neighbor, False)
            else:
                # 方向趋同
                self.angle = average_angle([ob.angle for ob in neighbors])
        self.proc_move()


def boids04_app():
    global fps_list
    show_pfs_counter = 0
    pg.init()
    if FLLSCRN:
        screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
        pg.mouse.set_visible(False)
    else:
        screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    birds = pg.sprite.Group()
    for i in range(NUMBERS):
        bird = Bird(randint(25, WIDTH-25), randint(25, HEIGHT-25))
        birds.add(bird)
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                return
        birds.update(birds)
        screen.fill(BGCOLOR)
        birds.draw(screen)
        real_fps = round(clock.get_fps())
        show_pfs_counter += 1
        if show_pfs_counter >= real_fps:
            show_pfs_counter = 0
            pg.display.set_caption(f"实际帧率：{real_fps}")
            if real_fps >= 150: fps_list.append(real_fps)
        pg.display.flip()
        clock.tick(FPS)


def show_fps():
    global fps_list
    pt.plot(fps_list)
    pt.show()


if __name__ == '__main__':
    boids04_app()
    pg.quit()
    # show_fps()
    sys.exit()
