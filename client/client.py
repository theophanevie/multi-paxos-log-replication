import logging
import math
import time
from random import random

from mpi4py import MPI

from utils import MSG_TYPE

comm = MPI.COMM_WORLD


def run(rank: int, servers: int, msg, clients: int):
    """
    CLIENT execution

    rank : int
    mpi rank
    servers : int
    number of server
    clients : int
    number of clients
    msg : []
    list of message to send to servers
    """

    logging.debug(f"Client {rank} init")

    comm.recv(source=0, tag=MSG_TYPE["REPL"].value)

    logging.debug(f"Client {rank} start")

    for mymsg in msg:

        i = 0
        status = MPI.Status()

        # while we do not have confirmation from server
        while i == 0 or data["code"] != 200:
            time.sleep(i)
            t = 0

            # send message to random server
            msg = {"value": mymsg}
            my_server = int(round(random() * servers - 0.5)) + 1
            comm.send(msg, dest=my_server, tag=MSG_TYPE["CLIENT"].value)
            logging.debug(f"Client {rank} send {msg} to {my_server}")

            # look if the server send back something
            rec = comm.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG, status=status)

            # if nothing begin to wait until timeout
            while not rec:
                time.sleep(1)
                rec = comm.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG, status=status)
                t += 1

                # timed out, client resend message
                if t > 90:
                    t = 0
                    logging.debug(f"Client {rank} send TIMED OUT")
                    my_server = int(round(random() * servers - 0.5)) + 1
                    comm.send(msg, dest=my_server, tag=MSG_TYPE["CLIENT"].value)
                    logging.debug(f"Client {rank} send {msg} to {my_server}")

            # client get a response from the server
            data = comm.recv(source=status.source, tag=MSG_TYPE["CLIENT"].value)
            logging.debug(f"Client {rank} received {data['code']} from {my_server}")

            # increase time before resend if server was unavailable
            i = min(
                i + 8 + int((2 * clients * servers) * random()), servers * clients * 4
            )

    logging.debug(f"Client {rank} end")
