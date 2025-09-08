import pytest
from app.services.stream_parser import StreamJSONBuilder


def test_sse_prefix():
    builder = StreamJSONBuilder()
    # 模拟 SSE：多行可能包含 data: 前缀
    chunks = [
        'data: ',
        'data: {"overview": "部',
        'data: 分文本", ',
        'data: "confidence": 0.9}',
        'data: [DONE]',
    ]
    results = []
    for c in chunks:
        obj = builder.feed(c)
        if obj is not None:
            results.append(obj)
    assert len(results) == 1
    assert results[0]["overview"] == '部分文本'
    assert results[0]["confidence"] == 0.9


def test_split_token():
    builder = StreamJSONBuilder()
    chunks = [
        '{"overview": "这是一段很长的描述，可能在',
        '模型输出中被拆分到中间。", "confidence":',
        ' 0.85}',
    ]
    res = None
    for c in chunks:
        res = builder.feed(c)
    assert res is not None
    assert res["confidence"] == 0.85


def test_multiple_objects():
    builder = StreamJSONBuilder()
    # 多对象也可能以 SSE 行形式到达
    chunks = [
        'data: {"a": 1}\n',
        'data: {"b": 2}',
    ]
    objs = []
    for c in chunks:
        # feed may return first object, loop to extract remaining
        while True:
            obj = builder.feed(c)
            if obj is None:
                break
            objs.append(obj)
            c = ''
    assert len(objs) >= 2
    assert objs[0]["a"] == 1
    assert objs[1]["b"] == 2
