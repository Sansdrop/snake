import msvcrt
import ctypes
import os
import random
import threading
import time
import queue

''' 初始化场景实体 '''

os.system('cls')
MAXSIZE = 36
scene_ = []
scene_x = scene_y = 0
while scene_x < MAXSIZE:
    scene_.append([])
    scene_y = 0
    while scene_y < MAXSIZE:
        scene_[scene_x].append(0)
        scene_y += 1
    scene_x += 1


def change_scene_add(loc: list, entity_type: int):
    # 在各实体等出现变动时,场景实体需要进行同步变化,list:[(,),(,), ...]
    for loc_node in loc:
        scene_[loc_node[0]][loc_node[1]] = entity_type


def change_scene_del(loc: list):
    # 消失的实体,对应场景实体类型重置为0,list:[(,),(,), ...]
    for loc_node in loc:
        scene_[loc_node[0]][loc_node[1]] = 0


def is_loc_legitimacy(loc):  # 目标位置的场景是否尚未存在物体
    if(scene_[loc[0]][loc[1]] == 0):
        return True
    return False


''' 控制台指定位置打印字符str，来自CSDN博主：@BluePROT '''


class COORD(ctypes.Structure):
    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]

    def __init__(self, x, y):
        self.X = x
        self.Y = y


def reset_current_loc():  # 重置光标于场景底部
    STD_OUTPUT_HANDLE = -11
    hOut = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    INIT_POS = COORD(MAXSIZE*2, MAXSIZE)  # 这里参数是x*2，因为实心方块是两个占位符
    ctypes.windll.kernel32.SetConsoleCursorPosition(hOut, INIT_POS)


def print_at_loc(x, y, str):  # 和上一个函数差不多，区别在于位置指定
    STD_OUTPUT_HANDLE = -11
    hOut = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    INIT_POS = COORD(x*2, y)  # 这里参数是x*2，因为实心方块是两个占位符
    ctypes.windll.kernel32.SetConsoleCursorPosition(hOut, INIT_POS)
    print(str)


''' 主体类 '''


class Entity:
    loc = []
    body_model = '■'

    def __init__(self, str):
        self.body_model = str


class Map(Entity):     # ■★●□
    entity_type = 1

    def print_map(self):
        for node in self.loc:
            print_at_loc(node[0], node[1], self.body_model)


class Snake(Entity):
    entity_type = 2
    head_model = '□'
    head_loc = [0, 0]
    move_direction = [0, 0]
    body_lenth = 4

    def print_snake(self):
        for node in self.loc:
            print_at_loc(node[0], node[1], self.body_model)
        print_at_loc(self.loc[0][0], self.loc[0][1], self.head_model)

    def __init__(self):  # 不能超出地图边界或出现在墙体(场景实体)上
        # 得到一个随机的移动方向的坐标（相对蛇头）
        self.loc.clear()
        self.move_direction[random.randint(
            0, 1)] = (-1) ** random.randint(1, 2)
        self.body_lenth = random.randint(3, 5)
        while True:
            # 蛇头取随机值，并保证蛇身不会超出边界
            x = random.randint(1+self.body_lenth, MAXSIZE-2-self.body_lenth)
            y = random.randint(1+self.body_lenth, MAXSIZE-2-self.body_lenth)
            head_x = x
            head_y = y  # XXX目前不清楚这里的变量取的是索引还是实际值
            i = 0
            while i < self.body_lenth:
                if is_loc_legitimacy((x, y)) == True:  # 蛇体合法
                    self.loc.append((x, y))
                    x -= self.move_direction[0]
                    y -= self.move_direction[1]
                    i += 1
                else:
                    self.loc.clear()
                    continue
            if i == self.body_lenth:  # 整条蛇都合法
                self.head_loc = [head_x, head_y]
                break
        change_scene_add(self.loc, self.entity_type)
        self.print_snake()

    def move_once_as_reprint(self, is_growing):
        self.head_loc[0] += self.move_direction[0]
        self.head_loc[1] += self.move_direction[1]
        self.loc.insert(0, (self.head_loc[0], self.head_loc[1]))
        if is_growing == False:  # 如果是进食生长状态则尾部不消失作为新长出的部分
            end = self.loc.pop()
            print_at_loc(end[0], end[1], '  ')
            change_scene_del([end])
        else:  # 生长状态下需要增加蛇体长度
            self.body_lenth += 1
        print_at_loc(self.head_loc[0], self.head_loc[1], self.head_model)
        print_at_loc(self.loc[1][0], self.loc[1][1], self.body_model)
        """
        change_scene_add([self.head_loc], self.entity_type) 
        此处的重置scene决定现在后续进程函数种执行，以便判断蛇头的状态
        """

    def change_direction(self, str):
        if str is b'8' and self.move_direction[1] == 0:
            self.move_direction[1] = -1
            self.move_direction[0] = 0
        elif str is b'4' and self.move_direction[0] == 0:
            self.move_direction[0] = -1
            self.move_direction[1] = 0
        elif str is b'6' and self.move_direction[0] == 0:
            self.move_direction[0] = 1
            self.move_direction[1] = 0
        elif str is b'2' and self.move_direction[1] == 0:
            self.move_direction[1] = 1
            self.move_direction[0] = 0


class Food():
    loc = []
    body_model = '■'
    entity_type = 3

    def __init__(self, str):
        self.body_model = str

    def print_food(self):
        print_at_loc(self.loc[0][0], self.loc[0][1], self.body_model)

    def new_food_reprint(self, str1, str2):
        food_type_judge = random.randint(0, 5)
        if food_type_judge == 0:
            self.body_model = str2
            self.entity_type = 6
        else:
            self.body_model = str1
            self.entity_type = 3
        if self.loc.__len__() != 0:
            change_scene_del(self.loc)
            self.loc.clear()
        while True:
            # food位置取随机值，并保证位置合法
            x = random.randint(0, MAXSIZE-1)
            y = random.randint(0, MAXSIZE-1)
            if is_loc_legitimacy((x, y)) == True:  # food位置合法
                self.loc.append([x, y])
                break
            else:
                self.loc.clear()
                continue
        change_scene_add(self.loc, self.entity_type)
        self.print_food()


map = Map('■')
i = 0
while i < MAXSIZE:
    map.loc += [(0, i), (MAXSIZE-1, i), (i, 0), (i, MAXSIZE-1)]
    i += 1
change_scene_add(map.loc, map.entity_type)
map.print_map()
snake = Snake()
food = Food('●')
food.new_food_reprint('●', '★')
reset_current_loc()


'''测试多线程'''

q = queue.Queue()


def key_getch():
    while True:
        a = msvcrt.getch()
        q.put(a)


def snaker_main():
    end_wait_times = 0
    while True:
        is_growing = False
        if q.empty() == False:  # 改变方向
            i = q.get()
            snake.change_direction(i)
        time.sleep(0.30)
        if end_wait_times != 0:
            is_growing = True
            end_wait_times -= 1
        snake.move_once_as_reprint(is_growing)
        # 记录蛇头位置的场景实体以判断food是否被吃掉
        is_food_ate = scene_[snake.head_loc[0]][snake.head_loc[1]]
        if is_food_ate > 2:  # 蛇头位置吃到food
            score = food.entity_type - 2  # 根据score判断end要滞留几次
            end_wait_times += score  # 滞留次数
            food.new_food_reprint('●', '★')
        is_snake_dead_ateSelf = is_food_ate
        if is_snake_dead_ateSelf == 2:
            reset_current_loc()
            print('\n\tY O U    D E A D')
            break
        is_snake_hitWall = is_food_ate
        if is_snake_hitWall == 1:
            reset_current_loc()
            print('\n\tY O U    D E A D')
            break
        change_scene_add([snake.head_loc], snake.entity_type)


program1 = threading.Thread(target=key_getch)
program2 = threading.Thread(target=snaker_main)
program2.start()
program1.start()
