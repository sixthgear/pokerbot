class Player(object):
    
    def __init__(self, name):
        self.name = name
        self.cards = []
        self.hand = None
        self.status = 0
        self.stack = 1000
        self.current_bet = 0
        self.button = ''