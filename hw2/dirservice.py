import sys
import socket
import struct
import _thread

'''
The following program was tested for the following operating systems:
    * LINUX

Run dirservice.py before running the chat client
dirservice.py takes the following command line argument:
    * ip address and port number on which the server will listen in the form "ip-address:port-number"

An accreditation of sources:
https://pymotw.com/2/socket/udp.html
http://www.diveintopython.net/scripts_and_streams/command_line_arguments.html
http://www.binarytides.com/python-socket-server-code-example/
'''

def encode_message_dict_hit(destination_ip_and_port, error_code = 400):
    header_buf = bytearray(18)
    destination_ip_and_port = destination_ip_and_port + ' ' * (16 - len(destination_ip_and_port))
    header_buf = struct.pack('!H16s', error_code, destination_ip_and_port.encode('utf-8'))
    return header_buf

def encode_message_dict_miss(error_code = 600):
    header_buf = bytearray(18)
    destination_ip_and_port = ' ' * (16)
    header_buf = struct.pack('!H16s', error_code, destination_ip_and_port.encode('utf-8'))
    return header_buf

def decode_message(msg_buf):
    tuple = struct.unpack('!16s16s16s', msg_buf[:48])
    (UID, ip_and_port, DID) = tuple
    UID = UID.decode('utf-8')
    UID = UID.split(' ', 1)[0]
    DID = DID.decode('utf-8')
    DID = DID.split(' ', 1)[0]
    ip_and_port = ip_and_port.decode('utf-8')
    return (UID, DID, ip_and_port)

def main():
    # Directory dictionary will return IP:Port when queried with user-id key
    directory = {}

    args = sys.argv

    server_address = args[1].split(':')
    server_address[1] = int(server_address[1])
    server_address = tuple(server_address)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)
    sock.listen(10)

    # The multi-treading code between the comments is an adaptation of the method found here:
    #  http://www.binarytides.com/python-socket-server-code-example/ by user "Silver Moon"
    def clientthread(conn):

        while True:

            try:
                data = conn.recv(4096)
                (UID, DID, ip_port) = decode_message(data)
                print('>> ', 'received directory request from: ', UID)
                # If look up was a hit
                if DID in directory:
                    # Add user to directory
                    directory[UID] = ip_port
                    # And reply to the client
                    print('>>', 'sending data back to the client')
                    message = encode_message_dict_hit(directory[DID])
                    conn.sendall(message)

                else:
                    # Add user to directory
                    directory[UID] = ip_port
                    # DID is not in the directory, so we'll need to let client know lookup was a miss
                    print('>>', 'could not find ', DID, ' in directory')
                    message = encode_message_dict_miss()
                    conn.sendall(message)

            except:
                # Clean up the connection
                print('>> ', 'client closed the connection')
                conn.close()
                break

        conn.close()

    while True:
        print('>> ', 'waiting for connections')
        conn, addr = sock.accept()
        print('>> ', 'connected to client: ', addr)

        _thread.start_new_thread(clientthread, (conn,))
    # Comment

if __name__ == '__main__':
    main()