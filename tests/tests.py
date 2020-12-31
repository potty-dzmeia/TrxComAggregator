import unittest
from app import PortRedirector
from app import Settings

# input  return   leftover
kenwood_transactions = [
    (bytearray(b"data;"), bytearray(b"data;"), bytearray(b"")),
    (bytearray(b"data;asdf;data;asdf;333"), bytearray(b"data;asdf;data;asdf;"), bytearray(b"333")),
    (bytearray(b"data;sdf"), bytearray(b"data;"), bytearray(b"sdf")),
    (bytearray(b""), bytearray(b""), bytearray(b"")),
    (bytearray(b"d"), bytearray(b""), bytearray(b"d")),
    (bytearray(b"\x34;"), bytearray(b"4;"), bytearray(b"")),
    (bytearray(b"\xFD;"), bytearray(b"\xFD;"), bytearray(b"")),
    (bytearray(b";"), bytearray(b";"), bytearray(b"")),
    (bytearray(b";;;a"), bytearray(b";;;"), bytearray(b"a")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;IF00007267891+yyyyrx*00t11spbd1*"),
     bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*"))
]

yaesu_transactions = [
    (bytearray(b"data;"), bytearray(b"data;"), bytearray(b"")),
    (bytearray(b"data;asdf;data;asdf;333"), bytearray(b"data;asdf;data;asdf;"), bytearray(b"333")),
    (bytearray(b"data;sdf"), bytearray(b"data;"), bytearray(b"sdf")),
    (bytearray(b""), bytearray(b""), bytearray(b"")),
    (bytearray(b"d"), bytearray(b""), bytearray(b"d")),
    (bytearray(b";"), bytearray(b";"), bytearray(b"")),
    (bytearray(b";;;a"), bytearray(b";;;"), bytearray(b"a")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;IF00007267891+yyyyrx*00t11spbd1*"),
     bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*"))
]

elecraft_transactions = [
    (bytearray(b"data;"), bytearray(b"data;"), bytearray(b"")),
    (bytearray(b"data;asdf;data;asdf;333"), bytearray(b"data;asdf;data;asdf;"), bytearray(b"333")),
    (bytearray(b"data;sdf"), bytearray(b"data;"), bytearray(b"sdf")),
    (bytearray(b""), bytearray(b""), bytearray(b"")),
    (bytearray(b"d"), bytearray(b""), bytearray(b"d")),
    (bytearray(b";"), bytearray(b";"), bytearray(b"")),
    (bytearray(b";;;a"), bytearray(b";;;"), bytearray(b"a")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"FA01234567890;"), bytearray(b"FA01234567890;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"")),
    (bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;IF00007267891+yyyyrx*00t11spbd1*"),
     bytearray(b"IF00007267891+yyyyrx*00t11spbd1*;"), bytearray(b"IF00007267891+yyyyrx*00t11spbd1*"))
]

# input  return   leftover
icom_transactions = [
    [bytearray.fromhex("FE FE 5e 5c FD"), bytearray.fromhex("FE FE 5e 5c FD"), bytearray.fromhex("")],
    [bytearray.fromhex("FE FE 5e 5c FD FE FE 00 33 FD"), bytearray.fromhex("FE FE 5e 5c FD FE FE 00 33 FD"),
     bytearray.fromhex("")],
    [bytearray.fromhex("FE FE 5e 5c FD FE FE 5e 5c "), bytearray.fromhex("FE FE 5e 5c FD"),
     bytearray.fromhex("FE FE 5e 5c")],
    [bytearray.fromhex(""), bytearray.fromhex(""), bytearray.fromhex("")],
    [bytearray.fromhex("FD"), bytearray.fromhex("FD"), bytearray.fromhex("")],
    [bytearray.fromhex("FD"), bytearray.fromhex("FD"), bytearray.fromhex("")],
    [bytearray.fromhex("FD FD FD FD"), bytearray.fromhex("FD FD FD FD"), bytearray.fromhex("")],
    [bytearray.fromhex("FE FE 5e 03 FD"), bytearray.fromhex("FE FE 5e 03 FD"), bytearray.fromhex("")],
]


class PortRedirector_Test(unittest.TestCase):

    def test_kenwood(self):
        for test_item in kenwood_transactions:
            result = PortRedirector._PortRedirector__extract_transactions(test_item[0], "Kenwood")
            self.assertTrue(result == test_item[1])
            self.assertTrue(test_item[0] == test_item[2])

    def test_yaesu(self):
        for test_item in yaesu_transactions:
            result = PortRedirector._PortRedirector__extract_transactions(test_item[0], "Yaesu")
            self.assertTrue(result == test_item[1])
            self.assertTrue(test_item[0] == test_item[2])

    def test_elecraft(self):
        for test_item in elecraft_transactions:
            result = PortRedirector._PortRedirector__extract_transactions(test_item[0], "Elecraft")
            self.assertTrue(result == test_item[1])
            self.assertTrue(test_item[0] == test_item[2])

    def test_icom(self):
        for test_item in icom_transactions:
            result = PortRedirector._PortRedirector__extract_transactions(test_item[0], "Icom")
            self.assertTrue(result == test_item[1])
            self.assertTrue(test_item[0] == test_item[2])


class Settings_Test(unittest.TestCase):

    def test1(self):
        # Create object  with default settings
        settings = Settings("tests/test-settings.cfg")

        self.assertEqual(settings.get_trx_model(), "Kenwood")
        self.assertListEqual(settings.get_vports(), ["COM15", "COM16", "COM17"])
        self.assertTrue(settings.get_vports_count() == 3)
        self.assertEqual(settings.get_trx_port(), "COM9")
        self.assertTrue(settings.get_trx_port_settings()["baudrate"] == 115200)
        self.assertTrue(settings.get_trx_port_settings()["bytesize"] == 8)
        self.assertTrue(settings.get_trx_port_settings()["parity"] == "N")
        self.assertTrue(settings.get_trx_port_settings()["stopbits"] == 1)


    def test2(self):
        # Create object  with default settings
        settings = Settings("tests/test-settings2.cfg")

        self.assertEqual(settings.get_trx_model(), "Icom")
        self.assertListEqual(settings.get_vports(), ["COM2"])
        self.assertTrue(settings.get_vports_count() == 1)
        self.assertEqual(settings.get_trx_port(), "COM1")
        self.assertTrue(settings.get_trx_port_settings()["baudrate"] == 115200)
        self.assertTrue(settings.get_trx_port_settings()["bytesize"] == 8)
        self.assertTrue(settings.get_trx_port_settings()["parity"] == "N")
        self.assertTrue(settings.get_trx_port_settings()["stopbits"] == 1)

        self.assertTrue(settings.get_trx_port_settings()["xonxoff"] == False)
        self.assertTrue(settings.get_trx_port_settings()["dsrdtr"] == False)
        self.assertTrue(settings.get_trx_port_settings()["rtscts"] == False)
        self.assertTrue(settings.get_trx_port_settings()["timeout"] == None)
        self.assertTrue(settings.get_trx_port_settings()["write_timeout"] == None)
        self.assertTrue(settings.get_trx_port_settings()["inter_byte_timeout"] == None)


if __name__ == '__main__':
    unittest.main()
