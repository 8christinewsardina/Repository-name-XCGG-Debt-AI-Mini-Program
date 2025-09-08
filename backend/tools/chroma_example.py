def run():
    try:
        import chromadb
    except Exception:
        print('chromadb 未安装。若需要，请运行: pip install chromadb')
        return

    print('chromadb 安装可用。此示例不会执行实际写入操作。')


if __name__ == '__main__':
    run()
