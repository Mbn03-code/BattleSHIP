import socket
import json
import threading
from game_logic import Board

class BattleshipServer:
    def __init__(self, host='127.0.0.1', port=54321):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        
        self.clients = [None, None]  # Socket for each player
        self.boards = [Board(), Board()]  # Game board for each player
        self.current_player = 0  # Current player (0 or 1)
        self.game_started = False
        self.ships_placed = [False, False]  # Track if players have placed ships
        
        print("🚀 Battleship Server is ready...")
    
    def accept_clients(self):
        """Accept client connections"""
        for i in range(2):
            client, addr = self.server_socket.accept()
            self.clients[i] = client
            
            # Send player number
            self.send_to_client(i, {"type": "init", "player_id": i+1})
            
            print(f"🎮 Player {i+1} connected from {addr}")
            
            # Notify players
            if i == 0:
                self.send_to_client(i, {"type": "message", "content": "✅ You are Player 1! Waiting for Player 2..."})
            else:
                self.send_to_client(i, {"type": "message", "content": "✅ You are Player 2! Game is ready to start..."})
                self.send_to_client(0, {"type": "message", "content": "🎮 Player 2 has joined! Game is ready to start..."})
        
        print("🎉 Both players connected! Game can begin.")
        
        # Start receiving player messages in separate threads
        threading.Thread(target=self.handle_player, args=(0,)).start()
        threading.Thread(target=self.handle_player, args=(1,)).start()
    
        # Send request to place ships
        self.send_to_both({"type": "place_ships_request", "sizes": [3, 2]})
    
    def send_to_client(self, player_id, data):
        """Send data to a client"""
        try:
            self.clients[player_id].send(json.dumps(data).encode())
        except Exception as e:
            print(f"Error sending to player {player_id+1}: {e}")
    
    def handle_player(self, player_id):
        """Handle messages from a player"""
        client = self.clients[player_id]
        
        while True:
            try:
                data = client.recv(4096).decode()
                if not data:
                    break
                
                message = json.loads(data)
                self.process_message(player_id, message)
                
            except Exception as e:
                print(f"Error receiving from player {player_id+1}: {e}")
                break
        
        print(f"Connection with player {player_id+1} lost")
        self.clients[player_id] = None
        
        # Notify the other player
        other_player = 1 - player_id
        if self.clients[other_player]:
            self.send_to_client(other_player, {
                "type": "player_disconnected",
                "message": f"Player {player_id+1} disconnected. Game over."
            })
    
    def process_message(self, player_id, message):
        """Process messages from players"""
        msg_type = message.get("type", "")
        
        if msg_type == "place_ships":
            # Handle ship placement
            ships = message.get("ships", [])
            success = True
            for ship in ships:
                size = ship.get("size")
                direction = ship.get("direction")
                x, y = ship.get("position")
                if not self.boards[player_id].ship_installation(size, direction, (x, y)):
                    success = False
                    break
            
            if success:
                self.ships_placed[player_id] = True
                self.send_to_client(player_id, {"type": "ships_placed", "success": True})
                
                # Check if both players have placed ships to start the game
                if all(self.ships_placed):
                    self.game_started = True
                    self.send_to_both({
                        "type": "game_start", 
                        "current_player": self.current_player + 1
                    })
            else:
                self.send_to_client(player_id, {"type": "ships_placed", "success": False})
        
        elif msg_type == "shoot" and self.game_started:
            # Handle shots
            if player_id == self.current_player:  # Only process if it's this player's turn
                x, y = message.get("position")
                target_board = self.boards[1 - player_id]  # Opponent's board
                
                result = target_board.shoot(x, y)
                
                # Send result to both players
                self.send_to_both({
                    "type": "shoot_result",
                    "shooter": player_id + 1,
                    "position": [x, y],
                    "result": "hit" if result is True else "miss" if result is False else "invalid",
                    "game_over": target_board.all_ships_sunk() if result is not None else False
                })
                
                # Change turn if shot missed
                if result is False:
                    self.current_player = 1 - self.current_player
                    self.send_to_both({"type": "turn_change", "current_player": self.current_player + 1})
                
                # Game over check
                if result is not None and target_board.all_ships_sunk():
                    self.send_to_both({
                        "type": "game_over",
                        "winner": player_id + 1
                    })
    
    def send_to_both(self, data):
        """Send data to both players"""
        for i in range(2):
            if self.clients[i]:
                self.send_to_client(i, data)
    
    def run(self):
        """Main server execution"""
        try:
            print(f"Server started on {self.host}:{self.port}")
            self.accept_clients()
        except KeyboardInterrupt:
            print("Server stopped by user")
        finally:
            for client in self.clients:
                if client:
                    client.close()
            self.server_socket.close()
