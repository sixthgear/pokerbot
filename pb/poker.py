# coding: utf-8
"""
poker.py by sixthgear.

A set of handy functions and utilities to implement poker games and calculators.
LICENSE: buy me a beer sometime.
"""

import itertools
import random
import collections

def deck():
    """
    A simple deck generator used to deal from a single deck of 52 cards.
    If the end of the deck is reached, a StopIteration exception will be thrown.
        
    # create the generator
    >>> d = deck() 
    
    # deal one card
    >>> d.next() 
    Card(value=6, suit=3)
     
    # deal a hand of 5 cards
    >>> hand_output([d.next() for card in range(5)])
    [Q♡] [3♡] [8♢] [9♢] [6♡]
    
    # deal a hand of 5 cards
    >>> hand = [card for i, card in zip(d, range(5))] 
    [Q♡] [3♡] [8♢] [9♢] [6♡]    
    """    
    cards = [Card(i,j) for j in range(4) for i in range(1,14)]
    random.shuffle(cards)
    for c in cards:
        yield c

Card = collections.namedtuple('Card', 'value suit')
Hand = collections.namedtuple('Hand', 'rank cards desc')
Symbol = collections.namedtuple('Symbol', 'symbol name')

VALUES = [
    Symbol('A', 'low ace'),
    Symbol('2', 'duece'),
    Symbol('3', 'three'),
    Symbol('4', 'four'),
    Symbol('5', 'five'),
    Symbol('6', 'six'),
    Symbol('7', 'seven'),
    Symbol('8', 'eight'),
    Symbol('9', 'nine'),
    Symbol('T', 'ten'),
    Symbol('J', 'jack'),
    Symbol('Q', 'queen'),
    Symbol('K', 'king'),
    Symbol('A', 'ace'),
]

SUITS = [
    Symbol(u'♡', 'hearts'),
    Symbol(u'♢', 'diamonds'),
    Symbol(u'♣', 'clubs'),
    Symbol(u'♠', 'spades'),
]

HANDS = [
    (0x100000, 'royal flush'),
    (0x200000, 'straight flush'),
    (0x300000, 'quad %s'),
    (0x400000, 'full house - %s full of %s'),
    (0x500000, 'flush - %s'),
    (0x600000, 'straight - %s high'),
    (0x700000, 'trip %s'),
    (0x800000, 'two pair - %s and %s'),
    (0x900000, 'pair of %s'),
    (0xA00000, '%s high'),
]

def card_value_name(card, plural=True): 
    name = VALUES[card.value].name
    if not plural: 
        return name
    if card_value_sym(card) == '6': 
        return name + 'es'
    return name + 's'
        
def card_suit_name(card): return SUITS[card.suit].name
def card_value_sym(card): return VALUES[card.value].symbol
def card_suit_sym(card): return SUITS[card.suit].symbol
def card_output(card): return '[' + card_value_sym(card) + card_suit_sym(card) + ']'
def hand_output(hand, total=0):
    cards = map(card_output, hand)
    if len(cards) < total:
        cards += ['[  ]'] * (total-len(cards))
    return str.join(' ', cards)
    
def card_from_str(str):
    """
    Creates a card from a string like "Ah" or "5c"
    """
    value = [i+1 for i, v in enumerate(VALUES[1:]) if str[0].upper() == v[0]]
    suit = [i for i, s in enumerate(SUITS) if str[1].lower() == s[1][0]]
    if value and suit:
        return Card(value[0], suit[0])
    else:
        return None

        
def chk_straight(cards):
    """
    check a list of cards for straight sequences.
    """
    # might be redundant, but left for safety.
    cards.sort(key=lambda c: c.value, reverse=True)
    
    # add low aces for straights
    for c in [c for c in cards if c.value == 13]:
        low = Card(0, c.suit)
        cards.append(low)
        
    # straight detection variables
    straight_counter = 1
    straight = []    
    last = cards[0].value
    
    for c in cards:        
        delta = last - c.value
        last = c.value
        if delta == 0:
            straight.append(c)
        elif delta == 1:
            straight_counter += 1
            straight.append(c)
        elif delta > 1 and straight_counter < 5:
            straight_counter = 1
            straight = [c]
    
    if straight_counter >= 5:
        return straight 
    else:
        return []
    
    
def hand_build(cards):
    """
    Find the best possible poker hand from a list of cards and return it along
    with a rank and description. Returns a named tuple called Hand with the
    following properties:
    
    cards:  a list of the 5 cards that compose the best possible poker hand.
    rank:   an integer that can be used to sort or compare any hand returned by
            this function.
    desc:   a plain-language description of the hand. 
            Eg. "full house - threes full of aces"
        
    HAND SELECTION
    
    The hand is built by following a number of steps.
    
    1.  sort the cards in reverse rank order. (A high, 2 low).
    
    2.  build a dict of groupings of either rank or suit.
    
    3.  find rank groupings of 2 or more cards. These represent pairs, sets and 
        quads.
        
    4.  find suit groupings of 5 or more cards. There should realistically only
        be one of these if a 7 card (hold 'em) hand is passed in, but it may
        be larger than five cards. This represents a flush.
        
    5.  run a straight check algorithm. the chk_straight function takes a list
        of cards and iterates through them checking if the difference in value
        between any two cards is 1 or 0. If a decending sequence of 5 or more is
        found, it is returned (along with any pairs that might exist within that
        sequence, since we don't yet know if a straight flush is possible).
        
    6.  if there is both a straight AND a flush, rerun chk_straight on the flush
        cards to see if the two groups intersect. If so, we have a straight 
        flush (or royal if the high card is an ace.) If this intersection
        suceeds, there should be no more rank duplicates (since the flush check 
        would have removed any pairs that don't match suit).
        
    7.  Now we that all tests have been run, we just go through the list
        of possible hands from high to low, and inesert the required amount
        of cards that we need into the final hand that we need.
        
    8.  Now if our hand is less than 5 cards longs, we loop through the original
        (sorted) list of cards and insert them into the hand as kickers (if they
        aren't already being used in the hand). This assures the best possible 
        5-card hand is created with the highest kickers available.
        
    9.  Finally, we can run our rank calculation.
            
    RANK CALCULATION
    
    The rank is calculated by packing 6 integers into a 6-digit hexadecimal int.
    the most significant digit represents the rank of the hand, with royal flush 
    being 1 (0x100000), and high pair being 10 (0xA00000). 
    
    The remiainging 5 digits represent the number values (1 to 13) of each card 
    in the hand. For this to give an accurate ranking, the hand MUST be sorted 
    by card significance (use of a card to make up a hand) and then by card 
    value. In other words, the cards that make up the hand always come before any
    kickers. So a two-pair hand with aces and fives, along with a 9 kicker would
    be sorted AA559. That hand would rank 0x800884. 
    """
    
    # this wont work without at least five
    assert len(cards) >= 5
    
    # this is what we'll build for output, should be 5 cards
    hand = []    
    # order high to low to find patterns easier
    cards.sort(key=lambda c: c.value, reverse=True)
    
    # dicts for groupings (sets, flushes)
    vgroups = collections.defaultdict(list)
    sgroups = collections.defaultdict(list)    
        
    for c in cards:
        # build a hashmap of value groups and suit groups
        vgroups[c.value].append(c)        
        sgroups[c.suit].append(c)                

    # sort this so we grab the highest groups first. OrderDicts would make this
    # nicer. TODO: switch to 2.7.
    vgroup_values = sorted(vgroups.values(), key=lambda g: g[0].value, reverse=True)    
    # calculate groupings    
    pairs = [g for g in vgroup_values if len(g) == 2]
    trips = [g for g in vgroup_values if len(g) == 3]
    quads = [g for g in vgroup_values if len(g) == 4]
    flush = [g for g in sgroups.values() if len(g) >= 5]
    full_house = trips and pairs
    two_pair = len(pairs) >= 2            
    # check for straights
    straight = chk_straight(cards)
    straight_flush = []
    royal_flush = []
            
    # straight flush detection by taking an intersection between the set of flush
    # cards and the set of straight cards. Any resultant set >= 5 cards is our 
    # straight flush.
    if straight and flush:        
        # intersection = list(set(straight) & set(flush[0]))
        straight_flush = chk_straight(flush[0]) # intersection
    
    # royal flush detection
    if straight_flush and straight_flush[0].value == 13:
        royal_flush = straight_flush
    
    # finally return each hand if it exists    
    if royal_flush:
        hand += royal_flush[:5]
        rank, desc = HANDS[0]
        
    elif straight_flush:
        hand += straight_flush[:5]
        rank, desc = HANDS[1]
        
    elif quads:        
        hand += quads[0]
        rank, desc = HANDS[2][0], HANDS[2][1] % card_value_name(quads[0][0])
        
    elif full_house:
        hand += trips[0] + pairs[0]
        rank, desc = HANDS[3][0], HANDS[3][1] % \
            (card_value_name(trips[0][0]), card_value_name(pairs[0][0]))
            
    elif flush:
        hand += flush[0][:5]
        rank, desc = HANDS[4][0], HANDS[4][1] % card_suit_name(flush[0][0])
        
    elif straight:
        for i, c in enumerate(straight):
            if i == 0 or c.value != straight[i-1].value:
                hand.append(c)
            if len(hand) == 5: 
                break            
        rank, desc = HANDS[5][0], HANDS[5][1] % card_value_name(straight[0], False)
            
    elif trips:
        hand += trips[0]
        rank, desc = HANDS[6][0], HANDS[6][1] % card_value_name(trips[0][0])
        
    elif two_pair:
        hand += pairs[0] + pairs[1]
        rank, desc = HANDS[7][0], HANDS[7][1] % \
            (card_value_name(pairs[0][0]),card_value_name(pairs[1][0]))
            
    elif pairs:
        hand += pairs[0]
        rank, desc = HANDS[8][0], HANDS[8][1] % card_value_name(pairs[0][0])
        
    else:    
        hand += hand[:5]
        rank, desc = HANDS[9][0], HANDS[9][1] % card_value_name(cards[0], False)
        
    # add highcards to the end to make five.    
    while len(hand) < 5:
        card = cards.pop(0)
        if card not in hand:             
            hand.append(card)            
    
    # calculate rank for each card
    for i, c in enumerate(hand):
        rank |= (13 - c.value) << (4 * (4-i))
        
    return Hand(rank, hand, desc)
    
    
    
def hand_build_omaha(hole, board):
    """
    Analyze and rank a 9-card OMAHA hand. Omaha hands have the tricky requirement
    that they be built using EXACTLY two of the four hole cards, and three of
    the community cards from the board.
    
    Given this requirement, to support omaha hands, we wrap our hand_build 
    function with one that creates all 60 possible 5-card hands from a list of 
    holecards and board cards. (6 possible combinations of hole cards x 10
    possible combinations of board cards)
    
    Each 5-card hand is then fed through the ranker, and then the best one is 
    selected and returned.
    """    
    
    assert len(hole) == 4
    assert len(board) == 5
    
    best = Hand([], 0xFFFFFF, '')
    
    # 6 combinations of hole cards
    hole_hands = [list(c) for c in itertools.combinations(hole, 2)]     
    # 10 combinations of house cards
    board_hands = [list(c) for c in itertools.combinations(board, 3)] 
    # and total possible hands is the product of both sets
    hands = (hand_build(a+b) for a, b in itertools.product(hole_hands, board_hands))
    
    # test each hand, find the lowest rank.
    for h in hands:
        if h.rank < best.rank: best = h
    
    # done.
    return best


if __name__ == '__main__':

    """
    A simple example that creates 9 texas hold 'em hands and 9 omaha hands
    and ranks them.
    """

    player = collections.namedtuple('player', 'cards hand')

    d = deck()
    players = [[[d.next(), d.next()], None] for p in range(9)]
    board = [d.next() for c in range(5)]    
    for p in players: 
        p[1] = hand_build(p[0] + board)
    
    print
    print 'HOLD EM HANDS:'
    print 'BOARD ' + hand_output(board)
    print '---'  
    
    for i,p in enumerate(sorted(players, key=lambda p: p[1].rank)):
        hand = p[1]
        print 'PLR %d %s                   %s (%s) "%s"' % \
            (i+1, hand_output(p[0]), hand_output(hand.cards), hex(hand.rank), hand.desc)
    
    d = deck()
    players = [[[d.next(), d.next(), d.next(), d.next()], None] for p in range(9)]
    board = [d.next() for c in range(5)]    
    for p in players: p[1] = hand_build_omaha(p[0], board)
    
    print
    print 'OMAHA HANDS:'
    print 'BOARD ' + hand_output(board)
    print '---'  
    
    for i,p in enumerate(sorted(players, key=lambda p: p[1].rank)):
        hand = p[1]
        print 'PLR %d %s         %s (%s) "%s"' % \
            (i+1, hand_output(p[0]), hand_output(hand.cards), hex(hand.rank), hand.desc)
    