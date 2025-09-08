# 本地测试脚本：针对 StreamJSONBuilder 的边界场景
# 场景包括：
# 1) SSE-like 前缀："data: {\"a\": 1}" 被拆成若干行
# 2) JSON 在键/值中断开：'{"overview": "这是一段很长的描述..."}'
# 3) 多个 JSON 对象连续发送

from app.services.stream_parser import StreamJSONBuilder


def run_case_sse_prefix():
    builder = StreamJSONBuilder()
    chunks = [
        'data: ',
        '{"overview": "部',
        '分文本", "confidence": 0.9}',
    ]
    results = []
    for c in chunks:
        obj = builder.feed(c)
        if obj is not None:
            results.append(obj)
    assert len(results) == 1, f"expected 1 obj, got {len(results)}"
    print('SSE prefix case passed:', results[0])


def run_case_split_token():
    builder = StreamJSONBuilder()
    chunks = [
        '{"overview": "这是一段很长的描述，可能在',
        '模型输出中被拆分到中间。", "confidence":',
        ' 0.85}',
    ]
    res = None
    for c in chunks:
        res = builder.feed(c)
    assert res is not None, 'split token case failed to reconstruct JSON'
    print('Split token case passed:', res)


def run_case_multiple_objects():
    builder = StreamJSONBuilder()
    chunks = [
        '{"a": 1}{"b": 2}',
    ]
    objs = []
    for c in chunks:
        # feed may return first object, loop to extract remaining
        while True:
            obj = builder.feed(c)
            if obj is None:
                break
            objs.append(obj)
            # continue feeding empty to try extract more from existing buffer
            c = ''
    assert len(objs) >= 2, f'multiple objects case expected >=2, got {len(objs)}'
    print('Multiple objects case passed:', objs)


if __name__ == '__main__':
    run_case_sse_prefix()
    run_case_split_token()
    run_case_multiple_objects()
    print('All stream parser tests passed')
