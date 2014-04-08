from datetime import datetime
import time
import itertools
import player
import poker

class txt(object):
    """
    strings used in the game.
    """
    buttons = 'SB BB UG CO D'
    rule = '-----------------------------------------------------------'
    topic = 'NLHE %d/%d | Hand %d %s | %d/%d players ("sit" to play)'
    dealing = 'dealing %s to %s ($%d)'
    inhand = 'in-hand %s %s ($%d)'
    showing ='showing %s "%s" for %s'
    draw = '%s %s -- POT $%d'
    winner = 'WINNER %s %s ($%d)'
    next = 'NEXT HAND starts in %d seconds.'
    action_a = 'POT $%d. Action on %s ($%d).'
    action_b = 'POT $%d. Action on %s ($%d) +%d to call.'
    at_risk = '-- %s at-risk.'
    sits = '%s sits at the table.'
    stands = '%s leaves the table.'
    posts_small = '%s posts small blind (%d).'
    posts_big = '%s posts big blind (%d).'
    posts_ante = '%s posts ante (%d).'
    calls = '%s calls for %d.'
    raises = '%s raises to %d.'
    raises_all = '%s raises all-in to %d.'
    checks = '%s checks.'
    folds = '%s folds.'
    busted = '%s has busted.'
    rebuys = '%s rebuys for %d.'

POSITIONS = {
    -1: 'CO', # cut-off
    0: 'D',   # dealer
    1: 'SB',  # small blind
    2: 'BB',  # big blind
    3: 'UG',  # under the gun
}

NAMES = [
    'sixthgear',
    'mjard',
    'synx',
    'thoughtpolice',
    'BaconJuice'
]

class Game(object):

    def __init__(self, players=5):

        self.hand_num = 0
        self.sb = 15
        self.bb = 30
        self.ante = 0
        self.max_players = 9
        self.players = [player.Player(NAMES[p]) for p in range(players)]
        self.rounds = [
            ('PREFLOP', 0),
            ('FLOP', 3),
            ('TURN', 1),
            ('RIVER', 1),
        ]

    def parse(self, cmd):
        """
        parse a client command
        """
        pass

    def out(self, msg):
        """
        output a game action
        """
        print '[%02d:%02d] * pbt >> ' % (datetime.now().hour, datetime.now().minute) + msg

    def draw(self, round):
        """
        draw n cards and add them to the board.
        """
        self.board += [self.deck.next() for i in range(round[1])]
        for p in self.players:
            self.out(txt.inhand % (poker.hand_output(p.cards), p.name, p.stack))
        self.out('')
        self.out(txt.draw % (round[0], poker.hand_output(self.board, 5), self.pot))
        self.out('')

    def bet(self, player, amt):
        """
        bet some monies
        """
        player.stack -= amt
        player.current_bet += amt
        self.current_bet = max(self.current_bet, amt)
        self.pot += amt

    def deal(self):
        """
        deal the hand.
        """
        for p in self.players:
            p.cards = [self.deck.next(), self.deck.next()]
            p.cards.sort(key=lambda c: c.value, reverse=True)
            self.out(txt.dealing % (poker.hand_output(p.cards), p.name, p.stack))

    def showdown(self):
        """
        showdown
        TODO: side pots for allin players
        """
        #
        # build hands
        for p in self.players:
            p.hand = poker.hand_build(p.cards + self.board)

        ranked = sorted(self.players, key=lambda p: p.hand.rank)
        winners = [p for p in ranked if p.hand.rank == ranked[0].hand.rank]
        split = self.pot / len(winners)

        self.out(txt.draw % ('SHOWDOWN', poker.hand_output(self.board, 5), self.pot))
        self.out('')
        for p in self.players:
            self.out(txt.showing % (poker.hand_output(p.cards), p.hand.desc, p.name))

        self.out('')

        for p in winners:
            p.stack += split
            self.out(txt.winner % (poker.hand_output(p.hand.cards), p.name, p.stack))

        self.out('')


    def allin(self):
        pass

    def valid(self, p, cmd):
        return True

    def play(self):
        """
        This coroutine represents a synchronous loop of game logic.
        The bot may need to perform other tasks while this is executing, so it
        will yield control whenever it is waiting for user action.
        """
        while True:

            self.hand_num += 1

            self.deck = poker.deck()
            self.board = []
            for p in self.players:
                p.hand = None
                p.cards = []
                p.current_bet = 0

            self.pot = 0
            self.current_bet = 0
            self.action = 0

            # assign buttons
            # assign action order

            # pre-deal
            self.out(txt.topic % (self.sb, self.bb, self.hand_num, poker.hand_output(self.board, 5), len(self.players), self.max_players))
            self.out(txt.rule)
            self.out(txt.posts_small % (self.players[0].name, self.sb))
            self.out(txt.posts_big % (self.players[1].name, self.bb))

            # post blinds
            self.bet(self.players[0], self.sb)
            self.bet(self.players[1], self.bb)

            # deal
            self.deal()

            # loop
            for r in self.rounds:
                # betting cycle
                if r[0] != 'PREFLOP':
                    self.draw(r)
                    self.out(txt.topic % (self.sb, self.bb, self.hand_num, poker.hand_output(self.board, 5), len(self.players), self.max_players))

                self.out(txt.rule)
                for p in self.players:
                    self.out(txt.action_b % (self.pot, p.name, p.stack, self.current_bet - p.current_bet))

                    # yield here
                    # resume when we have valid hand input to act upon.
                    while True:
                        cmd = yield
                        if self.valid(p, cmd): break

                    bet = self.current_bet - p.current_bet
                    self.bet(p, bet)
                    self.out(txt.calls % (p.name, bet))

                self.out(txt.rule)

            self.showdown()
            self.out(txt.next % 30)
            self.out(txt.rule)
            time.sleep(8)

    # for p in self.players:
    # cards = poker.hand_output(p.cards)
    # print 'BOARD ' + poker.hand_output(self.board)
    # p.hand = poker.hand_build(p.cards + self.board)
    # self.players.sort(key=lambda p: p.hand.rank)
