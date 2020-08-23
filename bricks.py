import copy
import numpy as np
import pygame
from pygame.locals import *

# pygame 초기화
pygame.init()

CLOCK = pygame.time.Clock()  # 시계
FPS = 60  # FPS
THROW_TERM = FPS // 20  # 발사하는 시간 차
BALL_SPEED = 600 // FPS  # 공 SPEED

# 팔레트
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BALL_COLOR = (51, 102, 255)
GRAY = (155, 155, 155)

# 폰트
FONT24 = pygame.font.SysFont(None, 24)
FONT32 = pygame.font.SysFont(None, 32)
FONT48 = pygame.font.SysFont(None, 48)

# 게임 오브젝트 사이즈
BRICK_WIDTH = 85  # 벽돌 너비
BRICK_HEIGHT = 40  # 벽돌 높이
BRICK_GAP = 5  # 벽돌 사이의 공간
BALL_RADIUS = 10  # 공 사이즈

# 법선벡터
ORIGIN = np.array([0, 0])
VERTICAL = np.array([1, 0])
HORIZONTAL = np.array([0, -1])

# 사이즈
WIDTH = 7 * BRICK_GAP + 6 * BRICK_WIDTH
HEIGHT = 105 * 2 + 9 * BRICK_GAP + 8 * BRICK_HEIGHT

# 윈도우
window = pygame.display.set_mode((WIDTH, HEIGHT))
window_rect = window.get_rect()
pygame.display.set_caption("Bricks")


# 정사영
def project(a, b):
    return b * (sum(a * b))


# 단위벡터
def unit(a):
    return a / np.linalg.norm(a)


# 각도
def polar(a):
    return (np.arctan2(-a[1], a[0]) + 2 * np.pi) % (2 * np.pi)


# Scene : 최상위 클래스
class Scene:
    def draw(self):
        pass

    def event(self, event):
        pass


# Start
class Start(Scene):
    def draw(self):
        global window

        title = FONT48.render("START", True, BLACK)
        title_rect = title.get_rect()
        title_rect.center = window.get_rect().center

        window.blit(title, title_rect)

    def event(self, event):
        global scene

        if event.type == MOUSEBUTTONDOWN:
            scene = Game()


# Game
class Game(Scene):
    class Sprite:
        def update(self, *args):
            pass

        def collide_area(self):
            pass

        def draw(self):
            pass

    class Ball(Sprite):
        def __init__(self):
            self.position = np.array((WIDTH / 2, HEIGHT - 100 - BALL_RADIUS))  # 공의 위치벡터
            self.vector = ORIGIN  # 속도 단위 벡터
            self.move = False

        def update(self, bricks):
            if not self.move:
                return

            self.position += self.vector * BALL_SPEED

            collide = False  # 충돌?
            n = ORIGIN  # 법선벡터

            # 원(공)-직사각형(벽돌) 충돌
            for i in range(len(bricks)):
                if bricks[i].collide_area.collidepoint(*self.position):  # 부딪혔다면
                    collide = True

                    # 이분탐색(공 위치 보정)
                    low = 0
                    high = BALL_SPEED
                    self.position -= self.vector * BALL_SPEED
                    for _ in range(10):
                        mid = (low + high) / 2
                        if bricks[i].collide_area.collidepoint(*(self.position + self.vector * mid)):
                            high = mid
                        else:
                            low = mid
                    self.position += self.vector * high

                    # 법선벡터 설정
                    if abs(self.position[0] + BALL_RADIUS - bricks[i].rect.left) < 1 or \
                            abs(self.position[0] - BALL_RADIUS - bricks[i].rect.right) < 1:
                        n = HORIZONTAL
                    else:
                        n = VERTICAL

                    # 벽돌이 0개라면 벽돌 삭제
                    bricks[i].count -= 1
                    if bricks[i].count == 0:
                        bricks.pop(i)

                    break

            # 게임 공간 경계에서의 충돌 체크
            if self.position[0] - BALL_RADIUS <= 7 or self.position[0] + BALL_RADIUS >= WIDTH - 7:  # 양 사이드에 부딪혔을 때
                collide = True
                if self.position[0] - BALL_RADIUS <= 7:  # 왼쪽에 부딪혔을 때
                    self.position[0] = 8 + BALL_RADIUS
                if self.position[0] + BALL_RADIUS >= WIDTH - 7:  # 오른쪽에 부딪혔을때
                    self.position[0] = WIDTH - 8 - BALL_RADIUS
                n = HORIZONTAL
            if self.position[1] - BALL_RADIUS <= 100:  # 천장에 부딪혔을때
                collide = True
                self.position[1] = 101 + BALL_RADIUS
                n = VERTICAL
            if self.position[1] + BALL_RADIUS >= window_rect.bottom - 100:  # 땅에 왔을 때 움직임을 멈춘다
                self.move = False
                self.vector = ORIGIN
                self.position[1] = window_rect.bottom - 100 - BALL_RADIUS

            if collide:
                self.vector = unit(project(self.vector, n) * 2 - self.vector)

        def draw(self):
            pygame.draw.circle(window, BALL_COLOR, (int(self.position[0]), int(self.position[1])), BALL_RADIUS)

    class Brick(Sprite):
        def __init__(self, row, column, count):
            self.row = row  # 행
            self.column = column  # 열

            self.count0 = count  # 초기 벽돌 갯수
            self.count = count  # 벽돌 갯수

            self.rect = pygame.Rect(0, 0, BRICK_WIDTH, BRICK_HEIGHT)
            self.collide_area = pygame.Rect(0, 0, BRICK_WIDTH + BALL_RADIUS * 2, BRICK_HEIGHT + BALL_RADIUS * 2)

        def update(self):
            self.rect.left = BRICK_GAP * (self.column + 1) + BRICK_WIDTH * self.column
            self.rect.top = 100 + BRICK_GAP + BRICK_GAP * (self.row + 1) + BRICK_HEIGHT * self.row

            self.collide_area.center = self.rect.center

        def draw(self):
            # pygame.draw.rect(window, (0, 255, 0), self.collide_area())  # 충돌 범위 indicator

            ratio = self.count / self.count0
            pygame.draw.rect(window, (255, 153 * (1 - ratio), 153 * (1 - ratio)), self.rect)

            count_label = FONT24.render("{0}".format(self.count), True, BLACK)
            count_rect = count_label.get_rect()
            count_rect.center = self.rect.center
            window.blit(count_label, count_rect)

    class GreenBall(Sprite):
        def __init__(self, row, column):
            self.row = row
            self.column = column
            self.rect = pygame.Rect(0, 0, BALL_RADIUS * 4, BALL_RADIUS * 4)

        def draw(self):
            self.rect.centerx = BRICK_GAP * (self.column + 1) + BRICK_WIDTH * self.column + BRICK_WIDTH / 2
            self.rect.centery = 100 + BRICK_GAP + BRICK_GAP * (self.row + 1) + BRICK_HEIGHT * self.row + BRICK_HEIGHT / 2
            pygame.draw.circle(window, (51, 255, 51), self.rect.center, BALL_RADIUS)

    def generate(self):
        next_line = {-1: set(), 1: -1}
        i = np.random.randint(6)
        next_line[1] = i
        for _ in range(5):
            j = np.random.randint(6)
            if i == j:
                pass
            else:
                next_line[-1].add(j)
        for i in next_line[-1]:
            self.bricks.append(self.Brick(0, i, self.score + 1))
        self.green_balls.append(self.GreenBall(0, next_line[1]))

    def __init__(self):
        self.score = 0
        self.add_ball = 0

        self.balls = [self.Ball()]
        self.bricks = []
        self.green_balls = []

        self.generate()  # 벽돌, 초록 공 생성

        self.throwing = False  # 공이 움직이고 있는가?
        self.throwing_vector = ORIGIN  # 공을 던지는 방향을 저장하는 벡터
        self.timer = 0  # 던지고 있을 때 작동하는 타이머

    def draw(self):
        global scene

        # 던질 때
        if self.throwing and self.timer <= (len(self.balls) - 1) * THROW_TERM + 1:
            self.timer += 1
            if self.timer % THROW_TERM == 1:
                self.balls[self.timer // THROW_TERM].move = True
                self.balls[self.timer // THROW_TERM].vector = self.throwing_vector

        # 공이 초록공에 부딪혔을 때
        for ball in self.balls:
            for green_ball in self.green_balls:
                if green_ball.rect.collidepoint(*ball.position):
                    self.add_ball += 1
                    self.green_balls.remove(green_ball)
                    break

        # 다 던졌을 때
        ok = True
        for ball in self.balls:
            if ball.move:
                ok = False
        if ok and self.throwing:
            self.throwing = False
            self.timer = 0
            self.throwing_vector = ORIGIN

            # 벽돌을 내린다
            for brick in self.bricks:
                brick.row += 1
                if brick.row == 7:
                    scene = End(self.score)
                    return

            # 초록공도 내린다
            remove = []
            for green_ball in self.green_balls:
                green_ball.row += 1
                if green_ball.row == 7:
                    self.add_ball += 1
                    remove.append(green_ball)
            for r in remove:
                self.green_balls.remove(r)

            self.score += 1
            for _ in range(self.add_ball):
                self.balls.append(self.Ball())
            self.add_ball = 0

            for ball in self.balls:
                ball.position = copy.copy(self.balls[0].position)

            # 다음 라인 생성
            self.generate()

        # 천장 그리기
        pygame.draw.line(window, GRAY, (0, 100), (WIDTH, 100), 5)
        # 바닥 그리기
        pygame.draw.line(window, GRAY, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 5)

        # 공 그리기
        for ball in self.balls:
            ball.update(self.bricks)
            ball.draw()

        # 벽돌 그리기
        for brick in self.bricks:
            brick.update()
            brick.draw()

        # 초록 공 그리기
        for green_ball in self.green_balls:
            green_ball.draw()

        # 스코어
        score_label = FONT32.render("Score : {0}, FPS : {1}".format(self.score, str(int(CLOCK.get_fps()))), True, BLACK)
        score_rect = score_label.get_rect()
        score_rect.top = window_rect.top
        score_rect.left = window_rect.left
        window.blit(score_label, score_rect)

    def event(self, event):
        if event.type == MOUSEBUTTONDOWN and not self.throwing:
            d = np.array(pygame.mouse.get_pos()) - self.balls[0].position
            if 10 * np.pi / 180 <= polar(d) <= 170 * np.pi / 180:  # 각도 제한 10도 ~ 170도
                self.throwing = True
                self.throwing_vector = unit(d)
                self.timer = 0


# End
class End(Scene):
    def __init__(self, score):
        self.score = score

    def draw(self):
        label = FONT48.render("Your score is {0}.".format(self.score), True, BLACK)
        label_rect = label.get_rect()
        label_rect.center = window_rect.center
        window.blit(label, label_rect)

    def event(self, event):
        global scene

        if event.type == MOUSEBUTTONDOWN:
            scene = Game()
            return


scene = Start()
while True:
    # 이벤트 핸들링
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

        scene.event(event)

    # 업데이트
    window.fill(WHITE)

    scene.draw()

    pygame.display.update()
    CLOCK.tick(FPS)
