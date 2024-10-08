import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数 
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

class Bird:
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)

class Beam:
    def __init__(self, bird: "Bird"):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)

class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

def game_over(screen: pg.Surface, score: int):
    """ゲームオーバー時の画面表示を行う"""
    font = pg.font.Font(None, 100)
    game_over_text = font.render("GAME OVER", True, (255, 0, 0))
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(game_over_text, (WIDTH//4, HEIGHT//3))
    screen.blit(score_text, (WIDTH//3, HEIGHT//2))
    pg.display.update()
    time.sleep(3)  # 3秒間停止

class Score:
    """
    スコアを表示するためのクラス
    """
    def __init__(self):
        """
        スコアを初期化する
        """
        self.fonto = pg.font.SysFont("hgp創英角ポップ体", 50)  # フォントの設定
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # スコアの初期値
        self.img = self.fonto.render(f"socre: {self.score}", 0, self.color)  # スコア表示用Surface
        self.rct = self.img.get_rect()
        self.rct.topleft = (100, HEIGHT - 50)  # 画面左下から50px上

    def update(self, screen: pg.Surface):
        """
        スコアを更新して画面に表示する
        """
        self.img = self.fonto.render(f"score: {self.score}", 0, self.color)  # スコアを描画するSurfaceを更新
        screen.blit(self.img, self.rct)  # スコアを画面に描画

class Explosion:
    def __init__(self, center: tuple[int, int], life: int = 10):
        # 爆発画像の読み込みと上下左右反転
        original_img = pg.image.load("fig/explosion.gif")
        flipped_img1 = pg.transform.flip(original_img, True, False)
        flipped_img2 = pg.transform.flip(original_img, False, True)

        # 画像をリストに格納
        self.images = [original_img, flipped_img1, flipped_img2]
        self.image_index = 0  # どの画像を表示するか
        self.life = life  # 爆発時間
        self.image = self.images[self.image_index]
        self.rct = self.image.get_rect(center=center)

    def update(self, screen: pg.Surface):
        # lifeが正なら減少させて画像を切り替える
        if self.life > 0:
            self.life -= 1
            # 画像を順番に切り替えて点滅効果を演出
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = self.images[self.image_index]
            screen.blit(self.image, self.rct)  # 爆発画像を描画

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beam = None
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []  # ビームを管理するリスト
    explosions = []  # 爆発エフェクトを管理するリスト
    clock = pg.time.Clock()
    tmr = 0
    score = Score()  # スコアのインスタンスを生成

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))  # スペースキー押下でビームを追加

        screen.blit(bg_img, [0, 0])

        # こうかとんが爆弾に当たったかチェック
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                game_over(screen, score)  # ゲームオーバー画面を表示
                return

        # ビームが爆弾に当たったかチェック
        for beam in beams:
            for j, bomb in enumerate(bombs):
                if bomb and beam.rct.colliderect(bomb.rct):  # Noneでないことを確認
                    # 爆弾の位置で爆発エフェクトを発生
                    explosions.append(Explosion(bomb.rct.center))
                    bombs[j] = None  # 爆弾とビームの衝突で爆弾を消す
                    beams.remove(beam)  # ビームも消す
                    bird.change_img(6, screen)
                    pg.display.update()
                    score.score += 1  # スコアを1点増やす

        # 消えた爆弾と画面外のビームを除去
        bombs = [bomb for bomb in bombs if bomb is not None]
        beams = [beam for beam in beams if check_bound(beam.rct)[0]]

        # 鳥、ビーム、爆弾、スコアの更新
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:
            beam.update(screen)
        for bomb in bombs:
            bomb.update(screen)

        # 爆発エフェクトの更新
        for explosion in explosions:
            explosion.update(screen)
        # 爆発が終わったものを削除
        explosions = [exp for exp in explosions if exp.life > 0]

        # スコアの更新と表示
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
