import socket
import json
import threading
import pygame
import sys
import time
from pygame.locals import *

class BattleshipClient:
    def __init__(self, host='127.0.0.1', port=54321):
        # Network settings
        self.host = host
        self.port = port
        self.client_socket = None
        self.connected = False
        self.player_id = None
        self.current_player = None
        self.game_started = False
        self.winner = None
        self.message = "Connecting to server..."
        
        # Game settings
        self.my_board = [['w' for _ in range(8)] for _ in range(6)]
        self.enemy_board = [['w' for _ in range(8)] for _ in range(6)]
        
        # Ship placement
        self.placing_ships = False
        self.ships_to_place = []
        self.placed_ships = []  # Track all placed ships
        self.current_ship = None
        self.current_direction = 'h'  # 'h' for horizontal, 'v' for vertical
        
        # Initialize pygame
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Battleship Game')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.title_font = pygame.font.SysFont('Arial', 30, True)
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 0, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.GREY = (200, 200, 200)
        self.DARK_BLUE = (0, 0, 128)
        self.LIGHT_BLUE = (173, 216, 230)
        
        # Board settings
        self.cell_size = 40
        self.board_margin = 50
        self.my_board_x = self.board_margin
        self.my_board_y = 120
        self.enemy_board_x = self.width - self.board_margin - 8 * self.cell_size
        self.enemy_board_y = 120
        
        # Connect to server and start game
        self.connect_to_server()
    
    def connect_to_server(self):
        """Connect to the game server"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            
            # Start thread to receive messages
            threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            self.message = f"Failed to connect: {e}"
    
    def receive_messages(self):
        """Receive and process messages from the server"""
        while self.connected:
            try:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break
                
                message = json.loads(data)
                self.process_message(message)
                
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
        
        self.connected = False
        self.message = "Disconnected from server"
    
    def process_message(self, message):
        """Process messages from the server"""
        msg_type = message.get("type", "")
        
        if msg_type == "init":
            self.player_id = message.get("player_id")
            self.message = f"You are Player {self.player_id}"
        
        elif msg_type == "message":
            self.message = message.get("content", "")
        
        elif msg_type == "place_ships_request":
            self.placing_ships = True
            self.ships_to_place = []
            self.placed_ships = []  # Reset placed ships
            sizes = message.get("sizes", [3, 2])
            for size in sizes:
                self.ships_to_place.append({"size": size, "direction": "h", "position": None})
            
            if self.ships_to_place:
                self.current_ship = self.ships_to_place[0]
        
        elif msg_type == "ships_placed":
            if message.get("success", False):
                self.message = "Ships placed successfully. Waiting for opponent..."
            else:
                self.message = "Invalid ship placement. Try again!"
                self.placing_ships = True
                # Reset current ship
                if self.ships_to_place:
                    self.current_ship = self.ships_to_place[0]
        
        elif msg_type == "game_start":
            self.game_started = True
            self.current_player = message.get("current_player")
            self.message = f"Game started! {'Your turn' if self.current_player == self.player_id else 'Opponent\'s turn'}"
        
        elif msg_type == "shoot_result":
            shooter = message.get("shooter")
            position = message.get("position", [0, 0])
            result = message.get("result")
            x, y = position
            
            # Update the appropriate board
            if shooter == self.player_id:  # I shot
                if result == "hit":
                    self.enemy_board[x][y] = "H"
                    self.message = "🎯 Hit! Your turn again"
                elif result == "miss":
                    self.enemy_board[x][y] = "M"
                    self.message = "❌ Miss! Opponent's turn"
            else:  # Opponent shot
                if result == "hit":
                    self.my_board[x][y] = "H"
                    self.message = "😱 Your ship was hit! Opponent goes again"
                elif result == "miss":
                    self.my_board[x][y] = "M"
                    self.message = "😅 Opponent missed! Your turn"
        
        elif msg_type == "turn_change":
            self.current_player = message.get("current_player")
            if self.current_player == self.player_id:
                self.message = "🎮 Your turn!"
            else:
                self.message = "⏳ Waiting for opponent..."
        
        elif msg_type == "game_over":
            winner = message.get("winner")
            self.winner = winner
            if winner == self.player_id:
                self.message = "🏆 You won the game!"
            else:
                self.message = "😢 You lost the game."
        
        elif msg_type == "player_disconnected":
            self.message = message.get("message", "Opponent disconnected")
            self.game_started = False
    
    def send_message(self, message):
        """Send a message to the server"""
        if self.connected:
            try:
                self.client_socket.send(json.dumps(message).encode())
            except Exception as e:
                print(f"Error sending message: {e}")
    
    def place_ship(self, x, y):
        """Place a ship during setup phase"""
        if not self.current_ship:
            return
        
        # Convert screen coordinates to board indices
        board_x = (x - self.my_board_x) // self.cell_size
        board_y = (y - self.my_board_y) // self.cell_size
        
        if 0 <= board_y < 6 and 0 <= board_x < 8:
            # Validate placement
            size = self.current_ship["size"]
            direction = self.current_ship["direction"]
            
            # Check if ship placement is valid
            valid = True
            for i in range(size):
                check_x = board_y
                check_y = board_x + i if direction == 'h' else board_x
                check_x = board_y + i if direction == 'v' else board_y
                
                if not (0 <= check_x < 6 and 0 <= check_y < 8):
                    valid = False
                    break
                if self.my_board[check_x][check_y] != 'w':
                    valid = False
                    break
            
            if valid:
                # Place ship on client-side board
                for i in range(size):
                    place_x = board_y
                    place_y = board_x + i if direction == 'h' else board_x
                    place_x = board_y + i if direction == 'v' else board_y
                    
                    self.my_board[place_x][place_y] = 'S'
                
                # Create a copy of current_ship with position and add to placed_ships
                placed_ship = {
                    "size": self.current_ship["size"],
                    "direction": self.current_ship["direction"],
                    "position": [board_y, board_x]  # Note the coordinates order
                }
                self.placed_ships.append(placed_ship)
                
                # Remove from ships_to_place and update current_ship
                self.ships_to_place.remove(self.current_ship)
                
                # If all ships placed, send to server
                if not self.ships_to_place:
                    self.send_message({
                        "type": "place_ships",
                        "ships": self.placed_ships
                    })
                    self.placing_ships = False
                    self.current_ship = None
                else:
                    self.current_ship = self.ships_to_place[0]
    
    def rotate_ship(self):
        """Rotate the current ship during placement"""
        if self.current_ship:
            self.current_ship["direction"] = 'v' if self.current_ship["direction"] == 'h' else 'h'
    
    def shoot(self, x, y):
        """Send a shot to the server"""
        if not self.game_started or self.current_player != self.player_id or self.winner:
            return
        
        # Convert screen coordinates to board indices
        board_x = (x - self.enemy_board_x) // self.cell_size
        board_y = (y - self.enemy_board_y) // self.cell_size
        
        if 0 <= board_y < 6 and 0 <= board_x < 8:
            # Check if cell was already shot
            if self.enemy_board[board_y][board_x] not in ['H', 'M']:
                self.send_message({
                    "type": "shoot",
                    "position": [board_y, board_x]  # Note the coordinates order
                })
    
    def draw_board(self, x, y, board, is_enemy=False):
        """Draw a game board"""
        # Draw board grid
        for row in range(6):
            for col in range(8):
                cell_value = board[row][col]
                color = self.WHITE
                
                if cell_value == 'S' and not is_enemy:
                    color = self.GREY
                elif cell_value == 'H':
                    color = self.RED
                elif cell_value == 'M':
                    color = self.BLUE
                
                pygame.draw.rect(self.screen, color, 
                                (x + col * self.cell_size, y + row * self.cell_size, 
                                 self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, self.BLACK, 
                                (x + col * self.cell_size, y + row * self.cell_size, 
                                 self.cell_size, self.cell_size), 1)
        
        # Draw row numbers
        for row in range(6):
            text = self.font.render(str(row), True, self.BLACK)
            self.screen.blit(text, (x - 20, y + row * self.cell_size + 10))
        
        # Draw column numbers
        for col in range(8):
            text = self.font.render(str(col), True, self.BLACK)
            self.screen.blit(text, (x + col * self.cell_size + 15, y - 25))
    
    def draw_ship_preview(self, mouse_pos):
        """Draw a preview of the ship being placed"""
        if not self.placing_ships or not self.current_ship:
            return
        
        x, y = mouse_pos
        board_x = (x - self.my_board_x) // self.cell_size
        board_y = (y - self.my_board_y) // self.cell_size
        
        if 0 <= board_y < 6 and 0 <= board_x < 8:
            size = self.current_ship["size"]
            direction = self.current_ship["direction"]
            
            # Check if position is valid
            valid = True
            for i in range(size):
                check_x = board_y
                check_y = board_x + i if direction == 'h' else board_x
                check_x = board_y + i if direction == 'v' else board_y
                
                if not (0 <= check_x < 6 and 0 <= check_y < 8):
                    valid = False
                    break
                if self.my_board[check_x][check_y] != 'w':
                    valid = False
                    break
            
            # Draw preview
            for i in range(size):
                preview_x = self.my_board_x + (board_x + (i if direction == 'h' else 0)) * self.cell_size
                preview_y = self.my_board_y + (board_y + (i if direction == 'v' else 0)) * self.cell_size
                
                if valid:
                    pygame.draw.rect(self.screen, self.GREEN, 
                                    (preview_x, preview_y, self.cell_size, self.cell_size), 3)
                else:
                    pygame.draw.rect(self.screen, self.RED, 
                                    (preview_x, preview_y, self.cell_size, self.cell_size), 3)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        if self.placing_ships:
                            # Check if click is on my board
                            if (self.my_board_x <= mouse_pos[0] <= self.my_board_x + 8 * self.cell_size and
                                self.my_board_y <= mouse_pos[1] <= self.my_board_y + 6 * self.cell_size):
                                self.place_ship(mouse_pos[0], mouse_pos[1])
                        
                        elif self.game_started and self.current_player == self.player_id and not self.winner:
                            # Check if click is on enemy board
                            if (self.enemy_board_x <= mouse_pos[0] <= self.enemy_board_x + 8 * self.cell_size and
                                self.enemy_board_y <= mouse_pos[1] <= self.enemy_board_y + 6 * self.cell_size):
                                self.shoot(mouse_pos[0], mouse_pos[1])
                
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE and self.placing_ships:
                        self.rotate_ship()
            
            # Drawing
            self.screen.fill(self.WHITE)
            
            # Draw title
            title = self.title_font.render("BATTLESHIP", True, self.DARK_BLUE)
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))
            
            # Draw player info
            if self.player_id:
                player_text = self.font.render(f"Player {self.player_id}", True, 
                                           self.BLUE if self.player_id == 1 else self.RED)
                self.screen.blit(player_text, (20, 60))
            
            # Draw message
            msg_text = self.font.render(self.message, True, self.BLACK)
            self.screen.blit(msg_text, (self.width // 2 - msg_text.get_width() // 2, 60))
            
            # Draw boards
            if self.connected:
                # Draw my board title
                my_board_title = self.font.render("YOUR BOARD", True, self.BLACK)
                self.screen.blit(my_board_title, 
                               (self.my_board_x + 4 * self.cell_size - my_board_title.get_width() // 2, 
                                self.my_board_y - 50))
                
                # Draw enemy board title
                enemy_board_title = self.font.render("OPPONENT'S BOARD", True, self.BLACK)
                self.screen.blit(enemy_board_title, 
                               (self.enemy_board_x + 4 * self.cell_size - enemy_board_title.get_width() // 2, 
                                self.enemy_board_y - 50))
                
                # Draw boards
                self.draw_board(self.my_board_x, self.my_board_y, self.my_board, False)
                self.draw_board(self.enemy_board_x, self.enemy_board_y, self.enemy_board, True)
                
                # Draw ship preview during placement
                if self.placing_ships and self.current_ship:
                    self.draw_ship_preview(mouse_pos)
                    
                    # Draw placement instructions
                    instructions1 = self.font.render(f"Place your {self.current_ship['size']}-cell ship", True, self.BLACK)
                    instructions2 = self.font.render("Left-click to place, Space to rotate", True, self.BLACK)
                    self.screen.blit(instructions1, (self.width // 2 - instructions1.get_width() // 2, self.height - 60))
                    self.screen.blit(instructions2, (self.width // 2 - instructions2.get_width() // 2, self.height - 30))
                
                # Draw turn indicator if game started
                if self.game_started and not self.winner:
                    turn_text = self.font.render(
                        "YOUR TURN" if self.current_player == self.player_id else "OPPONENT'S TURN", 
                        True, self.GREEN if self.current_player == self.player_id else self.RED)
                    self.screen.blit(turn_text, (self.width // 2 - turn_text.get_width() // 2, self.height - 30))
                
                # Draw game over message
                if self.winner:
                    game_over_text = self.title_font.render(
                        "YOU WIN!" if self.winner == self.player_id else "YOU LOSE!", 
                        True, self.GREEN if self.winner == self.player_id else self.RED)
                    self.screen.blit(game_over_text, 
                                   (self.width // 2 - game_over_text.get_width() // 2, self.height - 50))
            
            pygame.display.flip()
            self.clock.tick(30)
        
        # Clean up
        pygame.quit()
        if self.client_socket:
            self.client_socket.close()


if __name__ == "__main__":
    client = BattleshipClient()
    client.run()