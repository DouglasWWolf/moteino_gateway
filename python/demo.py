import moteinogw
import struct
from timeit import default_timer as timer

# ==========================================================================================================
# echo_test() - Transmits / receives a large number of packets across the serial interface
#
# Measures the round-trip time, then examines each queued up packet to ensure that it matches
# the original packet that was sent
# ==========================================================================================================
def echo_test():
    count = 1000
    start = timer()
    for n in range(0, count):
        packet = n.to_bytes(4, 'big') + b'abcdefghijklmnopqrstuvwxyz'
        if not gw.echo(packet):
            print("Failed to transmit packet", n)
            quit()
    end = timer()
    print("Round trip for", count, "packets took", end - start, "seconds")

    print("Checking data integrity")
    confirmed = True
    for n in range(0, count):
        packet = gw.wait_for_message(5)
        expected = n.to_bytes(4, 'big') + b'abcdefghijklmnopqrstuvwxyz'

        if isinstance(packet, moteinogw.EchoPacket):
            if packet.payload != expected:
                print("Fault on packet", n)
                print("Expected: ", expected)
                print("Received: ", packet.payload)
                confirmed = False
        elif isinstance(packet, moteinogw.BadPacket):
            print("CRC Mismatch on packet", n)
            print("Expected: ", expected)
            print("Received: ", packet.payload)
            confirmed = False
        else:
            print("Unknown packet type!")
            print("Packet contents:", packet)
            confirmed = False

    if confirmed:
        print("Data integrity confirmed")
    else:
        print("Data corruption detected!")
# ==========================================================================================================


if __name__ == '__main__':
    gw = moteinogw.MoteinoGateway()
    gw.startup('COM11')

    # Wait for the packet that tells us the gateway is alive
    packet = gw.wait_for_message()

    '''
    # Serial-interface throughput test
    print("Starting serial throughput test")
    for n in range(0, 1000):
        print("Echo Test #"+str(n+1))
        echo_test()
    quit()
    '''

    # Initialize the radio: 915 Mhz, Node ID 1, Network ID 100
    gw.init_radio(915, 1, 100)

    # Set the encryption key
    gw.set_encryption_key(b'1234123412341234')

    print("Initialized!")

    radio_format = '<BBBHH'
    radio_size   = struct.calcsize(radio_format)

    # Sit in a loop, displaying incoming radio packets and occasionally replying to one
    counter = 0
    response_id = 0
    while True:
        packet = gw.wait_for_message()
        if isinstance(packet, moteinogw.RadioPacket):
            print("[rssi", packet.rssi,"] From node", packet.src_node, "to node", packet.dst_node)
            version, temp, setpoint, battery, pwm = struct.unpack('<BBBHH', packet.data[:radio_size])
            print("    Version   = ", version)
            print("    Temp (F)  = ", temp)
            print("    Setpoint  = ", setpoint)
            print("    Battery   = ", battery)
            print("    Servo PWM = ", pwm)

            counter = counter + 1
            if counter % 1 == 0:
                response_id = response_id + 1
                response = 'I see you %i' % (response_id)
                gw.send_radio_packet(packet.src_node, bytes(response, 'utf-8'))

