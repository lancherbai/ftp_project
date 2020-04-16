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
