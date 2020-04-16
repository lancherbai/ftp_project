ftp 文件服务器


【1】 分为服务端和客户端，要求可以有多个客户端同时操作。
【2】 客户端可以查看服务器文件库中有什么文件。
【3】 客户端可以从文件库中下载文件到本地。
【4】 客户端可以上传一个本地文件到文件库。
【5】 使用print在客户端打印命令输入提示，引导操作

```python
1.技术分析
    *并发模型：多进程   多线程
    *网络传输方法：tcp

2.功能分析    (封装模型:类)
    搭建网络架构

    查看文件列表
    上传文件
    下载文件
    退出

3.通信协议设计
                请求类型    请求参量
    查看文件列表     L
    上传文件        P
    下载文件        G       filename
    退出            Q
            服务端YES表示允许,NO表示不允许

4.分析具体功能
    搭建网络架构
    查看文件列表
            客户端:
                1.发送请求给服务端
                2.等待服务端回复,确认是否可以查看
                3.YES开始接收文件列表
                4.NO --> 结束
            服务端:
                1.接收请求,进行初步处理
                2.根据情况给客户端回复(YES NO)
                3.YES将文件列表发送到服务端

    上传文件
    下载文件
    退出

5.细节的处理和完善



知识点总结：
    tcp链接
    多线程
    协议
    三段式应答机制
    总分结构
```

```python
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
```

```python
"""
ftp 客户端
c/s模式   发送请求 获取结果
"""
import sys
import time
from socket import *
from threading import Thread

SERVER_ADDR = ("127.0.0.1", 9001)


class FTPClient():
    def __init__(self, sockfd):
        self.sockfd = sockfd

    def do_list(self):
        self.sockfd.send(b"L")  # 发送请求
        # 等待回复 YES NO
        data = self.sockfd.recv(128).decode()
        # print(data)
        if data == "YES":
            # 接收文件列表
            # 问题:选择一次性传输时,先声明大小;分次发送时需在末尾添加消息边界
            data = self.sockfd.recv(4096)
            print(data.decode())
        else:
            print("获取文件列表失败")

    # 下载文件
    def get_file(self, filename):
        self.sockfd.send(("G " + filename).encode())  # 发送请求
        # 等待回复 YES NO
        data = self.sockfd.recv(128).decode()
        if data == "YES":
            f = open(filename, "wb")
            while True:
                data = self.sockfd.recv(1024)
                # 问题:怎么结束接收文件?一种用sleep,一种是接收特殊标记
                if data == b"##":
                    break
                f.write(data)
            f.close()
        else:
            print("未找到该文件")

    def put_file(self, filename):
        # 文件路径去除
        filename = filename.split("/")[-1]
        try:
            f = open(filename, "rb")
        except:
            print("要上传的文件不存在")
            return
        else:
            self.sockfd.send(("P " + filename).encode())  # 发送请求
            # 等待回复 YES NO
            data = self.sockfd.recv(128).decode()
            if data == "YES":  # 表示允许上传
                while True:
                    data = f.read(1024)
                    if not data:
                        time.sleep(0.1)
                        self.sockfd.send(b"##")
                        break
                    self.sockfd.send(data)
                f.close()
            else:
                print("FTP已有同名文件!")

    def do_quit(self):
        self.sockfd.send("Q ".encode())
        self.sockfd.close()
        sys.exit("谢谢使用!")  # 退出进程


# 链接服务端
def main():
    sockfd = socket()
    sockfd.connect(SERVER_ADDR)
    # 实例化对象
    ftp = FTPClient(sockfd)

    while True:
        print("==============   命令选项  ==============")
        print("==============    list    ==============")
        print("==============  get file  ==============")
        print("==============  put file  ==============")
        print("==============    quit    ==============")
        cmd = input("请输入选项:")

        cmd = cmd.split(" ")

        if cmd[0] == "list":
            ftp.do_list()
        elif cmd[0] == "get":
            ftp.get_file(cmd[1])
        elif cmd[0] == "put":
            ftp.put_file(cmd[1])
        elif cmd[0] == "quit":
            ftp.do_quit()
        else:
            print("输入有误!")


if __name__ == '__main__':
    main()
```

