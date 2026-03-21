from time import sleep

from wxautox import WeChat


def main():
    # 1. 先确保 Windows 微信已登录，并停留在主界面
    wx = WeChat(language="cn")

    # 2. 查看当前会话列表
    sessions = wx.GetSessionList()
    print("当前会话：", list(sessions.keys())[:10])

    # 3. 打开某个聊天窗口
    target = "文件传输助手"
    chat_name = wx.ChatWith(target, exact=False)
    print("已打开聊天：", chat_name)

    # 4. 发送文本消息
    result = wx.SendMsg("这是一条 wxautox 测试消息", who=target)
    print("发送结果：", result)

    # 5. 读取当前窗口已加载的消息
    messages = wx.GetAllMessage()
    print("最近消息条数：", len(messages))
    for item in messages[-5:]:
        print(item)

    # 6. 监听新消息
    wx.AddListenChat(target)
    print("开始监听 10 秒...")
    for _ in range(10):
        sleep(1)
        new_msgs = wx.GetListenMessage()
        if new_msgs:
            print("收到新消息：", new_msgs)
            break
    else:
        print("10 秒内没有新消息")


if __name__ == "__main__":
    main()
