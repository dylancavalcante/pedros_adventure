import pygame
import pytmx
import random
import os
import sys

# --- FUNÇÃO DE CAMINHO PARA EXECUTÁVEL ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURAÇÕES ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GAME_TITLE = "Pedro's adventure"
GAME_ICON_PATH = resource_path("cat-Sheet.png") 
ZOOM_ATUAL = 5.0
ZOOM_ALVO = 5.0
FPS = 60

TEXTO_INTRO = (
    "Pedro,|"
    "Queria te pedir desculpas por não ter estado presente no dia do seu aniversário. "
    "Fiquei realmente chateado por não ter participado de um momento que era importante pra você. "
    "Você é uma pessoa que significa muito pra mim, e eu valorizo demais a nossa relação.|"
    "Espero que tenha sido um dia incrível, cheio de pessoas que gostam de você, "
    "porque você merece isso e muito mais. Mesmo não tendo estado lá, quero que saiba que "
    "pensei em você (por muitas horas, na verdade) e fiquei feliz por mais um ano da sua vida.|"
    "Eu preparei um presente simples, mas foi feito de coração. É uma forma pequena de "
    "demonstrar o quanto você é importante pra mim e o quanto eu valorizo o que temos.|"
    "Obrigado por ser quem você é. Obrigado por existir. Espero que a gente ainda comemore muitos aniversários juntos.|"
    "Com carinho, Dylan."
)

class Camera:
    def __init__(self, largura_mapa, altura_mapa):
        self.camera = pygame.Rect(0, 0, largura_mapa, altura_mapa)
        self.largura = largura_mapa
        self.altura = altura_mapa
        self.offset_tremor = pygame.math.Vector2(0, 0)

    def aplicar(self, entidade):
        if isinstance(entidade, pygame.Rect):
            return entidade.move(self.camera.topleft + self.offset_tremor)
        return entidade.rect.move(self.camera.topleft + self.offset_tremor)

    def update(self, alvo, int_w, int_h, intensidade_tremor):
        x = -alvo.rect.centerx + int(int_w / 2)
        y = -alvo.rect.centery + int(int_h / 2)
        x = min(0, max(-(self.largura - int_w), x))
        y = min(0, max(-(self.altura - int_h), y))
        self.camera = pygame.Rect(x, y, self.largura, self.altura)
        
        if intensidade_tremor > 0:
            self.offset_tremor.x = random.uniform(-intensidade_tremor, intensidade_tremor)
            self.offset_tremor.y = random.uniform(-intensidade_tremor, intensidade_tremor)
        else:
            self.offset_tremor.x = 0
            self.offset_tremor.y = 0

class Mapa:
    def __init__(self, arquivo_tmx):
        # Uso do resource_path no mapa
        self.tmx_data = pytmx.util_pygame.load_pygame(resource_path(arquivo_tmx))
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        self.paredes = []
        self.interativos = []
        self.spawn_pedro = (100, 250)
        self.spawn_deus = (1775, 310) 
        self.tem_deus = False
        self.carregar_dados()

    def carregar_dados(self):
        try:
            for obj in self.tmx_data.get_layer_by_name("spawn"):
                if obj.name == "spawn": self.spawn_pedro = (obj.x, obj.y)
        except: pass
        try:
            for obj in self.tmx_data.get_layer_by_name("spawn_deus"):
                if obj.name == "spawn_deus": 
                    self.spawn_deus = (obj.x, 310) 
                    self.tem_deus = True
        except: pass
        try:
            for obj in self.tmx_data.get_layer_by_name("colisoes"):
                self.paredes.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        except: pass
        try:
            for obj in self.tmx_data.get_layer_by_name("interacoes"):
                if "interact" in obj.properties:
                    self.interativos.append({
                        "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                        "texto": obj.properties["interact"],
                        "nome": obj.name 
                    })
        except: pass

    def desenhar(self, superficie, camera):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        pos = (x * self.tmx_data.tilewidth + camera.camera.x + camera.offset_tremor.x, 
                               y * self.tmx_data.tileheight + camera.camera.y + camera.offset_tremor.y)
                        superficie.blit(tile, pos)

class Deus(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet_path):
        super().__init__()
        self.spritesheet = pygame.image.load(resource_path(sheet_path)).convert_alpha()
        self.frames = []
        larg_frame = 224
        for i in range(15):
            self.frames.append(self.spritesheet.subsurface(pygame.Rect(i*larg_frame, 0, larg_frame, 240)))
        self.image = self.frames[0]
        self.rect = self.image.get_rect(bottomleft=(x - 112, y)) 
        self.timer_anim = 0.0

    def update(self):
        self.timer_anim += 0.1
        self.image = self.frames[int(self.timer_anim % 15)]

class Pedro(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet_path):
        super().__init__()
        self.spritesheet = pygame.image.load(resource_path(sheet_path)).convert_alpha()
        self.frames = []
        for row in range(5):
            for col in range(4):
                self.frames.append(self.spritesheet.subsurface(pygame.Rect(col*16, row*16, 16, 16)))
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocidade = 1.5
        self.direcao = pygame.math.Vector2()
        self.olhando_direita = True
        self.timer_anim = 0.0

    def animar(self):
        self.timer_anim += 0.15
        if self.direcao.magnitude() > 0:
            idx = 12 + int(self.timer_anim % 4)
        else:
            idx = int(self.timer_anim % 4)
        img = self.frames[idx % len(self.frames)]
        if self.olhando_direita:
            img = pygame.transform.flip(img, True, False)
        self.image = img

    def update(self, paredes, bloqueado):
        if bloqueado:
            self.direcao = pygame.math.Vector2(0, 0)
            self.animar(); return
        keys = pygame.key.get_pressed()
        self.direcao.x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direcao.y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if self.direcao.x > 0: self.olhando_direita = True
        elif self.direcao.x < 0: self.olhando_direita = False
        if self.direcao.magnitude() > 0: self.direcao = self.direcao.normalize()
        self.pos.x += self.direcao.x * self.velocidade
        self.rect.x = round(self.pos.x)
        self.checar_colisao(paredes, 'horizontal')
        self.pos.y += self.direcao.y * self.velocidade
        self.rect.y = round(self.pos.y)
        self.checar_colisao(paredes, 'vertical')
        self.animar()

    def checar_colisao(self, paredes, orientacao):
        for parede in paredes:
            if self.rect.colliderect(parede):
                if orientacao == 'horizontal':
                    if self.direcao.x > 0: self.rect.right = parede.left
                    else: self.rect.left = parede.right
                    self.pos.x = self.rect.x
                else:
                    if self.direcao.y > 0: self.rect.bottom = parede.top
                    else: self.rect.top = parede.bottom
                    self.pos.y = self.rect.y

class Dialogo:
    def __init__(self, fonte):
        self.fonte = fonte
        self.ativo = False
        self.paginas = []
        self.pagina_atual = 0
        self.largura_caixa = 1000
        self.altura_caixa = 180
        self.x_caixa = (SCREEN_WIDTH - self.largura_caixa) // 2
        self.y_caixa = 500
        self.texto_completo_pagina = ""
        self.index_typewriter = 0
        self.timer_typewriter = 0.0
        self.ultimo_index_inteiro = -1
        self.e_deus = False 
        
        caminho_som = resource_path(os.path.join("assets", "type.wav"))
        try:
            if os.path.exists(caminho_som):
                self.som_type = pygame.mixer.Sound(caminho_som)
                self.som_type.set_volume(0.3)
            else: self.som_type = None
        except: self.som_type = None

    def iniciar(self, texto, e_deus=False, custom_pos=None):
        self.e_deus = e_deus
        self.y_caixa = custom_pos if custom_pos else 500
        self.paginas = []
        blocos = texto.split('|')
        for bloco in blocos:
            linhas = self.quebrar_texto(bloco.strip().strip('"'))
            max_l = 8 if custom_pos else 3
            for i in range(0, len(linhas), max_l):
                self.paginas.append(" ".join(linhas[i : i + max_l]).strip())
        self.pagina_atual = 0
        self.set_pagina_typewriter()
        self.ativo = True

    def quebrar_texto(self, texto):
        palavras = texto.split(' ')
        linhas, linha_atual = [], ""
        limite = self.largura_caixa - 80
        for p in palavras:
            teste = linha_atual + p + " "
            if self.fonte.size(teste)[0] < limite: linha_atual = teste
            else: linhas.append(linha_atual); linha_atual = p + " "
        linhas.append(linha_atual)
        return linhas

    def set_pagina_typewriter(self):
        self.texto_completo_pagina = self.paginas[self.pagina_atual]
        self.index_typewriter, self.timer_typewriter, self.ultimo_index_inteiro = 0, 0.0, -1

    def desenhar(self, tela, sem_caixa=False):
        if not self.ativo: return
        if not sem_caixa:
            pygame.draw.rect(tela, (20, 20, 20), (self.x_caixa, self.y_caixa, self.largura_caixa, self.altura_caixa))
            pygame.draw.rect(tela, (255, 255, 255), (self.x_caixa, self.y_caixa, self.largura_caixa, self.altura_caixa), 4)

        self.timer_typewriter += 0.8
        current_idx = int(self.timer_typewriter)
        if current_idx < len(self.texto_completo_pagina):
            if current_idx > self.ultimo_index_inteiro:
                char = self.texto_completo_pagina[current_idx]
                if char != " " and self.som_type: self.som_type.play()
                self.ultimo_index_inteiro = current_idx
            self.index_typewriter = current_idx
        else: self.index_typewriter = len(self.texto_completo_pagina)

        texto_parcial = self.texto_completo_pagina[:self.index_typewriter]
        linhas = self.quebrar_texto(texto_parcial)
        y_pos = self.y_caixa + 30
        for i, linha in enumerate(linhas):
            surf = self.fonte.render(linha.strip(), False, (255, 255, 255))
            tela.blit(surf, (self.x_caixa + 40, y_pos + i*35))
        
        if self.index_typewriter >= len(self.texto_completo_pagina):
            btn_txt = self.fonte.render("[E] CONTINUAR", False, (200, 200, 200))
            tela.blit(btn_txt, (self.x_caixa + self.largura_caixa - 180, self.y_caixa + self.altura_caixa - 45))

def main():
    pygame.init()
    pygame.mixer.init() 
    
    tela_real = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    
    if os.path.exists(GAME_ICON_PATH):
        icone = pygame.transform.scale(pygame.image.load(GAME_ICON_PATH).subsurface(0,0,16,16), (32,32))
        pygame.display.set_icon(icone)

    clock = pygame.time.Clock()
    estado_jogo = "INTRO" 
    intensidade_tremor = 0.0

    mapa = Mapa("projeto_aniversario.tmx")
    pedro = Pedro(mapa.spawn_pedro[0], mapa.spawn_pedro[1], "cat-Sheet.png")
    deus = Deus(mapa.spawn_deus[0], mapa.spawn_deus[1], "assets/Agis.png") if mapa.tem_deus else None
    camera = Camera(mapa.width, mapa.height)
    
    # Fontes com resource_path
    try: fonte = pygame.font.Font(resource_path(os.path.join("assets", "VT323-Regular.ttf")), 36)
    except: fonte = pygame.font.SysFont("Courier New", 24, bold=True)
    
    gerenciador_dialogo = Dialogo(fonte)
    gerenciador_intro = Dialogo(fonte)
    gerenciador_intro.iniciar(TEXTO_INTRO, False, custom_pos=100)
    gerenciador_intro.altura_caixa = 500

    audio_estado = "PARADO"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if estado_jogo == "INTRO":
                    if gerenciador_intro.index_typewriter < len(gerenciador_intro.texto_completo_pagina):
                        gerenciador_intro.index_typewriter = len(gerenciador_intro.texto_completo_pagina)
                        gerenciador_intro.timer_typewriter = float(len(gerenciador_intro.texto_completo_pagina))
                    else:
                        gerenciador_intro.pagina_atual += 1
                        if gerenciador_intro.pagina_atual >= len(gerenciador_intro.paginas):
                            estado_jogo = "JOGANDO"
                            try:
                                pygame.mixer.music.load(resource_path(os.path.join("assets", "Ballerina.wav")))
                                pygame.mixer.music.set_volume(0.5); pygame.mixer.music.play(-1)
                                audio_estado = "BALLERINA"
                            except: pass
                        else: gerenciador_intro.set_pagina_typewriter()

                elif estado_jogo == "JOGANDO":
                    if gerenciador_dialogo.ativo:
                        if gerenciador_dialogo.index_typewriter < len(gerenciador_dialogo.texto_completo_pagina):
                            gerenciador_dialogo.index_typewriter = len(gerenciador_dialogo.texto_completo_pagina)
                            gerenciador_dialogo.timer_typewriter = float(len(gerenciador_dialogo.texto_completo_pagina))
                        else:
                            gerenciador_dialogo.pagina_atual += 1
                            if gerenciador_dialogo.pagina_atual >= len(gerenciador_dialogo.paginas):
                                gerenciador_dialogo.ativo = False
                            else:
                                gerenciador_dialogo.set_pagina_typewriter()
                                if gerenciador_dialogo.e_deus: intensidade_tremor = 3.0
                    else:
                        hb = pedro.rect.inflate(30, 30)
                        for item in mapa.interativos:
                            if hb.colliderect(item["rect"]):
                                e_o_deus = (item["nome"] == "NPC")
                                gerenciador_dialogo.iniciar(item["texto"], e_o_deus)
                                if e_o_deus: intensidade_tremor = 8.0

        if estado_jogo == "INTRO":
            tela_real.fill((0, 0, 0))
            gerenciador_intro.desenhar(tela_real, sem_caixa=True)
        else:
            if deus:
                dist = pedro.pos.distance_to(pygame.math.Vector2(mapa.spawn_deus))
                global ZOOM_ATUAL, ZOOM_ALVO
                ZOOM_ALVO = 2.0 if dist < 220 else 5.0
                
                if dist < 350 and audio_estado == "BALLERINA":
                    pygame.mixer.music.fadeout(1000); audio_estado = "TRANS_PARA_SUSPENSE"
                if audio_estado == "TRANS_PARA_SUSPENSE" and not pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.load(resource_path(os.path.join("assets", "suspense.wav")))
                        pygame.mixer.music.play(-1); audio_estado = "SUSPENSE"
                    except: pass
                if dist > 400 and audio_estado == "SUSPENSE":
                    pygame.mixer.music.fadeout(1000); audio_estado = "TRANS_PARA_BALLERINA"
                if audio_estado == "TRANS_PARA_BALLERINA" and not pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.load(resource_path(os.path.join("assets", "Ballerina.wav")))
                        pygame.mixer.music.set_volume(0.5); pygame.mixer.music.play(-1)
                        audio_estado = "BALLERINA"
                    except: pass
                if audio_estado == "SUSPENSE":
                    vol = 1.0 - ((max(100, min(dist, 350)) - 100) / 250)
                    pygame.mixer.music.set_volume(max(0.1, vol * 0.8))
            
            ZOOM_ATUAL += (ZOOM_ALVO - ZOOM_ATUAL) * 0.05
            intensidade_tremor = max(0, intensidade_tremor - 0.4)
            int_w, int_h = int(SCREEN_WIDTH / ZOOM_ATUAL), int(SCREEN_HEIGHT / ZOOM_ATUAL)
            canvas = pygame.Surface((int_w, int_h))

            pedro.update(mapa.paredes, gerenciador_dialogo.ativo)
            if deus: deus.update()
            camera.update(pedro, int_w, int_h, intensidade_tremor)

            canvas.fill((25, 25, 25))
            mapa.desenhar(canvas, camera)
            if deus: canvas.blit(deus.image, camera.aplicar(deus))
            canvas.blit(pedro.image, camera.aplicar(pedro))

            tela_real.blit(pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
            if gerenciador_dialogo.ativo: gerenciador_dialogo.desenhar(tela_real)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__": main()