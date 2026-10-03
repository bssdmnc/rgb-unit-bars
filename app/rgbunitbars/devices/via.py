import hid

REPORT_SIZE = 32
ID_CUSTOM_SET_VALUE = 0x07
ID_CUSTOM_GET_VALUE = 0x08


class ViaError(Exception):
    pass


def find_raw_hid(vendor_id, exclude_product=None):
    for info in hid.enumerate(vendor_id, 0):
        if info["usage_page"] != 0xFF60 or info["usage"] != 0x61:
            continue
        if exclude_product and exclude_product in (info["product_string"] or ""):
            continue
        return info
    return None


class ViaDevice:
    def __init__(self, info):
        self.info = info
        self.handle = hid.device()
        self.handle.open_path(info["path"])

    def close(self):
        self.handle.close()

    def command(self, data):
        packet = bytes(data) + bytes(REPORT_SIZE - len(data))
        self.handle.set_nonblocking(1)
        while self.handle.read(REPORT_SIZE):
            pass
        self.handle.set_nonblocking(0)
        self.handle.write(b"\x00" + packet)
        prefix = 3 if data[0] in (ID_CUSTOM_SET_VALUE, ID_CUSTOM_GET_VALUE) else 1
        for _ in range(8):
            reply = self.handle.read(REPORT_SIZE, 1000)
            if not reply:
                break
            if list(reply[:prefix]) == list(packet[:prefix]):
                return reply
        raise ViaError("no matching reply from keyboard")
