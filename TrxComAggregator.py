import serial
import json
import logging.config
import threading
import queue
from time import sleep

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
# logger = logging.getLogger(__name__)
# logger.setLevel(level=logging.DEBUG)

APP_VERSION = "1.1"

class Settings(object):

    def __init__(self, settings=None):

        if settings:
            file = settings
        else:
            file = "settings.cfg"

        with open(file) as json_file:
            self.app_settings = json.load(json_file)


    def get_vports_count(self):
        """

        :return:
        :rtype: int
        """
        return self.app_settings["vport_names"].__len__()


    def get_vports(self):
        """

        :return:
        :rtype: list of str
        """
        return self.app_settings["vport_names"]


    def get_trx_model(self):
        """
        Returns brand of the transceiver
        :return:
        :rtype: str
        """
        return self.app_settings["trx"]["model"]


    def get_trx_port(self):
        """
        Name for the Com port to which the transceiver is connected
        :return:
        :rtype: str
        """
        return self.app_settings["trx"]["port_name"]


    def get_trx_port_settings(self):
        """
        Com settings which can be directly imported the Serial class
        :return:
        :rtype: str
        """
        return self.app_settings["trx"]["port_settings"]


    def get_trx_port_dtr_init_state(self):
        """
        Reads the initial state that the DTR pin must be set to
        :return:
        :rtype: bool
        """
        return self.app_settings["trx"]["dtr_init_state"]


    def get_trx_port_rts_init_state(self):
        """
        Reads the initial state that the RTS pin must be set to
        :return:
        :rtype: bool
        """
        return self.app_settings["trx"]["rts_init_state"]


class PortAggregator(object):

    def __init__(self, settings):
        self.settings = settings
        self.transactions_queue = queue.Queue()
        self.alive = False
        self.log = logging.getLogger('PortAggregator')
        self.threads_vport_reader = []
        self.thread_trxport_reader = None
        self.thread_queue_reader = None


    def start(self):
        self.alive = True
        vports = []

        # Start vPORT-->QUEUE threads
        for port_name in settings.get_vports():
            ser = serial.Serial(port=port_name)
            ser.timeout = 1  # timeout is used to allow the threads to check for closing flag
            t = threading.Thread(target=self.vport_reader, args=(ser,))
            t.name = 'vport-to-queue'
            t.start()
            self.threads_vport_reader.append(t)
            vports.append(ser)

        # Start QUEUE-->TRX thread
        trx_ser = serial.Serial(port=settings.get_trx_port())
        trx_ser.dtr = settings.get_trx_port_dtr_init_state()
        trx_ser.rts = settings.get_trx_port_rts_init_state()
        trx_ser.timeout = 1  # timeout is used to allow the threads to check for closing flag
        trx_ser.apply_settings(settings.get_trx_port_settings())
        self.thread_queue_reader = threading.Thread(target=self.queue_reader, args=(trx_ser,))
        # self.thread_queue_reader.daemon = True
        self.thread_queue_reader.name = 'queue-to-trx_port'
        self.thread_queue_reader.start()

        # Start TRX-->vPORTS thread
        self.thread_trxport_reader = threading.Thread(target=self.trxport_reader, args=(trx_ser, vports,))
        # self.thread_trxport_reader.daemon = True
        self.thread_trxport_reader.name = 'trx_port-to-vports'
        self.thread_trxport_reader.start()


    def stop(self):
        """Stop all threads"""
        self.log.debug('stopping')

        if self.alive:
            self.alive = False
            for t in self.threads_vport_reader:
                t.join()
            self.threads_vport_reader.clear()
            self.thread_queue_reader.join()
            self.thread_trxport_reader.join()


    def vport_reader(self, vport_instance):
        """
        Reads data from the vPort. When a complete transaction is read it will add it to the queue.
        :param vport_instance: vPort instance (must be open)
        :type vport_instance: serial.Serial
        :return:
        """

        self.log.debug('Thread START: {}'.format(vport_instance.name))

        buffer = bytearray()

        while self.alive:
            try:
                if vport_instance.in_waiting > 0:
                    data = vport_instance.read(vport_instance.in_waiting)
                else:
                    data = vport_instance.read(1)

                if len(data):
                    self.log.debug("Bytes read ({}): {}".format(len(data), data))
                    buffer += bytearray(data)
                    trans = self.__extract_transactions(buffer, self.settings.get_trx_model())
                    if len(trans):
                        self.transactions_queue.put(trans)

            except Exception as msg:
                self.log.error('{}'.format(msg))
                break

        self.alive = False
        vport_instance.close()
        self.log.debug('Thread END')


    def queue_reader(self, trx_port_instance):
        """
        Reads transactions from the queue and sends them to the transceiver
        :param trx_port_instance: TRX port (must be open)
        :type trx_port_instance: serial.Serial
        :return:
        """
        self.log.debug('Thread START')

        while self.alive:
            try:
                trans = self.transactions_queue.get(timeout=1)  # Use timeout so that we can check the self.alive flag
                self.log.debug("Transaction ---> TRX_port ({}): {}".format(trx_port_instance.name, trans))
                trx_port_instance.write(trans)
            except queue.Empty as msg:
                continue
            except Exception as msg:
                self.log.error('{}'.format(msg))
                break

        self.alive = False
        trx_port_instance.close()
        self.log.debug('Thread END')


    def trxport_reader(self, trx_port_instance, vport_instances):
        """
        Redirects data coming from the trx_port to all vport_instances
        :param trx_port_instance: COM port of the TRX (must be open)
        :type trx_port_instance: serial.Serial
        :param vport_instances: Virtual COM port instances (must be open)
        :type vport_instances: list of serial.Serial
        :return:
        """
        self.log.debug('Thread START')

        while self.alive:
            try:
                if trx_port_instance.in_waiting:
                    data = trx_port_instance.read(trx_port_instance.in_waiting)
                else:
                    data = trx_port_instance.read(1)

                if len(data):
                    self.log.debug("Bytes coming from TRX ({}): {}".format(len(data), data))
                    for ser in vport_instances:
                        ser.write(data)

            except Exception as msg:
                self.log.error('{}'.format(msg))
                break

        self.alive = False
        self.log.debug('Thread END')


    @classmethod
    def __extract_transactions(cls, buffer, trx_model):
        """
        Extracts and returns all bytes which form a complete transaction from the bytearray "buffer". The "buffer" will
        decrease with the extracted amount of bytes.

        :param buffer: Array of bytes from which we have to extract all valid transactions.
        :type buffer: bytearray
        :param trx: Transceiver model
        :type trx: str
        :return: All data up to the last terminating byte (including)
        :rtype: bytearray
        """
        index = -1;
        for i, v in enumerate(reversed(buffer)):
            if v == cls.terminating_byte[trx_model]:
                index = len(buffer) - i - 1  # index in the original list
                break;

        # No complete transaction was found
        if index == -1:
            return bytearray();

        trans = buffer[:index + 1]
        del buffer[:index + 1]
        return trans


    # Transaction terminating bytes for different transceivers
    terminating_byte = {"Kenwood": 0x3B,
                        "Yaesu": 0x3B,
                        "Elecraft": 0x3B,
                        "Icom": 0xFD}


if __name__ == '__main__':

    # Load settings
    settings = Settings()

    print("TrxComAggregator v."+APP_VERSION+" by LZ1ABC. To exit press CTRL+C.")
    print("Using: TRX COM port {} and vCOM ports {}".format(settings.get_trx_port(), settings.get_vports()))
    aggregator = PortAggregator(settings)

    try:
        aggregator.start()
        while aggregator.alive:
            sleep(1)
    except KeyboardInterrupt:
        aggregator.stop()
        pass
    except Exception as msg:
        aggregator.stop()
        pass

    sleep(1)  # Give time for all threads to close and then print 73
    print("73!")
