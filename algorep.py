#!/usr/bin/env python3

import logging

import click
import yaml
from mpi4py import MPI

import client
import repl
import server


@click.group()
def cli():
    pass


@cli.command("run")
@click.argument("configfile", type=click.Path(exists=True))
def run(configfile: str):
    """
    Main function

    configfile : str
    Path to configuration file
    """
    config = yaml.safe_load(open(configfile, "r"))
    clients = len(config["clients"])
    servers = config["servers"]

    # reset logfile
    with open("global.log", "w") as _:
        pass

    # start logger
    logging.basicConfig(filename="global.log", level=logging.DEBUG)

    comm = MPI.COMM_WORLD

    nbmsg = 0
    for c in config["clients"]:
        nbmsg += len(c["msg"])

    rank = comm.Get_rank()

    replmsg = []
    if "repl" in config:
        replmsg = config["repl"]

    # init repl
    if rank == 0:
        repl.run(rank, servers, clients, nbmsg, replmsg)

    # init server
    elif rank < servers + 1:
        server.run(rank, servers, clients, nbmsg)

    # init client
    else:
        client.run(rank, servers, config["clients"][rank - 1 - servers]["msg"], clients)


if __name__ == "__main__":
    cli()
