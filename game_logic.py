class Board:
    def __init__(self, row=6, col=8):
        self.row = row
        self.col = col
        self.board = [['w' for _ in range(self.col)] for _ in range(self.row)]
        self.ships_count = 0  # Total ship cells count
        self.hit_count = 0    # Total successful hits count
         
    def print_board(self, hide_ships=False, is_enemy=False):
        for row in self.board:
            if is_enemy:
                print(' '.join(['S' if cell == 'H' else 'M' if cell == 'M' else 'w' for cell in row]))
            elif hide_ships:
                print(' '.join(['w' if cell == 'S' else cell for cell in row]))
            else:
                print(' '.join(row))
        print("\n")

    def get_board_state(self, hide_ships=False):
        """Get board state for network transmission"""
        state = []
        for row in self.board:
            if hide_ships:
                state.append(['w' if cell == 'S' else cell for cell in row])
            else:
                state.append(row[:])
        return state

    def is_valid_position(self, size, direction, x, y):
        """Check if ship placement is valid"""
        if not (0 <= x < self.row and 0 <= y < self.col):
            return False
        if direction == 'h' and y + size > self.col:
            return False
        if direction == 'v' and x + size > self.row:
            return False
        for i in range(size):
            if direction == 'h' and self.board[x][y + i] != 'w':
                return False
            if direction == 'v' and self.board[x + i][y] != 'w':
                return False
        return True

    def ship_installation(self, size, direction, start_point):
        """Place a ship on the board"""
        x, y = start_point
        if not self.is_valid_position(size, direction, x, y):
            print("❌ You can't place the ship here!")
            return False
        else:
            for i in range(size):
                if direction == 'h':
                    self.board[x][y + i] = 'S'
                else:
                    self.board[x + i][y] = 'S'
            self.ships_count += size
            return True

    def shoot(self, x, y):
        """Process a shot at coordinates (x,y)"""
        if not (0 <= x < self.row and 0 <= y < self.col):  
            print("🚫 Out of Bounds! Try again.")
            return None  # player should shoot again

        if self.board[x][y] == 'S':
            self.board[x][y] = 'H'
            self.hit_count += 1
            print("🎯 Hit! You get another turn!")
            return True  # player should shoot again

        elif self.board[x][y] == 'w':
            self.board[x][y] = 'M'
            print("❌ Miss! Next player's turn.")
            return False # Next player's turn

        else:
            print("⚠️ Already shot here! Try again.")
            return None # player should shoot again
            
    def has_ships(self):
        """Check if the board has any ships placed"""
        return self.ships_count > 0
        
    def all_ships_sunk(self):
        """Check if all ships on the board have been sunk"""
        return self.ships_count > 0 and self.hit_count >= self.ships_count


class Game:
    
    def __init__(self):
        self.player1_board = Board()
        self.player2_board = Board()
        self.current_player = 1

    def print_boards(self):
        """Display the active player's board and a limited view of opponent's board"""
        if self.current_player == 1:
            print("🔵 Player 1's Board:")
            self.player2_board.print_board(is_enemy=True)
        else:
            print("🔴 Player 2's Board:")
            self.player1_board.print_board(is_enemy=True)

    def switch_turn(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def play_turn(self):
        while True:
            print(f"\n🎯 Player {self.current_player}'s Turn!")
            self.print_boards()

            while True:
                try:
                    x = int(input("Enter row (0-5): "))
                    y = int(input("Enter column (0-7): "))

                    if self.current_player == 1:
                        result = self.player2_board.shoot(x, y)
                    else:
                        result = self.player1_board.shoot(x, y)

                    if result is not None:   
                        break

                except ValueError:
                    print("⚠️ Invalid input! Please enter numbers.")

            if not result: 
                self.switch_turn()
                break

    def start_game(self):
        print("🎮 Battleship Game Started!")
        while True:
            self.play_turn()
