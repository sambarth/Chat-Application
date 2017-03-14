import sys
import socket
import select
import struct
import time

'''
The following program was tested for the following operating systems:
    * LINUX

Note that dirservice will need to be running prior to running chat.py
To run chat.py from the command line, pass it the following arguments:
    * the user id of the host
    * the ip address and port number of the host in the form "ip-address:port-number"
    * the user id of the client to which the host would like to chat
    * the ip address and port number of the directory in the form "ip-address:port-number"
'''

# The following method was provided by the course instructor
def encode_message(seqnum, UID, DID, msg, version=150):
    header_buf = bytearray(36)
    UID = UID + ' ' * (16 - len(UID))
    DID = DID + ' ' * (16 - len(DID))
    header_buf = struct.pack('!HH16s16s', version, seqnum, UID.encode('utf-8'), DID.encode('utf-8'))
    header_buf = header_buf + msg.encode('utf-8')
    return header_buf

# The following method was provided by the course instructor
def decode_message(msg_buf):
    tuple = struct.unpack('!HH16s16s', msg_buf[:36])
    (version, seqnum, UID, DID) = tuple
    UID = UID.decode('utf-8')
    UID = UID.split(' ', 1)[0]
    DID = DID.decode('utf-8')
    DID = DID.split(' ', 1)[0]
    msg = msg_buf[36:].decode('utf-8')
    return (seqnum, UID, DID, msg)


def encode_directory_request(UID, ip_and_port, DID):
    header_buf = bytearray(48)
    UID = UID + ' ' * (16 - len(UID))
    ip_and_port = ip_and_port + ' ' * (16 - len(ip_and_port))
    DID = DID + ' ' * (16 - len(DID))
    header_buf = struct.pack('!16s16s16s', UID.encode('utf-8'), ip_and_port.encode('utf-8'), DID.encode('utf-8'))
    return header_buf


def decode_directory_response(msg_buf):
    tuple = struct.unpack('!H16s', msg_buf[:18])
    (err_code, destination_address) = tuple
    destination_address = destination_address.decode('utf-8')
    return (err_code, destination_address)

def main():

    args = sys.argv
    user_id, raw_address, destination_user_id, raw_address_directory_service = args[1], args[2], args[3], args[4]
    server_address = raw_address.split(':', 1)
    server_address[1] = int(server_address[1])
    server_address = tuple(server_address)
    directory_address = raw_address_directory_service.split(':', 1)
    directory_address[1] = int(directory_address[1])
    directory_address = tuple(directory_address)
    destination_address = ''

    sock = socket.create_connection(directory_address)
    try:
        directory_miss = True
        while directory_miss:
            message = encode_directory_request(user_id, raw_address, destination_user_id)
            print('>> ', 'sending request to directory')
            sock.sendall(message)
            print('>> ', 'sent request to directory')
            data = sock.recv(4096)
            err_code, destination_address = decode_directory_response(data)
            if err_code == 400:
                destination_address = destination_address.split(':', 1)
                destination_address[1] = int(destination_address[1])
                destination_address = tuple(destination_address)
                directory_miss = False
            else:
                print('>> ', 'waiting to try again...')
                time.sleep(5)

    finally:
        print('>> ', 'closing socket')
        sock.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)

    try:
        seqnum = 0
        while True:

            print(user_id, ' >> ', end='', flush=True)
            rlist, wlist, elist = select.select([sock, sys.stdin], [], [])
            #print('Select completed', rlist, wlist, elist)

            if sys.stdin in rlist:
                message = encode_message(seqnum, user_id, destination_user_id, input())
                seqnum += 1
                print('sending message')
                sent = sock.sendto(message, destination_address)

            if sock in rlist:
                data, server = sock.recvfrom(4096)
                print('\n', 'they say',' >> ', decode_message(data)[3])

    finally:
        print('closing socket')
        sock.close()

if __name__ == '__main__':
    main()