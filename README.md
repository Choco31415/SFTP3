# SFTP3
An SFTP v3 client, as defined by the SFTP internet draft 02.

# Building
`git clone --recursive https://github.com/Choco31415/SFTP3.git`

# Running
`python Client.py`

Please note that you will need to edit Client.py to run it in a meaningful manner. You will need to:

  * Edit variables IP, username, key_filename, and password to reflect a valid login on a remote machine. Either password or keyfilename is fine.
  * Ensure that the file location contained in variable test_file exists.
  * Ensure that the directory contained in variable weird_directory exists.

Client.py is currently set up to test and showcase all methods of SFTP_Client.py.

# Project Tree
Attributes

  * A compound data type used for encoding file attributes.

Client

  * A test of the SFTP3 implementation.

File_Utils

  * Miscalleneous file I/O methods.

Packet

  * A request/response data class.

SFTP_Client

  * The user frontend. It contains SFTP methods, like creating and deleting directories.

SSH_Client

  * A paramiko SSH implementation.