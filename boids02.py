# 在随便乱跑的01基础上，增加障碍物和避障
import pygame as pg
import sys
from matplotlib import pyplot as pt
from random import randint, choice

# 一些常用参数
FLLSCRN = True  # True for Fullscreen, or False for Window
NUMBERS = 100  # How many boids to spawn, too many may slow fps (200)
BLK_NUMS = 50  # 障碍物数量
WRAP = True  # False avoids edges, True wraps to other side
SPEED = 3  # Movement speed (150)
WIDTH = 1920  # Window Width (1200)
HEIGHT = 1080  # Window Height (800)
BGCOLOR = (30, 30, 50)  # Background color in RGB
BLKCOLOR = (50, 50, 70)  # 障碍物的颜色
FPS = 120  # 帧率
SHOWFPS = True  # frame rate debug
''' 方向图 
1 0 7  x ---->
2 x 6  y
3 4 5  |
       v    '''
MOVE_DIR = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]
TURN_RATE = 3  # 随机转弯的概率

# 全局变量
fps_list = []


class Bird(pg.sprite.Sprite):
    def __init__(self, blocks):
        super().__init__()
        self.image = pg.Surface((15, 15)).convert()
        self.image.fill(BGCOLOR)
        self.color = pg.Color(0)  # preps color so we can use hsva
        self.color.hsva = (randint(0, 360), 90, 90)
        pg.draw.polygon(self.image, self.color, ((7, 0), (13, 14), (7, 11), (1, 14), (7, 0)))
        self.rect = self.image.get_rect()
        for _ in range(10):
            self.rect.centerx = randint(25, WIDTH-25)
            self.rect.centery = randint(25, HEIGHT-25)
            self.check_sprite = pg.sprite.Sprite()
            self.check_sprite.rect = self.rect.inflate(10, 10)
            if pg.sprite.spritecollideany(self.check_sprite, blocks) is None: break
        self.speed = randint(1, SPEED)
        self.dir = randint(0, 7)
        self.orig_image = self.image.copy()
        self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)

    def revert_dir(self):
        self.dir = (self.dir + 4) % 8

    def turn_dir(self):
        if self.dir in (0, 2, 4, 6):
            self.dir = (self.dir + choice((2, -2))) % 8
        else:
            self.dir = (self.dir + choice((1, 2, -1, -2))) % 8

    def update(self, blocks):
        dir_changed = False  # 方向只改变一次，第二次就不改变
        margin = 23  # 距离边沿的距离小于这个值，就开始转弯
        # 先记下原来的位置，遇到边沿或者障碍不能前进，要转弯
        old_x, old_y = self.rect.centerx, self.rect.centery
        self.rect.centerx += MOVE_DIR[self.dir][0] * self.speed
        self.rect.centery += MOVE_DIR[self.dir][1] * self.speed
        if WRAP:
            if self.rect.centerx > WIDTH:
                self.rect.centerx = 0
            elif self.rect.centerx < 0:
                self.rect.centerx = WIDTH
            if self.rect.centery > HEIGHT:
                self.rect.centery = 0
            elif self.rect.centery < 0:
                self.rect.centery = HEIGHT
        else:
            # Avoid edges of screen by turning toward the edge normal-angle
            sc_x, sc_y = self.rect.centerx, self.rect.centery
            if min(sc_x, sc_y, WIDTH - sc_x, HEIGHT - sc_y) < margin:
                # 转弯
                if sc_x < margin:
                    if self.dir == 2: self.dir = choice([1, 3])
                    elif self.dir == 1: self.dir = choice([0, 7])
                    elif self.dir == 3: self.dir = choice([4, 5])
                elif sc_x > WIDTH - margin:
                    if self.dir == 6: self.dir = choice([5, 7])
                    elif self.dir == 7: self.dir = choice([0, 1])
                    elif self.dir == 5: self.dir = choice([4, 3])
                if sc_y < margin:
                    if self.dir == 0: self.dir = choice([7, 1])
                    elif self.dir == 7: self.dir = choice([5, 6])
                    elif self.dir == 1: self.dir = choice([2, 3])
                elif sc_y > HEIGHT - margin:
                    if self.dir == 4: self.dir = choice([3, 5])
                    elif self.dir == 3: self.dir = choice([1, 2])
                    elif self.dir == 5: self.dir = choice([6, 7])
                dir_changed = True
                self.rect.centerx, self.rect.centery = old_x, old_y
                self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
        # 避开障碍物
        self.check_sprite.rect = self.rect.inflate(10, 10)
        if pg.sprite.spritecollideany(self.check_sprite, blocks):
            # self.revert_dir()
            self.turn_dir()
            dir_changed = True
            self.rect.centerx, self.rect.centery = old_x, old_y
            self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
        # 随机转弯
        if not dir_changed and randint(0, 100) < TURN_RATE:
            self.dir += randint(-1, 1)
            if self.dir > 7:
                self.dir = 0
            elif self.dir < 0:
                self.dir = 7
            self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)


class Block(pg.sprite.Sprite):
    def __init__(self, x=None, y=None, w=None, h=None):
        super().__init__()
        if w is None or h is None:
            w, h = randint(15, int(WIDTH / 10)), randint(15, int(HEIGHT / 10))
        self.image = pg.Surface((w, h)).convert()
        self.image.fill(BLKCOLOR)
        self.rect = self.image.get_rect()
        if x is None or y is None:
            x, y = randint(25, WIDTH - w - 25), randint(25, HEIGHT - h - 25)
        self.rect.x = x
        self.rect.y = y


def boids02_app():
    global fps_list
    show_pfs_counter = 0
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    blocks = pg.sprite.Group()
    for _ in range(BLK_NUMS): blocks.add(Block())
    birds = pg.sprite.Group()
    for _ in range(NUMBERS): birds.add(Bird(blocks))
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                return
        birds.update(blocks)
        screen.fill(BGCOLOR)
        blocks.draw(screen)
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
    pt.plot(fps_list)
    pt.show()


if __name__ == '__main__':
    boids02_app()
    pg.quit()
    # show_fps()
    sys.exit()
