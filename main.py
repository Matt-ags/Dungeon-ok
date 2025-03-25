import pygame
import json
import os

# Inicializa o Pygame
pygame.init()

# Carrega o arquivo JSON
with open('map.json') as f:
    map_data = json.load(f)

# Configurações do jogo
TILE_SIZE = map_data['tileSize']
MAP_WIDTH = map_data['mapWidth']
MAP_HEIGHT = map_data['mapHeight']
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

# Cria a tela
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jogo com Sistema de Camadas")
clock = pygame.time.Clock()

# Ordem de renderização das camadas (da mais ao fundo para a mais na frente)
LAYER_ORDER = [
    'Floor',         # Chão (fundo)
    'Walls',         # Paredes principais
    'Walls sides',   # Paredes laterais
    'Walls pillars', # Pilares
    'Doors',         # Portas
    'Traps',         # Armadilhas
    'Miscs',         # Objetos decorativos
    'Gargoyles',     # Gárgulas
    'Pickups'        # Itens coletáveis (topo)
]

# Classe para carregar a spritesheet
class SpriteSheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()
        
    def get_sprite(self, x, y, width, height):
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        return sprite

# Carrega a spritesheet
try:
    spritesheet = SpriteSheet('spritesheet.png')
except:
    spritesheet = None

# Mapeamento de tiles (ajuste conforme sua spritesheet)
TILE_MAPPING = {
    # Chão
    '43': (48, 80),
    
    # Paredes
    '27': (48, 48), '28': (64, 48), '29': (80, 48),
    '35': (48, 64), '36': (64, 64),
    '37': (80, 64), '38': (96, 64), '39': (112, 64),
    '40': (0, 80), '41': (16, 80), '42': (32, 80),
    
    # Portas
    '0': (0, 0), '1': (16, 0), '2': (32, 0), '3': (48, 0),
    '4': (64, 0), '5': (80, 0), '6': (96, 0), '7': (112, 0),
    '8': (0, 16), '9': (16, 16),
    
    # Gárgulas e objetos
    '30': (96, 48), '31': (112, 48), '32': (0, 64), 
    '33': (16, 64), '34': (32, 64),
    '10': (32, 16), '11': (48, 16), '12': (64, 16),
    '13': (80, 16), '14': (96, 16), '15': (112, 16),
    '16': (0, 32), '17': (16, 32), '18': (32, 32),
    '19': (48, 32), '20': (64, 32), '21': (80, 32),
    
    # Itens e armadilhas
    '22': (96, 32), '23': (112, 32), '24': (0, 48),
    '25': (16, 48), '26': (32, 48)
}

# Classe do jogador
class Player:
    def __init__(self, x, y):
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.speed = 3
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.collected_items = 0
        
        # Sprite do jogador
        if spritesheet:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((255, 0, 0))  # Vermelho
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((0, 0, 255))  # Azul como fallback
    
    def update(self, walls, pickups):
        keys = pygame.key.get_pressed()
        
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -self.speed
        if keys[pygame.K_RIGHT]:
            dx = self.speed
        if keys[pygame.K_UP]:
            dy = -self.speed
        if keys[pygame.K_DOWN]:
            dy = self.speed
            
        new_rect = self.rect.copy()
        new_rect.x += dx
        new_rect.y += dy
        
        can_move = True
        for wall in walls:
            if new_rect.colliderect(wall['rect']):
                can_move = False
                break
                
        if can_move:
            self.rect = new_rect
            self.x = self.rect.x
            self.y = self.rect.y
            
        for pickup in pickups[:]:
            if self.rect.colliderect(pickup['rect']):
                pickups.remove(pickup)
                self.collected_items += 1
    
    def draw(self, surface):
        if spritesheet:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (0, 0, 255), self.rect)

# Processa os dados do mapa
def process_map_data(map_data):
    tiles = []
    pickups = []
    
    for layer in map_data['layers']:
        layer_name = layer['name']
        for tile in layer['tiles']:
            tile_id = str(tile['id'])
            x = int(tile['x']) * TILE_SIZE
            y = int(tile['y']) * TILE_SIZE
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            
            if tile_id in TILE_MAPPING:
                sprite_pos = TILE_MAPPING[tile_id]
                if spritesheet:
                    image = spritesheet.get_sprite(sprite_pos[0], sprite_pos[1], TILE_SIZE, TILE_SIZE)
                else:
                    image = None
                    color = {
                        'Walls': (255, 255, 255),
                        'Walls sides': (200, 200, 200),
                        'Pickups': (0, 255, 0),
                        'Traps': (255, 0, 0),
                        'Doors': (139, 69, 19),
                        'Floor': (100, 100, 100)
                    }.get(layer_name, (100, 100, 100))
            else:
                image = None
                color = (100, 100, 100)
            
            tile_data = {
                'id': tile_id,
                'x': x,
                'y': y,
                'rect': rect,
                'image': image,
                'color': color if not image else None,
                'layer': layer_name,
                'collider': layer['collider'],
                'layer_order': LAYER_ORDER.index(layer_name) if layer_name in LAYER_ORDER else len(LAYER_ORDER)
            }
            
            if layer_name == 'Pickups' and not layer['collider']:
                pickups.append(tile_data)
            else:
                tiles.append(tile_data)
    
    return tiles, pickups

# Processa o mapa
tiles, pickups = process_map_data(map_data)

# Filtra paredes para colisão
walls = [tile for tile in tiles if tile['collider']]

# Cria o jogador
player = Player(10, 10)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    player.update(walls, pickups)
    
    # Desenha tudo na ordem correta
    screen.fill((0, 0, 0))
    
    # 1. Desenha tiles ordenados por camada
    for tile in sorted(tiles, key=lambda x: x['layer_order']):
        if tile['image']:
            screen.blit(tile['image'], (tile['x'], tile['y']))
        elif tile['color']:
            pygame.draw.rect(screen, tile['color'], tile['rect'])
    
    # 2. Desenha itens coletáveis (sempre no topo)
    for pickup in pickups:
        if pickup['image']:
            screen.blit(pickup['image'], (pickup['x'], pickup['y']))
        else:
            pygame.draw.rect(screen, (0, 255, 0), pickup['rect'])
    
    # 3. Desenha o jogador (por cima de tudo)
    player.draw(screen)
    
    # Mostra contador de itens
    font = pygame.font.SysFont(None, 24)
    text = font.render(f'Itens: {player.collected_items}', True, (255, 255, 255))
    screen.blit(text, (10, 10))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()