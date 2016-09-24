"""
A test of SFTP_client.

It is assumed that both the file test_file and weird_directory exist.
"""
# Handle imports
from SFTP_Client import SFTP_client
from Attributes import attributes

# Global vars
IP = "Some_IP"
username = "Some_SSH_user"
key_filename = "key"
password = None

test_file = "rock"
weird_directory = "~/../sftp/test/../rock"

# Start an SFTP connection
s = SFTP_client(IP, username=username, password=password, key_filename=key_filename)
print("ls: " + s.pipe_command("ls")) # Unnecessary, but nice for checking the network connection.

# Test our SFTP project
print("\nInitialization\n")

s.open_sftp_channel(max_packet_size=2048)

print("\nDirectories\n")

s.create_dir("temp_dir")
s.remove_dir("temp_dir")
s.listdir(".")
s.listdir_attr(".")

print("\nFiles\n")

s.create_file("file_t")
s.write_file("file_t", "Taco")
s.read_file("file_t", 1000000)
s.rename("file_t", "file_r")
s.remove_file("file_r")

print("\nStat\n")

s.stat("test")
s.lstat("test")
s.setstat(test_file, attributes(size=1000))

print("\nSymbolic Links\n")

s.symlink("pier", test_file)
s.readlink("pier")
s.remove_file("pier")

print("\nCanonicalization\n")

s.canonicalize(weird_directory)

s.stop()