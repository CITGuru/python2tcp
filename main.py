import os
import click
from TCPClient1 import Sender
from TCPServer1 import Reciever
from TCPHeader import TCPPacket
import socket


host = ""
port = 61115

def checkPathExist(path):
    directory = os.path.dirname(path)
    if os.path.exists(directory) or directory=="":
        return True
    return False

@click.group()
def main():
    """CLI to send files with go-back-N and TCP in Python"""
    pass

@main.command()
@click.option('--f', '--filename', required=True, help="Path to the file you want to send")
@click.option('--host', required=False, help="The host you want to send to")
@click.option('--p','--port', required=False, help="The port you are sending to", type=click.INT)
@click.option('--w','--win', required=True, help="The size of the window", type=click.INT)
@click.option('--n', '--numpac',required=True, help="The number of packets per window", type=click.INT)
@click.option('--t','--time', required=True, help="Time out", type=click.FLOAT)
def send(**kwargs):
    """Send files from go-back-N\n

        Example:

        Send\n
        python main.py send --f <path-to-file> --w 200 --n 200 --t 200 --p 24414

        Recieve\n
        python main.py recieve --f <file-to-save-to> --p 24414

    
    """
    win = kwargs["win"]
    time = kwargs["time"]
    numpac = kwargs["numpac"]
    filename = kwargs["filename"]

    if not checkPathExist(filename):
        raise Exception("Path does not exists")

    server = Sender(int(win), float(time), int(numpac), filename)
    global host, port

    if kwargs.get("host"):
        host = kwargs["host"]
    
    if kwargs.get("port"):
        port = int(kwargs["port"])

    server.soc.bind((host, port))
    server.soc.listen(5)
    conn, addr = server.soc.accept()
    data = conn.recv(1024)
    click.echo("Recieved connection")
    message = "{}/////{}/////{}".format(win,str(time),filename)
    conn.send(message.encode("utf-8"))
    tcp = TCPPacket()
    tcp.assemble_tcp_feilds()
    conn.send(tcp.raw)
    conn.close()
    server.soc.settimeout(5)
    conn, addr = server.soc.accept()
    data = conn.recv(1024)
    server.run(conn)
    conn.close()


@main.command()
@click.option('--f', '--filename', required=False, help="Path to the file you want to send")
@click.option('--host', required=False, help="The host you want to send to")
@click.option('--p','--port', required=False, help="The port you are sending to", type=click.INT)
def recieve(**kwargs):
    """Recieve files from go-back-N"""
    global host, port

    if kwargs.get("host"):
        host = kwargs["host"]
    
    if kwargs.get("port"):
        port = int(kwargs["port"])
        
    s = socket.socket()
    s.connect((host, port))
    s.send("Hello Server")
    mess = s.recv(1024)
    args = mess.split("/////")
    s.close()
    filename = args[2]
    if kwargs.get("filename"):
        filename = kwargs["filename"]
        if not checkPathExist(filename):
            raise Exception("Path does not exists")
    
    client = Reciever(int(args[0]), float(args[1]), filename)
    click.echo("recieved arguments")
    client.soc.connect((host, port))
    client.soc.send("Hello server")
    client.recieve()
    client.soc.close()

if __name__ == "__main__":
    main()