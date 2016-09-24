# Import stuff
import Packet

# Define global vars
pinkie_pie = "was here"

# Used by SFTP to denote what is included in an attribute object.
FILEXFER_names = {
    "SSH_FILEXFER_ATTR_SIZE":        0x00000001, # Has size only
    "SSH_FILEXFER_ATTR_UIDGID":      0x00000002, # Has UID, GID and above
    "SSH_FILEXFER_ATTR_PERMISSIONS": 0x00000004, # Has permissions and above
    "SSH_FILEXFER_ATTR_ACMODTIME":   0x00000008, # Has atime, mtime, and above
    "SSH_FILEXFER_ATTR_EXTENDED":    0x80000000  # Has extensions and above
}

# Used by Unix systems to indicate file "status" information
STATUS_BITS = {
    "S_IFSOCK":   0o140000, #  socket
    "S_IFLNK":    0o120000, #  symbolic link
    "S_IFREG":    0o100000, #  regular file
    "S_IFBLK":    0o060000, #  block device
    "S_IFDIR":    0o040000, #  directory
    "S_IFCHR":    0o020000, #  character device
    "S_IFIFO":    0o010000, #  FIFO
    "S_ISUID":    0o004000, #  set UID bit
    "S_ISGID":    0o002000, #  set-group-ID bit
    "S_ISVTX":    0o001000, #  sticky bit
    "S_IRUSR":    0o000400, #  owner has read permission
    "S_IWUSR":    0o000200, #  owner has write permission
    "S_IXUSR":    0o000100, #  owner has execute permission
    "S_IRGRP":    0o000040, #  group has read permission
    "S_IWGRP":    0o000020, #  group has write permission
    "S_IXGRP":    0o000010, #  group has execute permission
    "S_IROTH":    0o000004, #  others have read permission
    "S_IWOTH":    0o000002, #  others have write permission
    "S_IXOTH":    0o000001  #  others have execute permission
}

# Define classes
class attributes():
    """
    attributes is a wrapper class as defined by the SFTP internet draft 02. It describes the attributes of a file.

    Use attributes.bytes() to get the byte encoding, and attributes.decode(bytes) to decode from bytes.

    'atime' and 'mtime' are the access and modification times of a file, respectively. They are represented as seconds
    from Jan 1, 1970 in UTC.

    Format:
    uint32   flags
    uint64   size           present only if flag SSH_FILEXFER_ATTR_SIZE
    uint32   uid            present only if flag SSH_FILEXFER_ATTR_UIDGID
    uint32   gid            present only if flag SSH_FILEXFER_ATTR_UIDGID
    uint32   permissions    present only if flag SSH_FILEXFER_ATTR_PERMISSIONS
    uint32   atime          present only if flag SSH_FILEXFER_ACMODTIME
    uint32   mtime          present only if flag SSH_FILEXFER_ACMODTIME
    uint32   extended_count present only if flag SSH_FILEXFER_ATTR_EXTENDED
    string   extended_type
    string   extended_data
    ...      more extended data (extended_type - extended_data pairs),
               so that number of pairs equals extended_count
    """

    def __init__(self, size = None, uid = None, gid = None, permissions = None, atime = None,
                 mtime = None, extended_type = [], extended_data = [], b = None):
        self.size = size
        self.uid = uid
        self.gid = gid
        self.permissions = permissions
        self.atime = atime
        self.mtime = mtime
        self.extended_type = extended_type
        self.extended_data = extended_data

        self.byte_length = None # Only used when decoding attributes

        if not (b is None):
            self.decode(b)

    def get_byte_length(self):
        return self.byte_length

    def get_flags(self):
        """
        Construct and return the flags 8-digit decimal code.
        """
        flags = 0

        if not (self.size is None):
            flags += FILEXFER_names["SSH_FILEXFER_ATTR_SIZE"]
        if not (self.uid is None) and not (self.gid != None):
            flags += FILEXFER_names["SSH_FILEXFER_ATTR_UIDGID"]
        if not (self.permissions is None):
            flags += FILEXFER_names["SSH_FILEXFER_ATTR_PERMISSIONS"]
        if not (self.atime is None) and not (self.mtime is None):
            flags += FILEXFER_names["SSH_FILEXFER_ATTR_ACMODTIME"]
        if self.extended_type != [] and self.extended_data != []:
            flags += FILEXFER_names["SSH_FILEXFER_ATTR_EXTENDED"]

        return flags

    def get_size(self):
        return self.size

    def get_uid(self):
        return self.uid

    def get_gid(self):
        return self.gid

    def get_permissions(self):
        return self.permissions

    def get_atime(self):
        return self.atime

    def get_mtime(self):
        return self.mtime

    def get_extended_type(self):
        return self.extended_type

    def get_extended_data(self):
        return self.extended_data

    def get_file_type(self):
        """
        Get a String indicating the file type.
        Strings are defined as per POSIX.
        A dictionary of POSIX values and corresponding bits is provided at the top of this file.
        """
        if not (self.permissions is None):
            if self.permissions > 4096:
                file_type_bits = (self.permissions&61440)>>12
                if file_type_bits&1 == 1:
                    return "S_IFIFO"
                else:
                    if file_type_bits&8 == 8:
                        if file_type_bits&4 == 4:
                            return "S_IFSOCK"
                        else:
                            if file_type_bits&2 == 2:
                                return "S_IFLINK"
                            else:
                                return "S_IFREG"
                    else:
                        if file_type_bits&4 == 4:
                            if file_type_bits&2 == 2:
                                return "S_IFBLK"
                            else:
                                return "S_IFDIR"
                        else:
                            return "S_IFIFO"
            else:
                return None
        else:
            return None

    def bytes(self):
        """
        Get the bytes representing this attributes object.
        """
        msg = bytearray()

        # Attach attribute flags
        msg += Packet.bittify(self.get_flags(), 4)

        # Attach attribute properties
        if not (self.size is None):
            msg += Packet.bittify(self.size, 8)
        if not (self.uid is None) and not (self.gid is None):
            msg += Packet.bittify(self.uid, 4)
            msg += Packet.bittify(self.gid, 4)
        if not (self.permissions is None):
            msg += Packet.bittify(self.permissions, 4)
        if not (self.atime is None) and not (self.mtime is None):
            msg += Packet.bittify(self.atime, 4)
            msg += Packet.bittify(self.mtime, 4)

        # Attach extensions
        if self.extended_type != [] and self.extended_data != []:
            for type, data in zip(self.extended_type, self.extended_data):
                msg += Packet.bittify(type)
                msg += Packet.bittify(data)

        return msg

    def decode(self, b):
        """
        Given a bytes object that starts with an encoded attributes object, extract the attributes object,
        and store its byte length.
        """
        # Check what is included in this attributes file
        flags = int.from_bytes(b[0:4], byteorder='big', signed=False)

        # Use FILEXFER_names as a guide
        has_size = flags&1 == 1
        has_uidgid = flags&2 == 2
        has_permissions = flags&4 == 4
        has_acmodtime = flags&8 == 8
        has_extended = flags&16 == 16

        # Extract the easy ints
        i = 4
        if has_size:
            self.size = int.from_bytes(b[i:i+8], byteorder='big', signed=False)
            i += 8
        if has_uidgid:
            self.uid = int.from_bytes(b[i:i+4], byteorder='big', signed=False)
            self.gid = int.from_bytes(b[i+4:i+8], byteorder='big', signed=False)
            i += 8
        if has_permissions:
            self.permissions = int.from_bytes(b[i:i+4], byteorder='big', signed=False)
            i += 4
        if has_acmodtime:
            self.atime = int.from_bytes(b[i:i+4], byteorder='big', signed=False)
            self.mtime = int.from_bytes(b[i+4:i+8], byteorder='big', signed=False)
            i += 8

        # Get the extensions (if included)
        if has_extended:
            num_extensions = int.from_bytes(b[i:i+4], byteorder='big', signed=False)
            i+= 4

            for extension in range(1, num_extensions):
                string_len = int.from_bytes(b[i:i+4], byteorder='big', signed=False)
                type = b[i+4:i+4+string_len].decode("utf-8")

                self.extended_type.append(type)

                i += 4 + string_len

                string_len = int.from_bytes(b[i:i + 4], byteorder='big', signed=False)
                data = b[i+4:i+4+string_len].decode("utf-8")


                self.extended_data.append(data)

                i += 4 + string_len

        # Record byte length for parsing purposes
        self.byte_length = i

    def FILEXFER_type_name(self, FILEXFER_id):
        """
        Convert a FILEXFER bit to its corresponding name.
        """
        for FILEXFER, id in FILEXFER_names.items():
            if FILEXFER_id == id:
                return FILEXFER

        return None

    def __str__(self):
        to_return = ""

        flags = self.get_flags()

        # Use FILEXFER_names as a guide
        has_size = flags&1 == 1
        has_uidgid = flags&2 == 2
        has_permissions = flags&4 == 4
        has_acmodtime = flags&8 == 8
        has_extended = flags&16 == 16

        to_return += "\tAttributes"
        to_return += "\n\tFlags: " + str(flags)
        if has_size:
            to_return += "\n\tSize: " + str(self.size)
        if has_uidgid:
            to_return += "\n\tUID: " + str(self.uid)
            to_return += "\n\tGID: " + str(self.gid)
        if has_permissions:
            to_return += "\n\tPermissions: " + str(self.permissions)
        if has_acmodtime:
            to_return += "\n\tAtime: " + str(self.atime)
            to_return += "\n\tMtime: " + str(self.mtime)

        if has_extended:
            to_return += "\n\tExtended"
            to_return += "\n\tExt count: " + str(len(self.extended_type))

            for type, data in zip(self.extended_type, self.extended_data):
                to_return += "\n\t\tExt_type: " + type
                to_return += "\n\t\tExt_data: " + data

        return to_return