import socket

BROADCAST_IP = "255.255.255.255"
DEFAULT_PORT = 9


def create_magic_packet(macaddress: str) -> bytes:
    """
    Create a magic packet.
    A magic packet is a packet that can be used with the for wake on lan
    protocol to wake up a computer. The packet is constructed from the
    mac address given as a parameter.
    Args:
        macaddress: the mac address that should be parsed into a magic packet.
    """
    if len(macaddress) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, "")
    if len(macaddress) != 12:
        raise ValueError("Incorrect MAC address format")

    return bytes.fromhex("F" * 12 + macaddress * 16)


def send_magic_packet(mac: str, ip_address: str = BROADCAST_IP, port: int = DEFAULT_PORT) -> None:
    """
    Wake up computers having any of the given mac addresses.
    Wake on lan must be enabled on the host device.
    Args:
        macs: Macaddress of machine to wake.
    Keyword Args:
        ip_address: the ip address of the host to send the magic packet to.
        port: the port of the host to send the magic packet to.
    """
    packet = create_magic_packet(mac)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((ip_address, port))
        sock.send(packet)
