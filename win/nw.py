#!/usr/bin/env python
import time
import struct
import socket
import sys
import time
import thread

"""
    Spreading data over the local network
    
    Multicast addresses: 224.0.0.0 - 239.255.255.255

    Default address: 224.2.2.4
"""

CLUSTER_HOSTS = set()

def _ping(timeout=3):
    while 1:
        PORT = 50007              # Arbitrary non-privileged port
        hosts = list(CLUSTER_HOSTS)
        for host in hosts:
            print '> ping ' + host
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((host, PORT))
            
            s.sendall('ping')
            s.settimeout(1)
            try:
                data = s.recv(4)
                s.close()
            except socket.timeout:
                data = None
            if data != 'pong':  
                print 'removing host ' + host
                #CLUSTER_HOSTS.remove(host)
        time.sleep(timeout)
            
def _ping_receiver():
    
    print 'init pong'
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 50007              # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    print 'Connected by', addr
    while 1:
        data = conn.recv(4)
        if data == 'ping':
            print '>pong'
            conn.sendall('pong')
    conn.close()
        
def _send(data,group="224.2.2.4",port=8123,ttl=1):
    addrinfo = socket.getaddrinfo(group, None)[0]

    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Set Time-to-live (optional)
    ttl_bin = struct.pack('@i', ttl)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)

    print 'sent: '+data
    s.sendto(_create_packet('test',data), (addrinfo[4][0], port))
        
def _create_packet(group_name,data):
    header = struct.pack('I',len(group_name))
    packet = header+group_name+data+'\0'
    return packet
    
def _parse_packet(packet):
    header_size = struct.calcsize('I')
    header = packet[:header_size] 
    data = packet[header_size:]
    if data[-1] != '\0':
        raise Exception('Packet is bigger then 16kb')
    group_name_size = struct.unpack('I',header)[0]
    group_name = data[:group_name_size]
    data = data[group_name_size:-1]
    return group_name,data
      
def _receive(group="224.2.2.4",port=8123,ttl=1):
    # Look up multicast group address in name server and find out IP version
    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create a socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        pass # Some systems don't support SO_REUSEPORT
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, ttl)
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
    
    # Bind it to the port
    s.bind(('', port))

    group_bin = socket.inet_aton(addrinfo[4][0])
    # Join group
    mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    # Loop, printing any data we receive

    while True:
        packet, sender = s.recvfrom(16384) #16kb
        cluster_name,data = _parse_packet(packet)
        yield sender,cluster_name,data
    

def discovery(cluster_name="test"):
    _send('hello')
    for packet in _receive():
        sender,cluster_name_in,data = packet
        print 'received from: %s' % sender[0]
        if cluster_name != cluster_name_in:
            continue
        if data == 'hello':
            print 'got hello'
            _send('imhere')
            CLUSTER_HOSTS.add(sender[0])
        elif data == 'imhere':
            print 'got im here'
            CLUSTER_HOSTS.add(sender[0])
        elif data == 'pong':
            print 'got im here'
            CLUSTER_HOSTS.add(sender[0])
        print CLUSTER_HOSTS

        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        _send(' '.join(sys.argv[1:]))
    else:
        try:
            thread.start_new_thread(discovery,tuple())
            thread.start_new_thread(_ping_receiver,tuple())
            thread.start_new_thread(_ping,(3,))
            while 1:
                time.sleep(1)
        except Exception as e:
            import traceback
            print traceback.print_exc()
            print e
            time.sleep(5)
                