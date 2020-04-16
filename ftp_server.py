"""
ftp 服务器
多线程并发和
"""
import time
from socket import *
from threading import Thread
import os

HOST = "127.0.0.1"
PORT = 9001
ADDR = (HOST, PORT)
FTP = "/home/tarena/ftpHub/"  # 代表文件库


# 应对客户端请求
class FTPServer(Thread):
    def __init__(self, connfd):
        super().__init__()
        self.connfd = connfd

    def run(self):
        while True:
            data = self.connfd.recv(1024).decode()  # 接收客户端请求指令
            data = data.split(" ")  # [G,filename]
            # 分情况讨论
            if not data or data[0] == "Q":
                self.do_quit()
            if data[0] == "L":
                self.do_list()
            elif data[0] == "G":
                self.get_file(data[1])
            elif data[0] == "P":
                self.put_file(data[1])

    def do_list(self):
        # 判断文件库是否为空
        file_list = os.listdir(FTP)
        if not file_list:
            self.connfd.send(b"NO")
            return
        else:
            self.connfd.send(b"YES")
            # 将文件列表发送给客户端
            # 问题1:如何发送文件列表给客户端
            # 问题2:粘包如何解决
            time.sleep(0.1)
            data = "\n".join(file_list)
            self.connfd.send(data.encode())

    def get_file(self, filename):
        try:
            # 获取文件
            f = open(FTP + filename, "rb")
        except:
            # 文件不存在
            self.connfd.send(b"NO")
            return
        else:
            self.connfd.send(b"YES")
            # 处理文件的发送
            time.sleep(0.1)  # 防止粘包
            while True:
                data = f.read(1024)
                if not data:
                    time.sleep(0.1)
                    self.connfd.send(b"##")
                    break
                self.connfd.send(data)
            f.close()

    def put_file(self, filename):
        if os.path.exists(FTP + filename):
            self.connfd.send(b"NO")  # 文件已经存在,不允许上传
            return
        else:
            self.connfd.send(b"YES")  # 文件不存在,允许上传
            # 接收文件
            f = open(FTP + filename, "wb")
            while True:
                data = self.connfd.recv(1024)
                if data == b"##":
                    break
                f.write(data)
            f.close()

    def do_quit(self):
        return  # 函数退出表示进程结束


# 网络并发结构搭建
def main():
    sockfd = socket()
    sockfd.bind(ADDR)
    sockfd.listen(3)
    print("等待客户端链接......")

    while True:
        try:
            connfd, addr = sockfd.accept()
            print("链接到客户端", addr)
        except:
            print("服务结束")
        else:
            t = FTPServer(connfd)
            t.setDaemon(True)  # 主服务退出,其他服务也随之退出
            t.start()


if __name__ == '__main__':
    main()
