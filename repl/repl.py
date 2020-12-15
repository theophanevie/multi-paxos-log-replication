import logging
import time

from mpi4py import MPI

from utils import MSG_TYPE, SPEED

comm = MPI.COMM_WORLD


def display_metainfo(servers: int, clients: int, nbmsg: int):
    print("Multi Paxos log")
    print()
    print("mpi rank")
    print("repl: 0")
    srv = "servers:"
    for i in range(1, servers + 1):
        srv += " " + str(i)
    print(srv)
    clt = "clients:"
    for i in range(servers + 1, servers + clients + 1):
        clt += " " + str(i)
    print(clt)
    print()
    print(f"number of messages: {nbmsg}")
    print()


def display_command():
    print()
    print("Avalaible command:")
    print("START : Clients  will start to send their messages to random servers")
    print("EXIT : Exit the repl")
    print("SPEED <server> <LOW|MEDIUM|HIGH> : Change tick duration for a server")
    print("CRASH <server> : Server will respond only to repl")
    print(
        "RECOVERY <server> : Server will start again to answer message from other servers"
    )
    print()


def run(rank: int, servers: int, clients: int, nbmsg: int, cmds=[]):
    """
    REPL execution

    rank : int
    mpi rank
    servers : int
    number of server
    clients : int
    number of client
    nbmsg : int
    number of message
    cmds : [str]
    command for repl from configuration file
    """

    logging.debug(f"Repl {rank} start")

    display_metainfo(servers, clients, nbmsg)

    display_command()

    while True:

        # to catch parsing error due to user manipulation
        try:

            # get command from configfile
            if len(cmds) != 0:
                myinput = cmds[0].split()
                del cmds[0]
                print(">>>Get command from config file")
            else:
                myinput = input(">>>").split()
                if len(myinput) == 0:
                    pass

            # command SPEED
            if myinput[0] == "SPEED":
                print(
                    f"Server {myinput[1]} has now a tick of {SPEED[myinput[2]].value} seconds"
                )

                msg = {"SPEED": myinput[2]}
                logging.debug(f"Repl has sent a {msg} to {int(myinput[1])}")
                comm.send(msg, dest=int(myinput[1]), tag=MSG_TYPE["REPL"].value)

            # command START
            elif myinput[0] == "START":
                print("Clients start to send their messages to random servers")

                for i in range(clients):
                    logging.debug(f"Repl has sent a START to {servers + 1 + i}")
                    comm.send({}, dest=servers + 1 + i, tag=MSG_TYPE["REPL"].value)

            # command CRASh
            elif myinput[0] == "CRASH":
                print(f"Server {myinput[1]} has now crashed")

                msg = {"CRASH": True}
                logging.debug(f"Repl has sent a {msg} to {int(myinput[1]) + 1}")
                comm.send(msg, dest=int(myinput[1]) + 1, tag=MSG_TYPE["REPL"].value)

            # command RECOVERY
            elif myinput[0] == "RECOVERY":
                print(f"Server {myinput[1]} has recovered")

                msg = {"RECOVERY": True}
                logging.debug(f"Repl has sent a {msg} to {int(myinput[1]) + 1}")
                comm.send(msg, dest=int(myinput[1]) + 1, tag=MSG_TYPE["REPL"].value)

            # command EXIT
            elif myinput[0] == "EXIT":
                print(f"Repl has exit")
                return

            # wrong command, display available command
            else:
                display_command()

        # wrong command, display available command
        except:
            print("Invalid command/format")
            display_command()

    logging.debug(f"Repl {rank} end")
