import datetime
import logging
import math
import time

from mpi4py import MPI

from utils import MSG_TYPE, SPEED

comm = MPI.COMM_WORLD


class paxos_server:
    """
    server class
    """

    def __init__(self, rank: int, nbservers: int):
        self.rank = rank
        self.nbservers = nbservers
        self.na = datetime.datetime.now()
        self.np = datetime.datetime.now()
        self.nc = datetime.datetime.now()
        self.init = datetime.datetime.now()
        self.logfile = open(f"{rank}.log", "w")
        self.va = []
        self.vc = []
        self.seq = []
        self.client = -1
        self.speed = 1
        self.denied = 0
        self.disable = False
        self.logpos = 0
        self.timeout = 0

    def send_denied(self):
        """
        send a message to current client ask him to re send later
        """
        self.denied = 0
        self.timeout = 0
        msg = {"code": 503}
        comm.send(msg, dest=self.client, tag=MSG_TYPE.CLIENT.value)
        self.nc = self.init
        self.client = -1

    def tick(self):
        """
        wait between each action, determined by speed
        check if timedout
        """
        if self.timeout > 0 and not self.disable:
            self.timeout -= 1
            if self.timeout == 0:
                logging.debug(f"Serveur {self.rank} has TIMED OUT")
                self.send_denied()

        time.sleep(self.speed)

    def flush_sequence(self):
        """
        write in log current sequence and increase log position
        """
        logging.debug(f"Serveur {self.rank} flush")
        for value in self.seq:
            logging.debug(f"Serveur {self.rank} WRITE IN LOG {value} pos {self.logpos}")
            self.logfile.write(f"{value}\n")
            self.logfile.flush()
            self.logpos += 1
        self.seq = []

    def receive_denied(self, status):
        """
        handle when a server respond to a request by saying he is not avaible
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(
            f"Serveur {self.rank} has an DENIED for {self.client} from {status.source}"
        )

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        if self.client == -1:
            logging.debug(
                f"Serveur {self.rank} has already DENIED for {self.client} from {status.source}"
            )
            return

        self.denied += 1

        # if majority abort current round
        if self.denied >= math.ceil((self.nbservers + 1) / 2):
            self.send_denied()

    def receive_info(self, status):
        """
        receive a message from a client
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has an INFO {data}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # if already handling another client request
        if self.client != -1:
            logging.debug(
                f"Serveur {self.rank} has an DENIED for {status.source} from {self.rank}"
            )

            msg = {"code": 503}
            comm.send(msg, dest=status.source, tag=MSG_TYPE.CLIENT.value)
            return

        self.client = status.source
        self.value = data["value"]
        self.timeout = 4 * self.nbservers + 12
        self.nc = datetime.datetime.now()
        msg = {"nc": self.nc}

        # send prepare to all server
        for i in range(self.nbservers):
            comm.send(msg, dest=i + 1, tag=MSG_TYPE.PREPARE.value)

        self.curpromise = []
        self.denied = 0

    def receive_prepare(self, status):
        """
        receive prepare request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has a PREPARE {data}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # check msg id, if inferior respond denied, otherwise respong promise
        if self.np < data["nc"]:
            self.np = data["nc"]
            msg = {"na": self.na, "nc": self.np, "va": self.va, "logpos": self.logpos}
            comm.send(msg, dest=status.source, tag=MSG_TYPE.PROMISE.value)
        else:
            comm.send({}, dest=status.source, tag=MSG_TYPE.DENIED.value)

    def receive_promise(self, status):
        """
        receive promise request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has an PROMISE {data}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # check id
        if data["nc"] != self.nc:
            return

        # check log position
        if data["logpos"] < self.logpos:
            self.send_log(status.source, data["logpos"])
        else:
            self.curpromise.append((data["va"], data["na"], data["logpos"]))

        # check majority
        if len(self.curpromise) >= math.ceil((self.nbservers + 1) / 2):
            tmp = max(self.curpromise, key=lambda x: x[1])

            # if late abort current round and ask for log
            if data["logpos"] > self.logpos:
                msg = {"logpos": self.logpos}
                logging.debug(f"Serveur {self.rank} ASK FOR LOG")
                for i in range(self.nbservers):
                    comm.send(msg, dest=i + 1, tag=MSG_TYPE.ASKFORLOG.value)

                self.curpromise = []
                self.send_denied()
                return

            self.vc = self.value

            msg = {"nc": self.nc, "vc": self.vc}

            # send accept to all servers
            for i in range(self.nbservers):
                comm.send(msg, dest=i + 1, tag=MSG_TYPE.ACCEPT.value)

            self.curpromise = []
            self.denied = 0
            self.ack = 0

    def receive_accept(self, status):
        """
        receive accept request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has an ACCEPT {data}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # check id, if inferior respond denied otherwise respond accepted
        if self.np <= data["nc"]:

            # update only if server is the not sender and receiver
            if status.source != self.rank:
                self.va = data["vc"]
                self.na = data["nc"]
                self.np = data["nc"]

            msg = {"nc": data["nc"]}
            comm.send(msg, dest=status.source, tag=MSG_TYPE.ACCEPTED.value)
        else:
            comm.send({}, dest=status.source, tag=MSG_TYPE.DENIED.value)

    def receive_accepted(self, status):
        """
        receive accepted request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        logging.debug(f"Serveur {self.rank} has an ACCEPTED {data}")

        if data["nc"] != self.nc:
            logging.debug(f"Serveur {self.rank} has an INVALID ACCEPTED {data}")
            return

        self.ack += 1

        # check majority
        if self.ack >= math.ceil((self.nbservers + 1) / 2):

            # updateif server is the sender and receiver
            self.va = self.vc
            self.na = self.nc
            self.np = self.nc

            # send decide to all servers
            msg = {"vc": self.vc, "logpos": self.logpos}
            for i in range(self.nbservers):
                comm.send(msg, dest=i + 1, tag=MSG_TYPE.DECIDE.value)

            self.ack = 0
            self.timeout = 0

            # send confirmation to client
            msg = {"code": 200}
            comm.send(msg, dest=self.client, tag=MSG_TYPE.CLIENT.value)
            logging.debug(f"Serveur {self.rank} has send CONFIRMATION to {self.client}")
            self.client = -1
            self.denied = 0

    def receive_decide(self, status):
        """
        receive decide request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has an DECIDE {data}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # check log position
        if data["logpos"] != self.logpos:
            logging.debug(f"Serveur {self.rank} has an INVALID DECIDE {data}")
            comm.send({}, dest=status.source, tag=MSG_TYPE.DENIED.value)
            return

        self.seq = []
        self.seq.append(data["vc"])

        # write in log current values
        self.flush_sequence()

    def receive_repl(self, status):
        """
        receive repl request
        """
        data = comm.recv(source=status.source, tag=status.tag)

        logging.debug(f"Serveur {self.rank} has an REPL {data}")

        # adapt speed
        if "SPEED" in data:
            self.speed = SPEED[data["SPEED"]].value

        # stop sending or receving messages
        elif "CRASH" in data:
            self.disable = True

        # start again sending or receving messages
        elif "RECOVERY" in data:
            self.disable = False
            self.timeout = 0
            self.nc = self.init
            self.client = -1

    def send_log(self, dest, logpos):
        """
        compile missing log for a server and send them to it
        """
        log = []

        # compile missing log
        with open(f"{self.rank}.log", "r") as logfile:
            for i, line in enumerate(logfile):
                if i >= logpos:
                    log.append(line.rstrip())

        # send missing log
        msg = {"logpos": self.logpos, "log": log}
        logging.debug(f"Serveur {self.rank} SEND LOG")
        comm.send(msg, dest=dest, tag=MSG_TYPE.MISSINGLOG.value)

    def receive_missinglog(self, status):
        """
        receive missing log from other server
        """
        data = comm.recv(source=status.source, tag=status.tag)
        logging.debug(f"Serveur {self.rank} RECEIVE MISSING LOG {data['log']}")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # append missing log to current value and then write them in log
        self.seq = []
        for i in range(data["logpos"] - self.logpos, 0, -1):
            self.seq.append(data["log"][len(data["log"]) - i])
        self.flush_sequence()

    def receive_askforlog(self, status):
        """
        receive ask for log
        """
        data = comm.recv(source=status.source, tag=status.tag)
        logging.debug(f"Serveur {self.rank} RECEIVE ASK FOR LOG")

        if self.disable:
            logging.debug(f"Serveur {self.rank} is DEAD")
            return

        # send missing log to asking server
        self.send_log(status.source, data["logpos"])


def run(rank: int, servers: int, clients: int, ngtotalmsg: int):
    """
    SERVER execution

    rank : int
    mpi rank
    servers : int
    number of server
    clients : int
    number of client
    ngtotalmsg : int
    number of message
    """

    logging.debug(f"Serveur {rank} init")

    s = paxos_server(rank, servers)

    # while server do not get all messages in its log
    while s.logpos != ngtotalmsg:

        status = MPI.Status()

        # check if incomming message
        rec = comm.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG, status=status)

        # if one call the right function to handle it
        if rec:
            if status.tag == MSG_TYPE.CLIENT.value:
                s.receive_info(status)
            elif status.tag == MSG_TYPE.PREPARE.value:
                s.receive_prepare(status)
            elif status.tag == MSG_TYPE.PROMISE.value:
                s.receive_promise(status)
            elif status.tag == MSG_TYPE.ACCEPT.value:
                s.receive_accept(status)
            elif status.tag == MSG_TYPE.ACCEPTED.value:
                s.receive_accepted(status)
            elif status.tag == MSG_TYPE.DECIDE.value:
                s.receive_decide(status)
            elif status.tag == MSG_TYPE.DENIED.value:
                s.receive_denied(status)
            elif status.tag == MSG_TYPE.REPL.value:
                s.receive_repl(status)
            elif status.tag == MSG_TYPE.ASKFORLOG.value:
                s.receive_askforlog(status)
            elif status.tag == MSG_TYPE.MISSINGLOG.value:
                s.receive_missinglog(status)

        # wait and check for timedout
        s.tick()

    logging.debug(f"Serveur {rank} end")
