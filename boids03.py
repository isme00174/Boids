# 在基线01的基础上，增加2个功能：1）离得太近会分开； 2）方向趋同，尽量跟附近的伙伴保持一个方向
import pygame as pg
import sys
from matplotlib import pyplot as pt
from random import randint, choice

# 一些常用参数
FLLSCRN = False  # True for Fullscreen, or False for Window
NUMBERS = 80  # (80) How many boids to spawn, too many may slow fps
WRAP = True  # False avoids edges, True wraps to other side
SPEED = 2  # (2) Movement speed
WIDTH = 1200  # (1200) Window Width
HEIGHT = 700  # (700) Window Height
BGCOLOR = (30, 30, 50)  # Background color in RGB
FPS = 100  # (100)
SHOWFPS = True  # frame rate debug
TURN_RATE = 3  # (3) 随机转弯的概率
SIGHT = 50  # (50) 视力范围，只关心在此范围内的邻居
ATTEN_TIMES = 5  # (5) 走多少步才趋同一次
''' 方向图 
1 0 7  x ---->
2 x 6  y
3 4 5  |
       v    '''
MOVE_DIR = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]

# 全局变量
fps_list = []


class Bird(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((15, 15)).convert()
        self.image.fill(BGCOLOR)
        self.color = pg.Color(0)  # preps color so we can use hsva
        self.color.hsva = (randint(0, 360), 90, 90)
        pg.draw.polygon(self.image, self.color, ((7, 0), (13, 14), (7, 11), (1, 14), (7, 0)))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = randint(1, SPEED)
        self.dir = randint(0, 7)
        self.orig_image = self.image.copy()
        self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
        self.to_round_counter = 0  # 每次都转向会震荡，走几步再趋同一次

    def get_nei_list(self, birds):
        nei_list = []
        my_x, my_y = self.rect.center
        for spri in birds:
            if spri is self: continue
            dx = abs(my_x - spri.rect.centerx)
            dy = abs(my_y - spri.rect.centery)
            if dx <= SIGHT and dy <= SIGHT:
                nei_list.append(spri)
        return nei_list

    def get_nei_dir(self, nei_list):
        dir_list = []
        for spri in nei_list:
            dir_list.append(spri.dir)
        return dir_list

    def turn_to_around(self, dir_list):
        # 步骤1：方向列表减去自身方向
        adjusted_dirs = [nd - self.dir for nd in dir_list]
        # 步骤2：从列表中去掉4和-4
        filtered_dirs = [d for d in adjusted_dirs if d not in (4, -4)]
        # 步骤3：方向大于5则减8，小于-5则加8
        normalized_dirs = [d - 8 if d >= 5 else d + 8 if d <= -5 else d for d in filtered_dirs]
        # 步骤4：计算列表中的数字的平均值
        if normalized_dirs:  # 确保列表非空，避免除以零错误
            avg_dir = round(sum(normalized_dirs) / len(normalized_dirs))
            if avg_dir == 0: turn_dir = 0
            else:
                turn_dir = -1 if avg_dir < 0 else 1
        else:
            turn_dir = 0  # 如果经过过滤后列表为空，可视为没有有效方向，0不转弯
        self.dir = (self.dir + turn_dir) % 8

    # 只要有一个邻居太近，就返回True，否则返回False
    def is_too_close(self, birds):
        my_x, my_y = self.rect.center
        for spri in birds:
            if spri is self: continue
            dx = abs(my_x - spri.rect.centerx)
            dy = abs(my_y - spri.rect.centery)
            if dx <= 10 and dy <= 10: return True
        return False

    def update(self, birds):
        margin = 23  # 距离边沿的距离小于这个值，就开始转弯
        # 先记下原来的位置，遇到边沿或者障碍不能前进，要转弯
        old_x, old_y = self.rect.centerx, self.rect.centery
        self.rect.centerx += MOVE_DIR[self.dir][0] * self.speed
        self.rect.centery += MOVE_DIR[self.dir][1] * self.speed
        dir_changed = False  # 距离转过弯没有，有则不继续转弯
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
                self.rect.centerx, self.rect.centery = old_x, old_y
                dir_changed = True
                self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
        if not dir_changed:
            self.to_round_counter += 1
            if self.to_round_counter >= ATTEN_TIMES:
                self.to_round_counter = 0
                # 判断是否太近
                if self.is_too_close(birds):
                    self.dir = (self.dir + choice((1, -1))) % 8
                    self.rect.centerx, self.rect.centery = old_x, old_y
                    dir_changed = True
                    self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
                #
                else:
                    # 方向趋同
                    nei_list = self.get_nei_list(birds)
                    dir_list = self.get_nei_dir(nei_list)
                    self.turn_to_around(dir_list)
                    dir_changed = True
                    self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)
        # 没有其他事情，随机转弯
        if not dir_changed and randint(0, 100) < TURN_RATE:
            self.dir += randint(-1, 1)
            if self.dir > 7:
                self.dir = 0
            elif self.dir < 0:
                self.dir = 7
            self.image = pg.transform.rotate(self.orig_image.copy(), self.dir * 45)


def boids03_app():
    global fps_list
    show_pfs_counter = 0
    pg.init()
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
    boids03_app()
    pg.quit()
    # show_fps()
    sys.exit()
