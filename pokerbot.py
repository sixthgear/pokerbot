from pb import game

if __name__ == '__main__':
    import sys
    import random
    
    if len(sys.argv) > 1:
        seed = int(sys.argv[-1])
    else:    
        seed = random.getrandbits(16)
        
    random.seed(seed)
    print 'seed %d' % seed
    
    game = game.Game()        
    game_loop = game.play()    
    game_loop.send(None)
    while True:
        cmd = raw_input()
        game.parse(cmd)
        game_loop.send(cmd)
        
    
