"""
Use bittify() as a way to byte encode various objects.
"""
from Attributes import attributes

# Define global vars
id = 1

# The SFTP packet types
FXP_names = {
    "SSH_FXP_INIT": 1,
    "SSH_FXP_VERSION": 2,
    "SSH_FXP_OPEN": 3,
    "SSH_FXP_CLOSE": 4,
    "SSH_FXP_READ": 5,
    "SSH_FXP_WRITE": 6,
    "SSH_FXP_LSTAT": 7,
    "SSH_FXP_FSTAT": 8,
    "SSH_FXP_SETSTAT": 9,
    "SSH_FXP_FSETSTAT": 10,
    "SSH_FXP_OPENDIR": 11,
    "SSH_FXP_READDIR": 12,
    "SSH_FXP_REMOVE": 13,
    "SSH_FXP_MKDIR": 14,
    "SSH_FXP_RMDIR": 15,
    "SSH_FXP_REALPATH": 16,
    "SSH_FXP_STAT": 17,
    "SSH_FXP_RENAME": 18,
    "SSH_FXP_READLINK": 19,
    "SSH_FXP_SYMLINK": 20,
    "SSH_FXP_STATUS": 101,
    "SSH_FXP_HANDLE": 102,
    "SSH_FXP_DATA": 103,
    "SSH_FXP_NAME": 104,
    "SSH_FXP_ATTRS": 105,
    "SSH_FXP_EXTENDED": 200,
    "SSH_FXP_EXTENDED_REPLY": 201
}

# The SFTP status types
FX_names = {
    "SSH_FX_OK": 0,
    "SSH_FX_EOF": 1,
    "SSH_FX_NO_SUCH_FILE": 2,
    "SSH_FX_PERMISSION_DENIED": 3,
    "SSH_FX_FAILURE": 4,
    "SSH_FX_BAD_MESSAGE": 5,
    "SSH_FX_NO_CONNECTION": 6,
    "SSH_FX_CONNECTION_LOST": 7,
    "SSH_FX_OP_UNSUPPORTED": 8
}

# pflags for editing files
PFLAG_names = {
    "SSH_FXF_READ":   0x00000001,
    "SSH_FXF_WRITE":  0x00000002,
    "SSH_FXF_APPEND": 0x00000004,
    "SSH_FXF_CREAT":  0x00000008,
    "SSH_FXF_TRUNC":  0x00000010,
    "SSH_FXF_EXCL":   0x00000020
}

# Define helper methods
def bittify(obj, len=None):
    """
    Take an object, and convert it to bytearray.
    If length is specified, and obj is not a String or attributes, then the returned bytearray
    will be padded to this length.
    """
    pad = True # Start off assuming we pad everything.

    # Get the bytearray for each type of object.
    if isinstance(obj, int):
        # Convert large numbers to a bytearray friendly format.
        b = []
        while obj > 0:
            b.append(obj%256)
            obj -= obj%256
            obj = obj//256

        b.reverse()

        arr = bytearray(b)
    elif isinstance(obj, str):
        arr = bytearray(obj, "utf-8")
        pad = False
    elif isinstance(obj, attributes):
        arr = obj.bytes()
        pad = False
    else:
        arr = bytearray(obj)

    # Get length of bytearray, which Python doesn't support natively. >.>  <.<
    length = 0
    for byte in arr:
        length += 1

    # Byte pad our object
    if pad:
        assert not (len is None), "Length missing for an object."

        if length < len:
            arr = bytearray(len - length) + arr

    # Strings should be appended with 4 bytes detailing their length.
    if isinstance(obj, str):
        arr = bittify([length], 4) + arr

    return arr

# Define classes
class packet():
    """
    A SFTP request/response as defined by the SFTP internet draft 02.

    Use packet.bytes() to get the byte encoding of a packet, and
    packet.decode(bytes) to decode a server response.

    FXP_type is the type of the request/response as defined by the SFTP internet draft 02.

    id is a unique int identifying this packet.

    items is an array of the objects to included in the message/request.
    lengths is an array of the requested byte lengths of items, as provided.

    Please note, the purpose of packet is to provide a low-level interface for creating SFTP messages/requests.
    As such, packet will NOT interpret the contents of packet. That is for the implementer of packet.
    """

    def __init__(self, FXP_type=None, b=None, id=None):
        self.FXP_type = FXP_type
        self.id = id
        self.items = []
        self.lengths = []

        if not (b is None):
            self.decode(b)

    def assign_next_id(self):
        global id
        self.id = id
        id = (id+1)%4294967295

    def add(self, item, len=None):
        self.items.append(item)
        self.lengths.append(len)

    def remove(self, item):
        index = self.items.index(item)
        del self.items[index]
        del self.lengths[index]

    def get_FXP_type(self):
        return self.FXP_type

    def get_id(self):
        return self.id

    def get_items(self):
        return self.items

    def get_lengths(self):
        return self.items

    def bytes(self):
        """
        Encode a packet as bytes.

        Format:
        uint32             length
        byte               type
        byte[length - 1]   data payload
        """
        msg = bytearray() # The request/response, aka "data payload"

        # For each item in packet, turn it into a bytearray and append it to the message
        for item, length in zip(self.items, self.lengths):
            msg += bittify(item, length)

        if not (self.id is None):
            id_bytes = bittify(self.id, 4)
            msg = id_bytes + msg

        # Determine the message length and type
        length_bytes = bittify(len(msg)+1, 4)
        FXP_type_byte = self.FXP_type_byte()

        # Attach message length and type
        msg = length_bytes + FXP_type_byte + msg

        # Convert from bytearray to bytes for sending
        msg= bytes(list(msg))

        print("Encoded packet: " + str(msg))

        return msg

    def decode(self, b):
        """
        Decode a server bytearray response into a packet.

        As such, this method should ONLY be used to decode messages expected from an SFTP server.
        """

        # Get message length and type
        len = int.from_bytes(b[0:4], byteorder='big', signed=False)
        try:
            FXP_type_id = b[4]
        except Exception:
            raise Exception("Empty String received.")

        print("Decoding packet of type " + str(FXP_type_id))

        # Set packet type
        self.FXP_type = self.FXP_type_name(FXP_type_id)

        # Decode the rest of the message
        msg = b[5:]
        if FXP_type_id == FXP_names["SSH_FXP_VERSION"]:
            self.__decode_VERSION(msg)
        elif FXP_type_id == FXP_names["SSH_FXP_HANDLE"]:
            self.__decode_HANDLE(msg)
        elif FXP_type_id == FXP_names["SSH_FXP_STATUS"]:
            self.__decode_STATUS(msg)
        elif FXP_type_id == FXP_names["SSH_FXP_NAME"]:
            self.__decode_NAME(msg)
        elif FXP_type_id == FXP_names["SSH_FXP_ATTRS"]:
            self.__decode_ATTRS(msg)
        elif FXP_type_id == FXP_names["SSH_FXP_DATA"]:
            self.__decode_DATA(msg)
        else:
            raise Exception("What. Tried to decode unexpected packet of type " + self.FXP_type + ".")

    def __decode_VERSION(self, b):
        """
        Format:
        uint32 version
        <extension data pairs>

        <extension data> format:
        string extension_name
        string extension_data
        """
        # Get the version number
        self.add(int.from_bytes(b[0:4], byteorder='big', signed=False), 4)

        # Get extension data
        i = 4
        while i < len(b):
            # Extract the extension name
            string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
            extension_name = b[i + 4:i + 4 + string_len].decode("utf-8")

            self.add(extension_name, string_len)

            i += 4 + string_len

            # Extract the extension data
            string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
            extension_data = b[i + 4:i + 4 + string_len].decode("utf-8")

            self.add(extension_data, string_len)

            i += 4 + string_len

    def __decode_HANDLE(self, b):
        """
        Format:
        uint32     id
        string     handle
        """
        self.id = int.from_bytes(b[0:4], byteorder='big', signed=False)

        string_len = int.from_bytes(b[4:8], byteorder='big', signed=False)
        handle = b[8:8 + string_len].decode("utf-8")

        self.add(handle, 4)

    def __decode_STATUS(self, b):
        """
        Format:
        uint32     id
        uint32     error/status code
        string     error/status message (ISO-10646 UTF-8 [RFC-2279])
        string     language tag (as defined in [RFC-1766])
        """
        self.id = int.from_bytes(b[0:4], byteorder='big', signed=False)

        self.add(int.from_bytes(b[4:8], byteorder='big', signed=False))

        i = 8

        # Extract error message, if there is one
        if len(b) > i:
            string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
            message = b[i + 4:i + 4 + string_len].decode("utf-8")

            self.add(message)

            i += 4 + string_len

            # Extract language tag, if there is one
            if len(b) > i:
                string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
                language = b[i + 4:i + 4 + string_len].decode("utf-8")

                self.add(language)

    def __decode_NAME(self, b):
        """
        Format:
        uint32     id
        uint32     count
        repeats count times:
                string     filename
                string     longname
                ATTRS      attrs
        """
        self.id = int.from_bytes(b[0:4], byteorder='big', signed=False)

        num_files = int.from_bytes(b[4:8], byteorder='big', signed=False)
        self.add(num_files, 4)

        i = 8
        for file in range(1, num_files+1):
            # Extract filename
            string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
            filename = b[i+4:i+4+string_len].decode("utf-8")

            self.add(filename, string_len)

            i += 4 + string_len

            # Extract longname
            string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
            longname = b[i+4:i+4+string_len].decode("utf-8")

            self.add(longname, string_len)

            i += 4 + string_len

            # Decode attributes
            attr = attributes(b=b[i:]) # Shove in everything

            self.add(attr)

            i += attr.get_byte_length()

    def __decode_ATTRS(self, b):
        """
        Format:
        uint32     id
        ATTRS      attrs <- Dummy attributes
        """
        self.id = int.from_bytes(b[0:4], byteorder='big', signed=False)

        attr = attributes(b=b[4:])  # Shove in everything

        self.add(attr)

    def __decode_DATA(self, b):
        """
        Format:
        uint32     id
        string     data
        """
        self.id = int.from_bytes(b[0:4], byteorder='big', signed=False)

        string_len = int.from_bytes(b[4:8], byteorder='big', signed=False)
        data = b[8:8 + string_len].decode("utf-8")

        self.add(data, 4)

    def FXP_type_byte(self):
        num = FXP_names[self.FXP_type]

        bts = bittify(num, 1)

        return bts

    def FXP_type_name(self, FXP_id):
        for FXP, id in FXP_names.items():
            if FXP_id == id:
                return FXP

        return None

    def FX_type_byte(self, FX_type):

        num = FX_names[FX_type]

        bts = bittify(num, 1)

        return bts

    def FX_type_name(self, FX_id):
        for FX, id in FX_names.items():
            if FX_id == id:
                return FX

        return None

    def PFLAG_type_byte(self, PFLAG_type):
        num = PFLAG_names[PFLAG_type]

        bts = bittify(num, 1)

        return bts

    def PFLAG_type_name(self, PFLAG_byte):
        for PFLAG, id in PFLAG_names.items():
            if PFLAG_byte == id:
                return PFLAG

        return None

    def __str__(self):
        to_return = "Packet (type: " + self.FXP_type + ")"

        for item in self.items:
            to_return += "\n" + str(item)

        return to_return