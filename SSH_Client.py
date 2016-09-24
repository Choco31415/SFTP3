# Handle imports
import paramiko.paramiko as paramiko

# Create classes
class SSH():
    """
    Paramiko SSH implementation
    """

    def __init__(self, IP, username, password = None, key_filename = None):
        """
        Either password or key_filename is required.

        :param IP: The IP of the remote machine.
        :param username: The username of a user on the remote machine.
        :param password: The password of a user on a remote machine.
        :param key_filename: The key_filename on a remote machine.
        """
        assert not ((password is None) and (key_filename is None)), "Please provide a password or key_filename."

        self.IP = IP

        self.max_packet_size = 1024

        # Start parakimo for commands
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())

        if password is None:
            self.ssh.connect(self.IP, username=username, key_filename=key_filename, port=22)
        else:
            self.ssh.connect(self.IP, username=username, password=password, port=22)

    def pipe_command(self, cmd):
        """
        Run a command, cmd, on the server.
        """
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        data = stdout.read().splitlines()

        output = ""
        for line in data:
            output += line.decode("utf-8")

        return output

    def stop(self):
        self.ssh.close()