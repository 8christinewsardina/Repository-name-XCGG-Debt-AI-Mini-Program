import os


def run():
    try:
        import pinecone
    except Exception:
        print('pinecone-client 未安装。若需要，请运行: pip install pinecone-client')
        return

    api_key = os.getenv('PINECONE_API_KEY')
    env = os.getenv('PINECONE_ENV')
    index = os.getenv('PINECONE_INDEX')
    if not api_key or not env or not index:
        print('请设置 PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX 环境变量以运行示例。')
        return

    print('已检测到配置，示例将初始化 Pinecone （本脚本仅演示，不会执行 upsert）')


if __name__ == '__main__':
    run()
