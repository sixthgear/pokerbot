import sys
import socket
import string

HOST = 'irc.freenode.net'
PORT = 6667
NICK = 'pokerbot'
IDENT = ''
MODE = 0
REALNAME = 'pokerbot'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
s.setblocking(0)

def connect(address, port):
    """
    """
    s.connect((address, port))

def select():
    """
    """
    # non-blocking select
    in_set, _, _ = select.select([s], [s], [], 0)

    if in_set:
        recv_buffer = ''
        recv_buffer = s.recv(1024)

        if len(recv_buffer) > 0:
            read(recv_buffer)
        else:
            # closed connection
            s.close()
            continue


def write(data):
    """
    send a raw command to irc server.
    """
    s.send(data + '\r\n')

def read(data):

    for line in data.split('\n'):
        line = line.rstrip()
        tokens = line.split()

        # automatically reply to PING
        if(tokens[0] == 'PING'):
            write('PONG %s' % tokens[1])
        else:
            yield line

def identify():
    write('NICK %s' % NICK)
    write('USER %s %d * :%s' % (IDENT, MODE, REALNAME))

