

class HexDump:
    def __init__(self,
                 fmt='{addr:04x}  {h[0]:23}  {h[1]:23}  |{s[0]}{s[1]}|',
                 hex_fmt='{:02x} ',
                 group_length=8,
                 length=16):
        self.fmt = fmt
        self.hex_fmt = hex_fmt
        self.group_length = group_length
        self.length = length

    def _hex(self, data):
        # We strip any leading/trailing whitespace. Whitespace surrounding
        # groups belongs in 'fmt'.
        return ''.join(self.hex_fmt.format(b) for b in data).strip()

    @staticmethod
    def _str(data):
        # 32 to 126 are the printable ASCII characters
        return ''.join((32 <= b <= 126 and chr(b)) or '.' for b in data)

    def __call__(self, data):
        return self.dump(data)

    def dump(self, data):
        return '\n'.join(self.dump_iter(data))

    def dump_iter(self, data):

        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')

        for addr in range(0, len(data), self.length):
            row = data[addr: addr + self.length]
            h = []
            s = []
            # Chop up the row into byte/text groups
            for i in range(0, self.length, self.group_length):
                group = row[i: i + self.group_length]
                h.append(self._hex(group))
                s.append(self._str(group))
            yield self.fmt.format(addr=addr, h=h, s=s)
