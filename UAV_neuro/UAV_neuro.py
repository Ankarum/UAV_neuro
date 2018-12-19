
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

MAP_X_MIN = -1000 # Левая граница карты
MAP_X_MAX = 1000  # Правая граница карты
MAP_Y_MIN = -1000 # Нижняя граница карты
MAP_Y_MAX = 1000  # Верхняя граница карты
DELTA_TIME = 1    # Время между шагами

# Функция для вычисления расстояния между объектами
distance = lambda obj1, obj2: ((obj2.x - obj1.x)**2 + (obj2.y - obj1.y)**2)**0.5

# Функция для нахождения угла, показывающего направление от одного объекта до другого
directionAngle = lambda obj1, obj2: math.atan2(obj2.y - obj1.y, obj2.x - obj1.x)

# Вышка, которую должны охранять БЛА
# и у которой есть некоторый радиус обнаружения целей
class Tower:
    def __init__(self, x, y, detection_radius):
        self.x = x
        self.y = y
        self.detection_radius = detection_radius

    # Функция возвращает все обнаруженные цели, отсортированные по расстоянию до вышки
    def detect_targets(self, targets):
        # Цели в радиусе обнаружения, которые пока не перехватываются
        detected_targets = [target for target in targets if (distance(self, target) <= self.detection_radius)
                            and (target.intercepting == False)
                            and (target.destroyed == False)]
        sorted_by_distance = sorted(detected_targets, key = lambda t: distance(self, t))
        return sorted_by_distance

# Цели летят из начальной точки в конечную
class Target:
    def __init__(self, X_start, Y_start, destination, V):
        self.x = X_start
        self.y = Y_start
        self.direction_angle = directionAngle(self, destination) # Нахождение направления движения данной цели
        self.V = V
        self.intercepting = False # Цель перехватывается
        self.destroyed = False # Цель не уничтожена

    # Сделать "шаг" в направлении движения цели
    def move(self):
        step_distance = self.V * DELTA_TIME
        self.x = self.x + step_distance * math.cos(self.direction_angle)
        self.y = self.y + step_distance * math.sin(self.direction_angle)

    # Уничтоженный объект не отрисовывается и не двигается
    def destroy(self):
        self.destroyed = True

# Точка на карте
class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Беспилотник
class UAV:
    def __init__(self, X, Y, V, small_radius):
        self.idle_point = Point(X, Y) # Начальная точка, вокруг которой летает БЛА в режиме простоя
        self.x = X + small_radius # БЛА появляется справа от начальной точки (по карте)
        self.y = Y
        self.V = V
        self.direction_angle = math.pi/2
        self.small_radius = small_radius # Радиус, по которому летает БЛА во время ожидания
        self.target = None # Перехватываемый объект
        self.destroyed = False # БЛА не уничтожен

    # Задать перехватываемый объект
    def set_target(self, target):
        self.target = target
        target.intercepting = True # Обновить статус цели

    # Уничтоженный объект не отрисовывается и не двигается
    def destroy(self):
        self.destroyed = True
    
    # Сделать шаг (в направлении цели, если она есть или по кругу)
    # Предполагается, что после обнаружения цели БЛА уже не переходит в режим простоя (не летает по кругу)
    def move(self):
        # Если есть цель - лететь в её направлении
        if self.target != None:
            step_distance = self.V * DELTA_TIME
            self.direction_angle = directionAngle(self, self.target)
            self.x = self.x + step_distance * math.cos(self.direction_angle)
            self.y = self.y + step_distance * math.sin(self.direction_angle)

            # При "встрече" с целью, уничтожить ее (и себя)
            if distance(self, self.target) <= 40:
                self.target.destroy()
                self.destroy()
        else: # Движение по кругу в режиме покоя
            step_distance = self.V * DELTA_TIME
            self.direction_angle = directionAngle(self, self.idle_point) - math.pi/2 # БЛА летает против часовой стрелки
            self.x = self.x + step_distance * math.cos(self.direction_angle)
            self.y = self.y + step_distance * math.sin(self.direction_angle)

# Создание вышки
tower = Tower(0, 0, 600)

# Создание целей с заданными координатами, которые летят по направлению к вышке
targets = [Target(x, y, tower, 10) for (x,y) in [
    [-600, -600],
    [-800, 0],
    [-700, 600],
    [-200, 900]]]

# Создание беспилотников с "точками простоя", расположенными в точках рядом с вышкой
UAVs = [UAV(x, y, 20, 100) for (x, y) in [
    [tower.x - 200, tower.y - 200],
    [tower.x + 200, tower.y - 200],
    [tower.x - 200, tower.y + 200],
    [tower.x + 200, tower.y + 200]]]

fig = plt.figure()

# Совершить "шаги" БЛА и целей и отрисовать их на графике
def update(i):
    plt.clf()
    axes = plt.gca()
    axes.set_xlim([MAP_X_MIN, MAP_X_MAX])
    axes.set_ylim([MAP_Y_MIN, MAP_Y_MAX])
    
    # "Передвинуть" все цели и отрисовать их на карте
    for target in [target for target in targets if target.destroyed==False]:
        target.move()
        plt.plot(target.x, target.y, marker=(3, 0, math.degrees(target.direction_angle)-90), markersize=20, color="red")

    # "Обнаружить" ближайшую цель, попавшую в радиус обнаружения
    detected_targets = tower.detect_targets(targets)
    # Если цель обнаружена, отправить на перехват ближайший БЛА
    if len(detected_targets) > 0:
        nearest_target = detected_targets[0]
        # Определить ближайший незанятый БЛА
        nearest_UAV = sorted([uav for uav in UAVs if uav.target == None], key=lambda uav: distance(uav, nearest_target))[0]
        nearest_UAV.set_target(nearest_target)

    # "Передвинуть" беспилотники и отрисовать их на карте
    for uav in [uav for uav in UAVs if uav.destroyed==False]:
        uav.move()
        plt.plot(uav.x, uav.y, marker=(3, 0, math.degrees(uav.direction_angle)-90), markersize=20, color="blue")

    plt.plot(tower.x, tower.y, marker="*", markersize=30, color="green") # Отрисовать башню на карте
    detection_radius = plt.Circle((tower.x, tower.y), tower.detection_radius, color="g", fill=False) # "Создать" радиус обнаружения на карте
    axes.add_artist(detection_radius) # Отрисовать радиус на карте
    
anim = animation.FuncAnimation(fig, update, interval=100)
plt.show()
