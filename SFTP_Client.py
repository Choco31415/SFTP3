# Handle imports
from SSH_Client import SSH
from Packet import packet
from Attributes import attributes

import socket

# Define classes
class SFTP_client(SSH):
    """
    A SFTP v3 client as per the SFTP internet draft 02.

    Use open_sftp_session() to open an sftp channel, and use init() afterwards to start an sftp session.
    Use stop() to close the sftp channel, freeing it for future usage.
    """

    conn_timeout = 0.2 # For connection timeouts

    def open_sftp_channel(self, window_size=None, max_packet_size=None):
        """
        Connect to the sftp channel.
        """
        if not max_packet_size is None:
            self.max_packet_size = max_packet_size

        transport = self.ssh.get_transport()
        chan = transport.open_session(window_size=window_size,
                              max_packet_size=max_packet_size, timeout=1)
        if chan is None:
            return None # Error, don't know why
        chan.invoke_subsystem('sftp')
        chan.settimeout(self.conn_timeout)

        self.socket = chan

        self.__initiate()

    def __send(self, msg):
        """
        Send bytes to server.
        """
        self.open_sftp_channel(window_size=2048)

        length = len(msg)
        total_sent = 0
        sent = 0

        # Send message until everything is sent.
        while sent < length:
            sent += self.socket.__send(msg[total_sent:])
            if sent == 0:
                # This indicates an error or connection break
                raise RuntimeError("socket connection broken")
            total_sent += sent

    def __recv(self, max_packet_size = None):
        """
        Listen for bytes from server.
        """
        msg = bytes()
        recv = ""

        if max_packet_size is None:
            max_packet_size = self.max_packet_size

        # Read from the connection until timeout.
        while not (recv is None):
            try:
                recv = self.socket.__recv(max_packet_size)
            except socket.timeout:
                # Timeout occurred
                recv = None

            if recv == bytes():
                # This indicates an error or connection break
                raise RuntimeError("socket connection broken")

            if not (recv is None):
                msg += recv

        print("got: " + str(msg))

        return msg

    def __initiate(self):
        """
        Initiate the SFTP connection. This negotiates sftp versions between client and server.
        This is required to be run before any SFTP requests are sent.

        :return: None
        """

        """
        uint32 version
        <extension data>
        """
        c_packet = packet("SSH_FXP_INIT")
        c_packet.add(3, 4)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check that servers agree on the SFTP protocol version.
        if r_packet.get_items()[0] != 3:
            raise Exception("SFTP cannot settle on the protocol version to use.")

    def create_dir(self, dir, attr = None):
        """
        Create a directory.

        :param dir: Where to create the directory. Path is relative to user's ~.
        :param attr: Attributes for the directory. Normally, this can be left alone.
        :return: None
        """

        # Create directory
        """
        uint32 id
        string path
        ATTRS attrs
        """
        c_packet = packet("SSH_FXP_MKDIR")
        c_packet.assign_next_id()
        c_packet.add(dir)
        if attr is None:
            attr = attributes()
        c_packet.add(attr)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def remove_dir(self, dir):
        """
        Remove a directory.

        :param dir: The directory to remove. Path is relative to user's ~.
        :return: None
        """

        # Make directory
        """
        uint32 id
        string path
        """
        c_packet = packet("SSH_FXP_RMDIR")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        # waiting on response
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def listdir(self, dir):
        """
        Get the file names of files in a directory.

        :param dir: Directory to crawl. Path is relative to user's ~.
        :return: An array of strings
        """

        filenames = []

        # List directory
        """
        uint32     id
        string     path
        """
        c_packet = packet("SSH_FXP_OPENDIR")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        # waiting on response
        response = self.__recv()
        r_packet = packet(b=response)
        handle = r_packet.get_items()[0]

        # Read filenames from the directory until the directory is exhausted.
        reading = True
        while reading:
            try:
                # Read in filenames
                """
                uint32     id
                string     handle
                """
                c_packet = packet("SSH_FXP_READDIR")
                c_packet.assign_next_id()
                c_packet.add(handle)
                bytes = c_packet.bytes()
                self.__send(bytes)
                # waiting on response
                response = self.__recv()
                r_packet = packet(b=response)

                if r_packet.get_FXP_type() == "SSH_FXP_STATUS":
                    reading = False # Done reading files from folder
                else:
                    items = r_packet.get_items()

                    # Parse out filenames
                    for i in range(1, len(items), 3):
                        filenames.append(items[i])

            except Exception as e:
                print(e)
                reading = False

        # Close the directory.
        """
        uint32     id
        string     handle
        """
        c_packet = packet("SSH_FXP_CLOSE")
        c_packet.assign_next_id()
        c_packet.add(handle)
        bytes = c_packet.bytes()
        self.__send(bytes)
        # waiting on response
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

        return filenames

    def listdir_attr(self, dir):
        """
        Get the attributes of files in a directory.

        :param dir: Directory to crawl. Path is relative to user's ~.
        :return: An array of attributes
        """
        attrs = []

        # Open a directory.
        """
        uint32     id
        string     path
        """
        c_packet = packet("SSH_FXP_OPENDIR")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        # waiting on response
        response = self.__recv()
        r_packet = packet(b=response)
        handle = r_packet.get_items()[0]

        # Read filenames from the directory until the directory is exhausted.
        """
        uint32     id
        string     handle
        """
        reading = True
        while reading:
            try:
                c_packet = packet("SSH_FXP_READDIR")
                c_packet.assign_next_id()
                c_packet.add(handle)
                bytes = c_packet.bytes()
                self.__send(bytes)
                # waiting on response
                response = self.__recv()
                r_packet = packet(b=response)

                if r_packet.get_FXP_type() == "SSH_FXP_STATUS":
                    reading = False # Done reading files from folder
                else:
                    items = r_packet.get_items()

                    # Parse out attributes
                    for i in range(3, len(items), 3):
                        attrs.append(items[i])

            except Exception as e:
                print(e)
                reading = False

        # Close the directory.
        """
        uint32     id
        string     handle
        """
        c_packet = packet("SSH_FXP_CLOSE")
        c_packet.assign_next_id()
        c_packet.add(handle)
        bytes = c_packet.bytes()
        self.__send(bytes)
        # waiting on response
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

        return attrs

    def stat(self, dir):
        """
        Get the attributes of a file, following symbolic links.

        :param dir: File to read attributes of. Path is relative to user's ~.
        :return: An attributes
        """

        # Get file attributes via STAT, which follows symbolic links
        """
        uint32 id
        string path
        """
        c_packet = packet("SSH_FXP_STAT")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        attr = r_packet.get_items()[0]

        return attr

    def lstat(self, dir):
        """
        Get the attributes of a file, NOT following symbolic links.

        :param dir: File to read attributes of. Path is relative to user's ~.
        :return: AN attributes
        """

        # Attempt LSTAT, aka get file attirbutes and do NOT follow smybolic links
        """
        uint32 id
        string path
        """
        c_packet = packet("SSH_FXP_LSTAT")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        attr = r_packet.get_items()[0]

        return attr

    def setstat(self, dir, attr):
        """
        Set the attributes of a file, as defined in the SFTP internet draft 02.

        :param dir: File to set attributes of. Path is relative to user's ~.
        :param attr: The attributes to use.
        :return: None
        """

        # SSH_FXP_SETSTAT
        """
        uint32 id
        string path
        ATTRS attrs
        """
        c_packet = packet("SSH_FXP_SETSTAT")
        c_packet.assign_next_id()
        c_packet.add(dir)
        c_packet.add(attr)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def create_file(self, dir, attr = None):
        """
        Create a file.

        :param dir: Where to create the file. Path is relative to user's ~.
        :param attr: The attributes of a file. Default will create an empty file.
        :return: None
        """

        # Create
        """
        string filename
        uint32 pflags
        ATTRS attrs
        """
        c_packet = packet("SSH_FXP_OPEN")
        c_packet.assign_next_id()
        c_packet.add(dir)
        c_packet.add(c_packet.PFLAG_type_byte("SSH_FXF_CREAT"), 4)
        if attr is None:
            attr = attributes()
        c_packet.add(attr)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)
        handle = r_packet.get_items()[0]

        # Close
        """
        uint32 id
        string handle
        """
        c_packet = packet("SSH_FXP_CLOSE")
        c_packet.assign_next_id()
        c_packet.add(handle)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv() # Read any potential messages.
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def write_file(self, dir, data):
        """
        Write data to a file.

        :param dir: File to write. Path is relative to user's ~.
        :param data: Data to write
        :return: None
        """

        # Open
        """
        string filename
        uint32 pflags
        ATTRS attrs
        """
        c_packet = packet("SSH_FXP_OPEN")
        c_packet.assign_next_id()
        c_packet.add("file_t")
        c_packet.add(c_packet.PFLAG_type_byte("SSH_FXF_WRITE"), 4)
        attr = attributes()
        c_packet.add(attr)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)
        handle = r_packet.get_items()[0]

        # Write
        """
        uint32 id
        string handle
        uint64 offset
        string data
        """
        try:
            c_packet = packet("SSH_FXP_WRITE")
            c_packet.assign_next_id()
            c_packet.add(handle)
            c_packet.add(0, 8)
            c_packet.add(data)
            bytes = c_packet.bytes()
            self.__send(bytes)
            print("waiting on response")
            response = self.__recv()
            packet(b=response)
        except Exception as e:
            print(e)

        # Close
        """
        uint32 id
        string handle
        """
        c_packet = packet("SSH_FXP_CLOSE")
        c_packet.assign_next_id()
        c_packet.add(handle)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def read_file(self, dir, amount, offset=0):
        """
        Read a file.

        :param dir: File to read. Path is relative to user's ~.
        :param amount: The amount to read.
        :param offset: The offset to read from.
        :return: The data read.
        """
        data = ""

        # Open
        """
        string filename
        uint32 pflags
        ATTRS attrs
        """
        c_packet = packet("SSH_FXP_OPEN")
        c_packet.assign_next_id()
        c_packet.add(dir)
        c_packet.add(c_packet.PFLAG_type_byte("SSH_FXF_READ"), 4)
        attr = attributes()
        c_packet.add(attr)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)
        handle = r_packet.get_items()[0]

        # Read
        """
        uint32 id
        string handle
        uint64 offset
        uint32 len
        """
        try:
            c_packet = packet("SSH_FXP_READ")
            c_packet.assign_next_id()
            c_packet.add(handle)
            c_packet.add(offset, 8)
            c_packet.add(amount, 4)
            bytes = c_packet.bytes()
            self.__send(bytes)
            print("waiting on response")
            response = self.__recv()
            r_packet = packet(b=response)

            data = r_packet.get_items()[0]
        except Exception as e:
            print(e)

        # Close
        """
        uint32 id
        string handle
        """
        c_packet = packet("SSH_FXP_CLOSE")
        c_packet.assign_next_id()
        c_packet.add(handle)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

        return data

    def rename(self, dir, new_dir):
        """
        Rename a file or directory.

        :param dir: Move file from here. Path is relative to user's ~.
        :param new_dir: Move file to here. Path is relative to user's ~.
        :return: None
        """

        # Rename
        """
        uint32 id
        string oldpath
        string newpath
        """
        c_packet = packet("SSH_FXP_RENAME")
        c_packet.assign_next_id()
        c_packet.add(dir)
        c_packet.add(new_dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def remove_file(self, dir):
        """
        Remove a file.

        :param dir: File to remove. Path is relative to user's ~.
        :return: None
        """
        # Remove
        """
        uint32 id
        string filename
        """
        c_packet = packet("SSH_FXP_REMOVE")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def symlink(self, dir, link_to):
        """
        Create a symbolic link.

        :param dir: Where to create the symbolic link. Path is relative to user's ~.
        :param link_to: Where to symbolic link to. Path is relative to user's ~.
        :return:
        """
        # SSH_FXP_SYMLINK
        """
        uint32 id
        string linkpath
        string targetpath
        """
        c_packet = packet("SSH_FXP_SYMLINK")
        c_packet.assign_next_id()
        c_packet.add(link_to)
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        # Check for errors
        status_type = r_packet.get_items()[0]
        status_message = r_packet.get_items()[1].lower()
        if status_type != r_packet.FX_type_byte("SSH_FX_OK") and status_message != "success":
            raise Exception(status_message)

    def readlink(self, dir):
        """
        Read a symbolic link.

        :param dir: Symbolic link to read. Path is relative to user's ~.
        :return:
        """

        # SSH_FXP_READLINK
        """
        uint32 id
        string path
        """
        c_packet = packet("SSH_FXP_READLINK")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        return r_packet.get_items()[1]

    def canonicalize(self, dir):
        """
        Canonicalize a path.

        :param dir: Some path.
        :return: The canonicalzed path.
        """

        # SSH_FXP_REALPATH
        """
        uint32 id
        string path
        """
        c_packet = packet("SSH_FXP_REALPATH")
        c_packet.assign_next_id()
        c_packet.add(dir)
        bytes = c_packet.bytes()
        self.__send(bytes)
        print("waiting on response")
        response = self.__recv()
        r_packet = packet(b=response)

        return r_packet.get_items()[1]