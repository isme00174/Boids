# 用通义灵码辅助写的程序，比百度写的好很多
import pygame
from pygame.math import Vector2
import random
import math

# 常用
USE_EAGLE = True  # 是否出现老鹰
GO_THROUGH = True  # 遇到边界是穿越到另外一边，还是反弹回去
SHOW_PATH = False  # 显示移动路径
FPS = 30  # 帧率
BIRD_SPEED = 10  # 速度
EAGLE_SPEED = 9
BIRD_NUM = 400  # 鸟的数量
EAGLE_NUM = 3
PATH_LEN = 20  # 显示移动路径的长度
TURN_RATE = 6  # 随机转弯的概率，1-200
screen_width = 2000
screen_height = 1200
BIRD_SIZE = 5
EAGLE_SIZE = 5
MARGIN = 8  # 距离边界不能太近，差不多就好转弯了
SIGHT_VIEW = 50  # 视野范围
SIGHT_VIEW_squared = SIGHT_VIEW * SIGHT_VIEW  # 视野范围的平方，为了计算距离时减少开根号，增加效率
MIN_DISTANCE = 11  # 小鸟不能靠得太近
BLOCK_NUM = 5
BLOCK_SIZE = 50  # 障碍物的大小，最大值
BLOCK_VIEW = 5  # 避障视野，再往前走几步会撞到障碍物
# 颜色
BACK_GROUND_COLOR = (245, 245, 255)  # 浅灰偏蓝
BIRD_PATH_COLOR = (200, 200, 200)  # 淡灰色
EAGLE_PATH_COLOR = (20, 20, 20)  # 黑色
EAGLE_COLOR = (255, 0, 0)  # 红色
BIRD_COLOR = (0, 255, 0)  # 绿色
BLOCK_COLOR = (0, 0, 255)  # 浅蓝色
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
    eagle_image = None


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
    distance_of_closest_neighbor = 10000
    min_distance = 1000000

    for ob in objects:
        if ob != myself:
            distance_squared = myself.pos.distance_squared_to(ob.pos)
            if distance_squared < SIGHT_VIEW_squared:
                neighbors.append(ob)
                # 更新最近的邻居
                if distance_squared < min_distance:
                    min_distance = distance_squared
                    closest_neighbor = ob
                    distance_of_closest_neighbor = distance_squared
    return neighbors, closest_neighbor, math.sqrt(distance_of_closest_neighbor)


def goto_neighbor(myself, neighbor, dir = True):
    """
    走向或者远离周边的物体
    参数:
    dir : True=走向，False=远离
    返回:
    angle：走向或者远离物体的方向
    """
    if dir: nei_to_my = neighbor.pos - myself.pos
    else: nei_to_my = myself.pos - neighbor.pos
    angle2 = round(Vector2(1, 0).angle_to(nei_to_my))
    if angle2 < 0: angle2 += 360
    return angle2


def avoid_blocks(myself, blocks):
    '''
    避开障碍物
    参数：
    myself=小鸟类的实例，blocks=障碍物的列表
    返回：
    None=如果不会碰到障碍物，否则=转弯后的角度
    '''
    min_step = 1000000
    min_block = None
    # 测试再往前走几步，是否会碰到障碍物。 要找到会碰撞的最小步数和要撞上的那个障碍物
    for test_step in range(BLOCK_VIEW, 1, -1):
        test_pos = myself.pos + myself.speed * myself.dir * test_step
        for block in blocks:
            if test_pos.distance_to(block.pos) < block.size + myself.size + 2:
                # 会碰到障碍物，看看是不是最近的一个
                if test_step < min_step:
                    min_step = test_step
                    min_block = block
    if min_block:
        v_self_to_block = (min_block.pos - myself.pos).normalize()
        ang_to_block = round(Vector2(1, 0).angle_to(v_self_to_block))
        if ang_to_block < 0: ang_to_block += 360
        # 这里要判断是否跨越x轴正向，即271度到89度，做特殊处理，其他正常
        if myself.angle >= ang_to_block:
            if myself.angle > 271 and ang_to_block < 89: turn_fact = -1
            else: turn_fact = 1
        else:
            if ang_to_block > 271 and myself.angle < 89: turn_fact = 1
            else: turn_fact = -1
        # print(f'{min_step} steps, now angle={self.angle}', end='')
        return myself.angle + turn_fact * ((BLOCK_VIEW - min_step) * 20 + 10)
    else: return None

    
# 通用的移动物体的类
class Object:
    def __init__(self, x, y):
        self.pos = Vector2(x, y)
        self.angle = random.randint(0, 359)  # 随机角度
        self.dir = Vector2(1, 0)
        self.speed = 5
        self.size = 5
        self.path = []

    def proc_move(self):
        # 角度归一化
        if self.angle >= 360: self.angle -= 360
        elif self.angle < 0: self.angle += 360
        # 更新路径记录
        self.path.append(self.pos.copy())
        # 限制路径长度，避免消耗过多内存
        if len(self.path) > PATH_LEN:
            self.path.pop(0)

        # 根据角度和速度更新位置
        self.dir = Vector2(1, 0).rotate(self.angle).normalize()
        self.pos += self.speed * self.dir

        # 边界检测
        if GO_THROUGH:
            # 穿墙模式
            if self.pos.x < 0:
                self.pos.x = screen_width - 1
                self.path.clear()
            elif self.pos.x >= screen_width:
                self.pos.x = 0
                self.path.clear()
            if self.pos.y < 0:
                self.pos.y = screen_height - 1
                self.path.clear()
            elif self.pos.y >= screen_height:
                self.pos.y = 0
                self.path.clear()
        else:
            # 反弹回去
            if self.pos.x < MARGIN or self.pos.x > screen_width - MARGIN:
                self.angle = (180 - self.angle) % 360
                self.pos.x = max(MARGIN, min(screen_width - MARGIN, round(self.pos.x)))
            if self.pos.y < MARGIN or self.pos.y > screen_height - MARGIN:
                self.angle = (360 - self.angle) % 360
                self.pos.y = max(MARGIN, min(screen_height - MARGIN, round(self.pos.y)))


# 小鸟的类
class Bird(Object):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = BIRD_SIZE
        self.speed = BIRD_SPEED

    def move(self, birds, eagles, blocks):
        ''' 小鸟的飞行规则，优先级从高到低
        0. 避障
        1. 躲避老鹰
        2. 避免太挤
        3. 方向趋同
        4. 小概率随机转弯
        最后是边界处理 '''
        ang_changed = False
        new_angle = avoid_blocks(self, blocks)
        if new_angle != None:
            self.angle = new_angle
            ang_changed = True
            # print(f', turn to {self.angle}')
        if not ang_changed and USE_EAGLE:
            # 找出视力范围内，离自身最近的老鹰
            _, closest_eagle, _ = find_closest_neighbor(self, eagles)
            if closest_eagle:
                # 远离最近的老鹰
                self.angle = goto_neighbor(self, closest_eagle, False)
                ang_changed = True
        if not ang_changed and (not USE_EAGLE or not closest_eagle):
            # 找出距离小于SIGHT_VIEW的邻居，离自身最近的邻居以及这个邻居的距离
            neighbors, closest_neighbor, distance_of_closest_neighbor = find_closest_neighbor(self, birds)
            if len(neighbors) > 0:
                if distance_of_closest_neighbor < MIN_DISTANCE:
                    # 远离最近的邻居
                    self.angle = goto_neighbor(self, closest_neighbor, False)
                    ang_changed = True
                else:
                    # 方向趋同
                    self.angle = average_angle([ob.angle for ob in neighbors])
                    ang_changed = True
        # 大概率朝原来的方向，小概率随机转弯
        if not ang_changed and random.randint(1, 200) <= TURN_RATE:
            # 随机转弯
            self.angle += (random.choice((1, -1)) * random.randint(10, 45)) % 360
            ang_changed = True
        self.proc_move()

    def draw(self, screen):
        pygame.draw.circle(screen, BIRD_COLOR, (int(self.pos.x), int(self.pos.y)), self.size)
        # 画出路径
        if SHOW_PATH and len(self.path) > 1:
            path_points = [(int(x), int(y)) for x, y in self.path]
            pygame.draw.lines(screen, BIRD_PATH_COLOR, False, path_points, 1)

    def draw_img(self, screen):
        if bird_image:
            screen.blit(bird_image, (int(self.pos.x), int(self.pos.y)))
        else:
            self.draw(screen)


# 老鹰的类
class Eagle(Object):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = EAGLE_SIZE
        self.speed = EAGLE_SPEED

    def move(self, birds):
        ang_changed = False
        # 找出视力范围内，离自身最近的小鸟
        _, closest_neighbor, _ = find_closest_neighbor(self, birds)
        if closest_neighbor:
            # 追逐最近的小鸟
            self.angle = goto_neighbor(self, closest_neighbor, True)
            ang_changed = True
        # 大概率朝原来的方向，小概率随机转弯
        if not ang_changed and random.randint(1, 200) <= TURN_RATE:
            # 随机转弯
            self.angle += (random.choice((1, -1)) * random.randint(10, 45)) % 360
            ang_changed = True
        self.proc_move()

    def draw(self, screen):
        pygame.draw.circle(screen, EAGLE_COLOR, (int(self.pos.x), int(self.pos.y)), self.size)
        # 画出路径
        if SHOW_PATH and len(self.path) > 1:
            path_points = [(int(x), int(y)) for x, y in self.path]
            pygame.draw.lines(screen, EAGLE_PATH_COLOR, False, path_points, 1)

    def draw_img(self, screen):
        if eagle_image:
            screen.blit(eagle_image, (int(self.pos.x), int(self.pos.y)))
        else:
            self.draw(screen)


# 障碍物的类
class Block:
    def __init__(self, x, y):
        self.pos = Vector2(x, y)
        self.size = random.randint(BLOCK_SIZE-30, BLOCK_SIZE)

    def draw(self, screen):
        pygame.draw.circle(screen, BLOCK_COLOR, (int(self.pos.x), int(self.pos.y)), self.size)
        
        
def birds_tongyi_app():
    # 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    # 创建时钟对象
    clock = pygame.time.Clock()
    # 设置标题
    caption_str = "Birds Tongyi"
    pygame.display.set_caption(caption_str)
    # 创建小鸟列表
    birds = [Bird(random.randint(MARGIN, screen_width-MARGIN), random.randint(MARGIN, screen_height-MARGIN))
             for _ in range(BIRD_NUM)]
    # 创建老鹰列表
    eagles = [Eagle(random.randint(MARGIN, screen_width-MARGIN), random.randint(MARGIN, screen_height-MARGIN))
              for _ in range(EAGLE_NUM)]
    # 创建障碍物列表
    blocks = [Block(random.randint(BLOCK_SIZE+BIRD_SIZE, screen_width - BLOCK_SIZE-BIRD_SIZE),
                    random.randint(BLOCK_SIZE+BIRD_SIZE, screen_height - BLOCK_SIZE -BIRD_SIZE))
              for _ in range(BLOCK_NUM)]
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
            bird.move(birds,eagles,blocks)
            bird.draw_img(screen)
        if USE_EAGLE:
            # 更新并绘制老鹰
            for eagle in eagles:
                eagle.move(birds)
                eagle.draw_img(screen)
        # 重新绘制障碍物
        for block in blocks:
            block.draw(screen)
        pygame.display.set_caption(f'{caption_str} - {str(int(clock.get_fps()))}fps')
        # 更新屏幕
        pygame.display.flip()
        # 控制帧率
        clock.tick(FPS)  # 设置每秒10帧
    # 退出Pygame
    pygame.quit()


if __name__ == '__main__':
    birds_tongyi_app()
