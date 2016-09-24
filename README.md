# SFTP3
A SFTP v3 client, as defined by the SFTP internet draft 02.

# Building
`git clone --recursive https://github.com/Choco31415/SFTP3.git`

# Running

## Example
`python Client.py`

Client.py is currently set up to test and showcase SFTP methods.

Please note that you will need to edit Client.py to run it in a meaningful manner. You will need to:

  * Edit variables IP, username, key_filename, and password to reflect a valid login on a remote machine. Either password or keyfilename is fine.
  * Ensure that the file location contained in variable test_file exists.
  * Ensure that the path contained in variable weird_directory is valid.

## Writing Code

When writing your own SFTP code, you will need to put everything in the following format:

```
s = SFTP_client(IP, username, password=password, key_filename=key_filename)
s.open_sftp_channel(max_packet_size=2048)

<FTP code here>

s.close()
```

With comments:

```
# Create the SFTP_client object with these parameters.
# Password or key_filename is required, but not both.
# This only sets up a standard SSH connection.
s = SFTP_client(IP, username, password=password, key_filename=key_filename)
# Connect to sftp subsystem and negotiate sftp versions.
s.open_sftp_channel(max_packet_size=2048)

<FTP code here>

# Close the sftp connection, freeing it for future usage.
s.close()
```

All FTP methods may be found in FTP_client in FTP_Client.py.

Also, please note that any method calls that the server reports as invalid will cause exceptions in the Python code. As such, it is good practice to wrap the FTP code in a try-except statement.

# Project Tree
Attributes

  * Contains the attributes class, a compound data type used for encoding file attributes.

Client

  * A test of the SFTP3 implementation.

File_Utils

  * Miscalleneous file I/O methods.

Packet

  * Contains packet, a request/response data class.

SFTP_Client

  * The user frontend. It contains all SFTP methods that the user should use, like create and remove directory.

SSH_Client

  * A paramiko SSH implementation.