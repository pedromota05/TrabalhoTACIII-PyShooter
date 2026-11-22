"""
config.py — Configurações centralizadas do PyShooter.

Todas as constantes de gameplay, física, renderização e UI são
definidas aqui para facilitar ajustes e evitar "números mágicos"
espalhados pelo código.
"""
# ---------------------------------------------------------------------------
#  Tela
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 1200
# Define a altura da tela para 640 (múltiplo perfeito de 16 ROWS: 16 * 40 = 640) 
# Isso evita a faixa preta (gap) na parte inferior da tela.
SCREEN_HEIGHT = 640

# ---------------------------------------------------------------------------
#  Botões (pixel-art em resolução nativa ~810x305 px)
# ---------------------------------------------------------------------------
# A classe Button aplica o MESMO fator em largura e altura, então qualquer
# escala uniforme preserva a proporção "de fábrica" de cada arte (sem
# esticar/achatar o texto). Não existe mais tamanho fixo global.
MENU_SCALE = 0.28             # ~228x86 px por botão (grade 2x3 do Menu)
GAME_OVER_BUTTON_SCALE = 0.45  # mesmo tamanho para o Restart
MENU_MARGIN_X = 40             # distância de cada coluna ao centro da tela
MENU_SPACING_Y = 20            # espaço vertical entre as linhas da grade
MENU_START_Y = 220             # Y da primeira linha (abaixo do título)
LAN_BUTTON_SCALE = 0.28        # botões do menu Multiplayer LAN (mesma escala do Menu)
LAN_SPACING_Y = 20             # espaço vertical entre os elementos do menu LAN
EDITOR_MENU_BTN_SCALE = 0.12   # botão MENU do Editor de Fases (~85x42 px, alinhado a SAVE/LOAD)
SETTINGS_BTN_SCALE = 0.12      # botão de engrenagem no canto superior direito (~59x61 px)

# ---------------------------------------------------------------------------
#  Timing
# ---------------------------------------------------------------------------
FPS = 60

# ---------------------------------------------------------------------------
#  Estrutura dos Níveis
# ---------------------------------------------------------------------------
ROWS = 16
COLS = 200
TILE_SIZE = SCREEN_HEIGHT // ROWS  # 37
TILE_TYPES = 87
CHECKPOINT_TILE = 88  # bandeira de checkpoint (só editor/loader; o level_builder ignora)
MAX_LEVELS = 4

# Checkpoints da campanha: colunas (tiles) das bandeiras em cada fase.
# Escolhidas em chão firme antes dos trechos com mais mortes no bot humano
# (tools/bot_fases.py --humano). Não valem no Modo Desafio nem no multiplayer.
CHECKPOINTS = {1: [48, 95], 2: [29, 89], 3: [19, 83], 4: []}
CHECKPOINT_MSG_FRAMES = 90  # aviso "CHECKPOINT!" no HUD (1,5 s)
LEVEL_BANNER_FRAMES = 120  # aviso "FASE N" no início de cada fase (2 s)
SIGN_RANGE_X = 50   # distância horizontal (px) para interagir com a placa
SIGN_TEXTS = {
    1: [
        'Água funda mata na hora! Pule com W ou seta para cima. Caixas de munição recarregam seus tiros.',
        'Soldados à frente. Atire com ESPAÇO e jogue granadas com Q ou G.',
        'Logo adiante tem uma bandeira: é um checkpoint. Se morrer, você volta nela.',
        'Robôs aguentam mais tiros. Mantenha distância e use granadas.',
        'A saída está perto. Siga em frente!',
    ],
    2: ['Pântano! A água mata. Pule de plataforma em plataforma.'],
    3: [
        'Fase de gelo: a água gelada também é mortal.',
        'Snipers atiram de longe. Avance pulando e use granadas.',
        'Últimos inimigos antes da saída. Pegue a munição!',
    ],
}
SIGN_DEFAULT_TEXT = 'Continue em frente e cuidado com os inimigos!'
LEVELS_DIR = 'levels'

# ---------------------------------------------------------------------------
#  Câmera / Scroll
# ---------------------------------------------------------------------------
SCROLL_THRESH = 200

# ---------------------------------------------------------------------------
#  Física
# ---------------------------------------------------------------------------
GRAVITY = 0.75
TERMINAL_VELOCITY = 10   # FIX: clamping de velocidade de queda
JUMP_VELOCITY = -14

# ---------------------------------------------------------------------------
#  Player
# ---------------------------------------------------------------------------
PLAYER_SPEED = 5
PLAYER_SCALE = 1.55
# Cores do soldado: (nome, matiz HSV de destino; None = original verde)
PLAYER_COLORS = [('VERDE', None), ('AZUL', 215), ('VERMELHO', 0), ('AMARELO', 50), ('ROXO', 285)]
PLAYER_START_AMMO = 20
PLAYER_START_GRENADES = 5
SHARED_LIVES = 3  # vidas da campanha (compartilhadas no multiplayer)
LIVES_RESET_FRAMES = 180  # 3 s até o Host recomeçar a fase sem vidas

# ---------------------------------------------------------------------------
#  Enemy
# ---------------------------------------------------------------------------
ENEMY_SPEED = 2
ENEMY_SCALE = 1.55
ENEMY_AMMO = 20
ENEMY_GRENADES = 0
ENEMY_VISION_WIDTH = 150
ENEMY_VISION_HEIGHT = 20

# ---------------------------------------------------------------------------
#  Projétil (Bullet)
# ---------------------------------------------------------------------------
BULLET_SPEED = 10
BULLET_DAMAGE_TO_ENEMY = 25
BULLET_DAMAGE_TO_PLAYER = 5
SHOOT_COOLDOWN = 20

# Dash (tecla ESPAÇO)
DASH_SPEED = 16          # pixels por quadro durante o dash
DASH_FRAMES = 10         # duração do dash em quadros
DASH_COOLDOWN = 50       # quadros até poder dar outro dash
DASH_TRAIL = 6           # quantos "fantasmas" o rastro guarda

# ---------------------------------------------------------------------------
#  Granada
# ---------------------------------------------------------------------------
GRENADE_SPEED = 7
GRENADE_INITIAL_VEL_Y = -11
GRENADE_TIMER = 100
GRENADE_DAMAGE = 50
GRENADE_BLAST_RADIUS = TILE_SIZE * 2

# ---------------------------------------------------------------------------
#  Itens coletáveis
# ---------------------------------------------------------------------------
HEALTH_PICKUP = 25
AMMO_PICKUP = 15
GRENADE_PICKUP = 3

# ---------------------------------------------------------------------------
#  Animação
# ---------------------------------------------------------------------------
ANIMATION_COOLDOWN = 100
EXPLOSION_SPEED = 4
EXPLOSION_SCALE = 0.5

# ---------------------------------------------------------------------------
#  Cores
# ---------------------------------------------------------------------------
BG_COLOR = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)
YELLOW = (255, 255, 0)

# ---------------------------------------------------------------------------
#  UI
# ---------------------------------------------------------------------------
FONT_NAME = None  # Fonte padrão nativa do Pygame (mesma aparência original, sem UserWarning)
FONT_SIZE = 30
