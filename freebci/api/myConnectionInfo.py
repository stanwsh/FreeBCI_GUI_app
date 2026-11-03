from freebci.core.catalog import rows as catalog_rows


class connectInfo:
    def __init__(self) -> None:
        self.id_list = catalog_rows()
        self.board_id = 2049
        self.connect_type = self.id_list[self.board_id - 2023][2]
        self.board = None
        self.wifi_address = None
        self.wifi_port = 0
        self.serial_port = None
        self.channel_num = self.id_list[self.board_id - 2023][8]
        self.baudRate = self.id_list[self.board_id - 2023][3]
        self.iswifi = False
        self.isbluetooth = False


class HardwareInfo:
    def __init__(self):
        self.SamplingRate = 250
        self.baudRate = '115200'
        self.activeChannels = []
        self.channel_num = 8
        self.isSend = False
        self.isApply = False
        self.chanMatched_index = [i for i in (range(self.channel_num - 1))]
        self.isAccelerometer = False
        self.sendMode = 'FreeBCI'
        self.dataMode = 'Battery'
