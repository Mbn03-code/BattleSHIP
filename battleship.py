class Board:
    def __init__(self, row=6, col=8):
        self.row = row
        self.col = col
        self.board = [['w' for _ in range(self.col)] for _ in range(self.row)]  

    def print_board(self, hide_ships=False, is_enemy=False):
        """چاپ برد، اگر hide_ships=True باشد، کشتی‌های حریف را نشان نمی‌دهد.
           اگر is_enemy=True باشد، فقط شلیک‌های موفق (S) و ناموفق (M) نشان داده می‌شوند.
        """
        for row in self.board:
            if is_enemy:
                print(' '.join(['S' if cell == 'H' else 'M' if cell == 'M' else 'w' for cell in row]))
            elif hide_ships:
                print(' '.join(['w' if cell == 'S' else cell for cell in row]))  
            else:
                print(' '.join(row))
        print("\n")

    def is_valid_position(self, size, direction, x, y):
        """بررسی معتبر بودن مکان کشتی"""
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
        """قرار دادن کشتی در برد"""
        x, y = start_point
        if not self.is_valid_position(size, direction, x, y):
            print("❌ You can't place the ship here!")
        else:
            for i in range(size):
                if direction == 'h':
                    self.board[x][y + i] = 'S'
                else:
                    self.board[x + i][y] = 'S'

    def shoot(self, x, y):
        """شلیک به برد"""
        if not (0 <= x < self.row and 0 <= y < self.col):  
            print("🚫 Out of Bounds! Try again.")
            return None  # مقدار None یعنی بازیکن باید دوباره وارد کند.
        
        if self.board[x][y] == 'S':
            self.board[x][y] = 'H'
            print("🎯 Hit! You get another turn!")
            return True  
        
        elif self.board[x][y] == 'w':
            self.board[x][y] = 'M'
            print("❌ Miss! Next player's turn.")
            return False
        
        else:
            print("⚠️ Already shot here! Try again.")
            return None  # دوباره باید مختصات وارد شود.


class Game:
    def __init__(self):
        self.player1_board = Board()
        self.player2_board = Board()
        self.current_player = 1  

    def print_boards(self):
        """نمایش برد بازیکن فعال و نمایش محدود شده از برد حریف"""
        if self.current_player == 1:
            print("🔵 Player 1's Board:")
            self.player1_board.print_board()
            print("🔴 Player 2's Board (Hidden):")
            self.player2_board.print_board(is_enemy=True)
        else:
            print("🔴 Player 2's Board:")
            self.player2_board.print_board()
            print("🔵 Player 1's Board (Hidden):")
            self.player1_board.print_board(is_enemy=True)

    def switch_turn(self):
        """تغییر نوبت بازیکنان"""
        self.current_player = 2 if self.current_player == 1 else 1

    def play_turn(self):
        """مدیریت یک نوبت بازی"""
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

                    if result is not None:  # اگر None نباشد، یعنی مقدار صحیح وارد شده
                        break

                except ValueError:
                    print("⚠️ Invalid input! Please enter numbers.")

            if not result:  # اگر `False` باشد، یعنی نوبت عوض شود
                self.switch_turn()
                break

    def start_game(self):
        """اجرای بازی"""
        print("🎮 Battleship Game Started!")
        while True:
            self.play_turn()


# --- اجرای بازی ---
game = Game()
game.player1_board.ship_installation(3, 'h', (2, 3))  
game.player1_board.ship_installation(2, 'v', (0, 7))
game.player2_board.ship_installation(3, 'v', (1, 2))  
game.player2_board.ship_installation(2, 'h', (4, 5))

game.start_game()
