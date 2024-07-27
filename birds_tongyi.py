# 用通义灵码辅助写的程序，比百度写的好很多
import pygame
import random
import math

# 常用
USE_EAGLE = True  # 是否出现老鹰
GO_THROUGH = True  # 遇到边界是穿越到另外一边，还是反弹回去
SHOW_PATH = False  # 显示移动路径
FPS = 30  # 帧率
BIRD_SPEED = 8  # 速度
EAGLE_SPEED = 7
BIRD_NUM = 100  # 鸟的数量
EAGLE_NUM = 3
PATH_LEN = 100  # 显示移动路径的长度
TURN_RATE = 6  # 随机转弯的概率，1-200
screen_width = 1600
screen_height = 900
BIRD_SIZE = 5
EAGLE_SIZE = 5
MARGIN = 8  # 距离边界不能太近，差不多就好转弯了
SIGHT_VIEW = 50  # 视野范围
MIN_DISTANCE = 11  # 小鸟不能靠得太近
# 颜色
BACK_GROUND_COLOR = (245, 245, 255)  # 浅灰偏蓝
BIRD_PATH_COLOR = (200, 200, 200)  # 淡灰色
EAGLE_PATH_COLOR = (20, 20, 20)  # 黑色
EAGLE_COLOR = (255, 0, 0)  # 红色
BIRD_COLOR = (0, 255, 0)  # 绿色
# 加载鸟和老鹰的图像
try:
    bird_image = pygame.image.load('bird.png')
except Exception as e:
    print("load bird img failed: ", e)
    bird_image = None
try:
    eagle_image = pygame.image.load('eagle.png')
except Exception as e:
    print("load eagle img failed: ", e)
    bird_image = None


def average_angle(angles):
    """
    计算一组角度的平均值。
    参数:
    angles : 角度的列表，每个角度的范围应该是0到360度。
    返回: int 角度的平均值。
    """
    # 将角度转换为弧度
    radians = [math.radians(angle) for angle in angles]
    # 计算x和y坐标的平均值
    avg_x = sum(math.cos(radian) for radian in radians) / len(radians)
    avg_y = sum(math.sin(radian) for radian in radians) / len(radians)
    # 反转换回角度
    avg_radian = math.atan2(avg_y, avg_x)
    # 将结果转换回0-360度的角度，并四舍五入到整数
    avg_angle = round(math.degrees(avg_radian))
    if avg_angle < 0:
        avg_angle += 360
    return avg_angle


def find_closest_neighbor(myself, objects):
    """
    找出距离小于SIGHT_VIEW的邻居，离自身最近的邻居以及这个邻居的距离
    参数:
    birds : list of Object 物体的列表。
    返回:
    tuple of lists
        第一个元素是距离小于SIGHT_VIEW的邻居；
        第二个元素是最近的邻居；
        第三个元素最近邻居的距离。
    """
    neighbors = []
    closest_neighbor = None
    distance_of_closest_neighbor = None
    min_distance = 10000

    for ob in objects:
        if ob != myself:
            distance = math.sqrt((ob.x - myself.x) ** 2 + (ob.y - myself.y) ** 2)
            if distance < SIGHT_VIEW:
                neighbors.append(ob)
                # 更新最近的邻居
                if distance < min_distance:
                    min_distance = distance
                    closest_neighbor = ob
                    distance_of_closest_neighbor = distance
    return neighbors, closest_neighbor, distance_of_closest_neighbor


# 通用的移动物体的类
class Object:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.randint(0, 359)  # 随机角度
        self.speed = 5
        self.size = 5
        self.path = []

    def proc_move(self):
        # 大概率朝原来的方向，小概率随机转弯
        if random.randint(1, 200) <= TURN_RATE:
            # 随机转弯
            self.angle = (self.angle + (random.choice((1, -1)) * random.randint(10, 45))) % 360

        # 更新路径记录
        self.path.append((self.x, self.y))
        # 限制路径长度，避免消耗过多内存
        if len(self.path) > PATH_LEN:
            self.path.pop(0)

        # 根据角度和速度更新位置
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y += self.speed * math.sin(math.radians(self.angle))

        # 边界检测
        if GO_THROUGH:
            # 穿墙模式
            if self.x < 0:
                self.x = screen_width - 1
                self.path.clear()
            elif self.x >= screen_width:
                self.x = 0
                self.path.clear()
            if self.y < 0:
                self.y = screen_height - 1
                self.path.clear()
            elif self.y >= screen_height:
                self.y = 0
                self.path.clear()
        else:
            # 反弹回去
            if self.x < MARGIN or self.x > screen_width - MARGIN:
                self.angle = (180 - self.angle) % 360
                self.x = max(MARGIN, min(screen_width - MARGIN, self.x))
            if self.y < MARGIN or self.y > screen_height - MARGIN:
                self.angle = (360 - self.angle) % 360
                self.y = max(MARGIN, min(screen_height - MARGIN, self.y))


# 小鸟的类
class Bird(Object):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = BIRD_SIZE
        self.speed = BIRD_SPEED

    def move(self, birds, eagles):
        ''' 小鸟的飞行规则，优先级从高到低
        1. 躲避老鹰
        2. 避免太挤
        3. 方向趋同
        4. 小概率随机转弯
        最后是边界处理 '''
        if USE_EAGLE:
            # 找出视力范围内，离自身最近的老鹰
            _, closest_eagle, _ = find_closest_neighbor(self, eagles)
            if closest_eagle:
                # 远离最近的老鹰
                self.angle = (math.degrees(math.atan2(closest_eagle.y - self.y, closest_eagle.x - self.x))
                              + 180) % 360
        if not USE_EAGLE or not closest_eagle:
            # 找出距离小于SIGHT_VIEW的邻居，离自身最近的邻居以及这个邻居的距离
            neighbors, closest_neighbor, distance_of_closest_neighbor = find_closest_neighbor(self, birds)
            if len(neighbors) > 0:
                if distance_of_closest_neighbor < MIN_DISTANCE:
                    # 远离最近的邻居
                    self.angle = (math.degrees(math.atan2(closest_neighbor.y - self.y, closest_neighbor.x - self.x))
                                  + 180) % 360
                else:
                    # 方向趋同
                    self.angle = average_angle([ob.angle for ob in neighbors])
        self.proc_move()

    def draw(self, screen):
        pygame.draw.circle(screen, BIRD_COLOR, (int(self.x), int(self.y)), self.size)
        # 画出路径
        if SHOW_PATH and len(self.path) > 1:
            path_points = [(int(x), int(y)) for x, y in self.path]
            pygame.draw.lines(screen, BIRD_PATH_COLOR, False, path_points, 1)

    def draw_img(self, screen):
        if bird_image:
            screen.blit(bird_image, (int(self.x), int(self.y)))
        else:
            self.draw(self)


# 老鹰的类
class Eagle(Object):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = EAGLE_SIZE
        self.speed = EAGLE_SPEED

    def move(self, birds):
        # 找出视力范围内，离自身最近的小鸟
        _, closest_neighbor, _ = find_closest_neighbor(self, birds)
        if closest_neighbor:
            # 追逐最近的小鸟
            self.angle = (math.degrees(math.atan2(closest_neighbor.y - self.y, closest_neighbor.x - self.x))) % 360
        self.proc_move()

    def draw(self, screen):
        pygame.draw.circle(screen, EAGLE_COLOR, (int(self.x), int(self.y)), self.size)
        # 画出路径
        if SHOW_PATH and len(self.path) > 1:
            path_points = [(int(x), int(y)) for x, y in self.path]
            pygame.draw.lines(screen, EAGLE_PATH_COLOR, False, path_points, 1)

    def draw_img(self, screen):
        if eagle_image:
            screen.blit(eagle_image, (int(self.x), int(self.y)))
        else:
            self.draw(self)


def bird02_app():
    # 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    # 创建时钟对象
    clock = pygame.time.Clock()
    # 设置标题
    pygame.display.set_caption("Random Flying Birds")
    # 创建小鸟列表
    birds = [Bird(random.randint(MARGIN, screen_width-MARGIN), random.randint(MARGIN, screen_height-MARGIN))
             for _ in range(BIRD_NUM)]
    # 创建老鹰列表
    eagles = [Eagle(random.randint(MARGIN, screen_width-MARGIN), random.randint(MARGIN, screen_height-MARGIN))
              for _ in range(EAGLE_NUM)]
    # 游戏主循环
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # 检查按键事件
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # 清屏
        screen.fill(BACK_GROUND_COLOR)
        # 更新并绘制小鸟
        for bird in birds:
            bird.move(birds,eagles)
            bird.draw(screen)
        if USE_EAGLE:
            # 更新并绘制老鹰
            for eagle in eagles:
                eagle.move(birds)
                eagle.draw(screen)
                eagle.draw(screen)
        # 更新屏幕
        pygame.display.flip()
        # 控制帧率
        clock.tick(FPS)  # 设置每秒10帧
    # 退出Pygame
    pygame.quit()


if __name__ == '__main__':
    bird02_app()
