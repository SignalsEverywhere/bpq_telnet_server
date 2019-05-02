import logging
import configparser
from miniboa import TelnetServer
from plugins import callsign as call

IDLE_TIMEOUT = 300
CLIENT_LIST = []
SERVER_RUN = True

config = configparser.RawConfigParser()

config.read('conf.txt')
NODE_CALLSIGN = config.get('MAIN', 'NODE_CALLSIGN')

if NODE_CALLSIGN == 'CHANGEME':
    print('ERROR: Change the callsign')
    input('To continue anyway press enter -- DEV USE ONLY')
    pass


menu_data = [['\n(1) Call "wb5od"', '(2) Weather "Zip"', '(3) Tweet "to" "message"'], ['\n(4) Development', '(5) Random thing', '(6) Getting tired'],
                ['\n(7) Testing', '(8) Sysop Menu', '(9) List Users']]


#
## Setup functions that an amateur operator may want like... aprs messaging, etc.
#


def on_connect(client):
    """
    Sample on_connect function.
    Handles new connections.
    """
    logging.info("Opened connection to {}".format(client.addrport()))
    #broadcast("{} joins the conversation.\n".format(client.addrport()))
    CLIENT_LIST.append(client)
    client.send("\r\nWelcome to the " + NODE_CALLSIGN + " python telnet server for ham radio packet.\n")

    col_width = max(len(word) for row in menu_data for word in row) + 2  # padding
    for row in menu_data:
        client.send("".join(word.ljust(col_width) for word in row))
    client.send("\n\rIf you need to see this again just type in 'menu'")


def on_disconnect(client):
    """
    Sample on_disconnect function.
    Handles lost connections.
    """
    logging.info("Lost connection to {}".format(client.addrport()))
    CLIENT_LIST.remove(client)
    #broadcast("{} leaves the conversation.\n".format(client.addrport()))


def kick_idle():
    """
    Looks for idle clients and disconnects them by setting active to False.
    """
    # Who hasn't been typing?
    for client in CLIENT_LIST:
        if client.idle() > IDLE_TIMEOUT:
            logging.info("Kicking idle lobby client from {}".format(client.addrport()))
            client.active = False


def process_clients():
    """
    Check each client, if client.cmd_ready == True then there is a line of
    input available via client.get_command().
    """
    for client in CLIENT_LIST:
        if client.active and client.cmd_ready:
            # If the client sends input echo it to the chat room
            commands(client)


def broadcast(msg):
    """
    Send msg to every client.
    """
    for client in CLIENT_LIST:
        client.send(msg)


def commands(client):
    """
    Echo whatever client types to everyone.
    """
    global SERVER_RUN
    msg = client.get_command()
    logging.info("{} says '{}'".format(client.addrport(), msg))

#    for guest in CLIENT_LIST:
#        if guest != client:
#            guest.send("{} says '{}'\n".format(client.addrport(), msg))
#        else:
#            guest.send("You say '{}'\n".format(msg))

    cmd = msg.lower()
    # bye = disconnect
    if cmd == 'bye':
        client.active = False
    # shutdown == stop the server
    elif cmd == 'hello':
        client.send('Hello you could make this do anything. type bye to leave')
    elif cmd.startswith('call'):
        try:
            split = cmd.split(' ')
            client.send(call.callsign_start(split[1]))
        except:
            client.send('\r\nError')
    elif cmd == 'menu':
        col_width = max(len(word) for row in menu_data for word in row) + 2  # padding
        for row in menu_data:
            client.send("".join(word.ljust(col_width) for word in row))
    elif cmd == 'shutdown':
        SERVER_RUN = False


if __name__ == '__main__':

    # Simple chat server to demonstrate connection handling via the
    # async and telnet modules.

    logging.basicConfig(level=logging.DEBUG)

    # Create a telnet server with a port, address,
    # a function to call with new connections
    # and one to call with lost connections.

    telnet_server = TelnetServer(
        port=4444,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .05
        )

    logging.info("Listening for connections on port {}. CTRL-C to break.".format(telnet_server.port))

    # Server Loop
    while SERVER_RUN:
        telnet_server.poll()        # Send, Recv, and look for new connections
        kick_idle()                 # Check for idle clients
        process_clients()           # Check for client input

    logging.info("Server shutdown.")