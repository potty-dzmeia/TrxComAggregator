import serial
import json
import logging.config
import threading
import queue
from time import sleep

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class Settings(object):

    def __init__(self, settings=None):

        if settings:
            file = settings
        else:
            file = "settings.cfg"

        with open(file) as json_file:
            self.app_settings = json.load(json_file)


    def get_vports_count(self):
        return self.app_settings["vport_names"].__len__()


    def get_vports(self):
        return self.app_settings["vport_names"]


    def get_trx_model(self):
        return self.app_settings["trx"]["model"]


    def get_trx_port(self):
        return self.app_settings["trx"]["port_name"]


    def get_trx_port_settings(self):
        return self.app_settings["trx"]["port_settings"]


class PortRedirector(object):

    def __init__(self, settings):
        self.settings = settings
        self.transactions_queue = queue.Queue()
        self.alive = False
        self.log = logging.getLogger('PortRedirector')
        self.log.setLevel(level=logging.DEBUG)
        self.threads_vport_reader = []
        self.thread_trxport_reader = None
        self.thread_queue_reader = None


    def start(self):
        self.alive = True
        vports = []

        # Start vport_reader threads
        for port_name in settings.get_vports():
            ser = serial.Serial(port=port_name)
            ser.timeout = 1  # big timeout is used to allow the threads to close if needed
            t = threading.Thread(target=self.vport_reader, args=(ser,))
            # t.daemon = True
            t.name = 'vport-to-queue'
            t.start()
            self.threads_vport_reader.append(t)
            vports.append(ser)

        # Start queue_reader threads
        trx_ser = serial.Serial(port=settings.get_trx_port())
        trx_ser.timeout = 1  # big timeout is used to allow the threads to close if needed
        trx_ser.apply_settings(settings.get_trx_port_settings())
        self.thread_queue_reader = threading.Thread(target=self.queue_reader, args=(trx_ser,))
        # self.thread_queue_reader.daemon = True
        self.thread_queue_reader.name = 'queue-to-trx_port'
        self.thread_queue_reader.start()

        # Start queue_reader threads
        self.thread_trxport_reader = threading.Thread(target=self.trxport_reader, args=(trx_ser, vports,))
        # self.thread_trxport_reader.daemon = True
        self.thread_trxport_reader.name = 'trx_port-to-vports'
        self.thread_trxport_reader.start()


    def stop(self):
        """Stop redirecting"""
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

        :param vport_instance:
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
                logger.error('{}'.format(msg))
                break

        self.alive = False
        vport_instance.close()
        self.log.debug('Thread END')


    def queue_reader(self, trx_port_instance):
        """

        :param trx_port_instance:
        :type trx_port_instance: serial.Serial
        :return:
        """
        self.log.debug('Thread START')

        while self.alive:
            try:
                trans = self.transactions_queue.get(timeout=1)  # Use timeout so that we can check the self.alive flag
                self.log.debug("Transaction ---> TRX_port ({}): {}".format(trx_port_instance.name, trans))
                trx_port_instance.write(trans)
                trx_port_instance.flush()

            except queue.Empty as msg:
                continue
            except Exception as msg:
                logger.error('{}'.format(msg))
                break

        self.alive = False
        trx_port_instance.close()
        self.log.debug('Thread END')


    def trxport_reader(self, trx_port_instance, vport_instances):
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
                logger.error('{}'.format(msg))
                break

        self.alive = False
        trx_port_instance.close()
        self.log.debug('Thread END')


    @classmethod
    def __extract_transactions(cls, buffer, trx):
        """
        Extracts and returns all bytes which form a complete transaction from the "buffer" bytearray. The "buffer" will
        decrease with the extracted amount of bytes.

        :param buffer: array of byte from which we have to extract all valid transactions.
        :type buffer: bytearray
        :param trx: Brand of transceiver
        :type trx: str
        :return: All data up to the last terminating byte (including)
        :rtype: bytearray
        """
        index = -1;
        for i, v in enumerate(reversed(buffer)):
            if v == cls.terminating_byte[trx]:
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

    print("Trx-Com-Splitter by LZ1ABC.")
    print("TRX ComPort is: {}".format(settings.get_trx_port()))
    print("Virtual CommPorts are: {}".format(settings.get_vports()))
    redirector = PortRedirector(settings)

    try:
        redirector.start()

        while redirector.alive:
            sleep(1)
    except Exception:
        redirector.stop()

    sleep(1)
    print("73!")
