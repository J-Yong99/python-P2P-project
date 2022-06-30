from ipaddress import ip_address
from socket import *
import threading
import sys
lock = threading.Lock()

global mailNumber
global onOff
mailNumber = 0
ip_address = 'localhost'
connectionList = {} #dict{"id":("ip", address)}
mailBox = []


#server는 클라이언트가 보낸 송신을 수신하고 
class Jserver:
    def __init__(self, mPort, userID, userName):
        #초기화
        self.userID = userID
        self.mPort = mPort
        self.userName = userName
        sThread = threading.Thread(target = self.serverRun, args = ())
        sThread.daemon = True
        sThread.start()
        # print("The server is ready to receive")
        
    def serverRun(self):
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.bind((ip_address, self.mPort))
        serverSocket.listen(100)
        while True:
            connectionSocket, addr = serverSocket.accept()
            ssThread = threading.Thread(target = self.handleClient, args = (connectionSocket, addr))
            ssThread.daemon = True
            ssThread.start()
            # print(f"new connection : {addr[1]}")
            
    def handleClient(self, connectionSocket, addr):
            clientMessage = connectionSocket.recv(10000).decode().split()
            print("SERVER -> client message recieved : ",clientMessage)
            #handle connection message
            if clientMessage[0] == "CONNECT":
                if clientMessage[4] not in connectionList.keys():
                    lock.acquire()
                    connectionList[clientMessage[4]] = (clientMessage[2], int(clientMessage[3]))
                    print(connectionList)
                    lock.release()
                    # print(f"SERVER -> CONNECT successfully established with port:{clientMessage[3]}")
                    sendmessage = (f"@connect {clientMessage[2]} {int(clientMessage[3])}")
                    sendmessage = list(sendmessage.split())
                    client = Jclient(self.userID, self.mPort, sendmessage)
            #handle query message
            #QUERY {dID} {mailNumber} from {self.userID}
            elif clientMessage[0] == "QUERY":
                if f"{clientMessage[4]}{clientMessage[2]}" not in mailBox:
                    lock.acquire()
                    mailBox.append(f"{clientMessage[4]}{clientMessage[2]}")
                    lock.release()
                    #내가 대상일 때
                    if self.userID == clientMessage[1]:
                        print("it's me")
                        command = f"@response {clientMessage[4]} {self.userID} {self.userName} {ip_address} {self.mPort} {len(clientMessage) - 4}".split()
                        for i in clientMessage[4:]:
                            command.append(i)
                        client = Jclient(self.userID, self.mPort, command)
                    elif self.userID not in clientMessage:
                        for i in connectionList.keys():
                            # print(clientMessage[3:],i)
                            # if str(i) not in clientMessage[3:]:
                                # print(f"SERVER -> QUERY successfully received from id:{clientMessage[-1]} ",clientMessage)
                                sendSentence = clientMessage[::]
                                sendSentence.append(self.userID)
                                sendSentence.append(i)
                                sendSentence = " ".join(sendSentence)#split,join
                                # print("sendsentece is ", sendSentence, " to ", i)
                                command = f"@query {clientMessage[1]}".split()
                                sssThread = threading.Thread(target = self.callClient, args = (command, sendSentence, ))
                                sssThread.daemon = True
                                sssThread.start()                            
                            

            elif clientMessage[0] == "@response":
                if clientMessage[1] == self.userID:
                    print(f"PeerInfo src {clientMessage[1]} target {clientMessage[2]} name {clientMessage[3]} IP {clientMessage[4]} port {clientMessage[5]} hop {clientMessage[6]}")
                else:
                    client = Jclient(self.userID, self.mPort, clientMessage)
        
            connectionSocket.close()
    def callClient(self, command, sendSentence):
        client = Jclient(self.userID, self.mPort, command, queryMessage = sendSentence)
            
#client는 송신의 역할만 한다.
class Jclient:
    def __init__(self, userID, mPort, command, queryMessage = None): 
        #초기화
        global mailNumber
        global onOff
        self.userID = userID
        self.mPort = mPort
        self.command = command
        print("CLIENT -> command is ",self.command,f" {queryMessage}")
        #connect message 송신 쓰레드 생성
        if command[0] == "@connect":
            serverName = command[1]
            dPort = int(command[2])
            #자기 자신을 향한 connect message는 무시
            if serverName == ip_address and dPort == mPort:
                return
            else:
                clientSocket = socket(AF_INET, SOCK_STREAM)
                try:
                    clientSocket.connect((serverName, dPort))
                    # print(f"CLIENT -> connection successfully established with port:{dPort}")
                except:
                    print("fail")

                cThread = threading.Thread(target = self.connectMessage, args=(clientSocket, serverName, ))#소켓을 연결한 뒤에는 쓰레드를 나눠서 메세지 보내기
                cThread.daemon = True
                cThread.start()
        #현재 연결된 리스트들 확인
        elif command[0] == "@list":
            print(connectionList) 
        #query message 송신 쓰레드 생성
        elif command[0] == "@query":
            #처음 query문을 보낼때
            dID = command[1]
            #서버에서 query문을 보낼때
            if queryMessage is not None:
                serverName = connectionList[queryMessage.split()[-1]][0]
                dPort = connectionList[queryMessage.split()[-1]][1]
                queryMessage = queryMessage.split()[:-1]
                queryMessage = " ".join(queryMessage)
                clientSocket = socket(AF_INET, SOCK_STREAM)
                try:
                    clientSocket.connect((serverName, dPort))
                    # print(f"CLIENT -> query successfully send to port:{dPort}")
                except:
                    print("fail") 
                cThread = threading.Thread(target = self.queryMessage, kwargs ={"clientSocket":clientSocket, "queryMessage":queryMessage})
                cThread.daemon = True
                cThread.start()            
            else:
                lock.acquire()
                mailNumber += 1
                lock.release()
                for i in connectionList.keys():
                    lock.acquire()
                    serverName = connectionList[i][0]
                    dPort = int(connectionList[i][1])
                    lock.release()
                    # 자기 자신을 향한 ₩query message 무시
                    if serverName == ip_address and dPort == mPort:
                        return
                    else:
                        clientSocket = socket(AF_INET, SOCK_STREAM)
                        try:
                            clientSocket.connect((serverName, dPort))
                            # print(f"CLIENT -> query successfully send to port:{dPort}")
                        except:
                            print("fail") 
                        cThread = threading.Thread(target = self.queryMessage, kwargs ={"clientSocket":clientSocket, "dID":dID})
                        cThread.daemon = True
                        cThread.start()   
        #query response message   
        #"@response {clientMessage[4]} {self.userID} {self.userName} {ip_address} {self.mPort} {len(clientMessage) - 4}"
        elif command[0] == "@response":
            serverName = connectionList[command[-1]][0]
            dPort = int(connectionList[command[-1]][1])
            clientSocket = socket(AF_INET, SOCK_STREAM)
            try:
                clientSocket.connect((serverName, dPort))
                # print(f"CLIENT -> response message successfully send to port:{dPort}")
            except:
                print("fail")

            cThread = threading.Thread(target = self.responseMessage, args=(clientSocket, command, ))#소켓을 연결한 뒤에는 쓰레드를 나눠서 메세지 보내기
            cThread.daemon = True
            cThread.start()
        elif command[0] == "@quit":
            lock.acquire()
            onOff = False
            lock.release()

        else:
            print("Invalid command")
    
    def connectMessage(self, clientSocket, serverName): 
        sentence = (f"CONNECT from {ip_address} {self.mPort} {self.userID}")
        clientSocket.send(sentence.encode())
        clientSocket.close()

    def queryMessage(self, clientSocket = None , dID = None, queryMessage = None): 
        if dID is not None:
            global mailNumber
            sentence = (f"QUERY {dID} {mailNumber} from {self.userID}")
            print("CLIENT -> ",sentence)
            clientSocket.send(sentence.encode())
            
        elif queryMessage is not None:
            print("CLIENT -> ", queryMessage)
            clientSocket.send(queryMessage.encode())
        clientSocket.close()

    def responseMessage(self, clientSocket, command): 
        command = command[:-1]
        command = " ".join(command)
        clientSocket.send(command.encode())
        clientSocket.close()
            
    
        
        
            

def main(argv):
    #초기화
    global onOff
    onOff = True
    userID = argv[2]
    serverPort = int(argv[1])
    userName = argv[3]
    
    print(f"Student ID : 20182213")
    print(f"Name : Kim JaeYong")
    #서버 백그라운드 구동
    server = Jserver(serverPort, userID, userName)
    #메인함수에서 계속 입력받으면서 클라이언트를 호출해서 송신
    while onOff:
        command = list(input(f"{userID}>\n").split())
        client = Jclient(userID, serverPort, command)

main(sys.argv)