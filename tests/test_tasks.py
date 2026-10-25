from sqlalchemy import event


def test_list_tasks_query_count_is_constant(client, db_session):
    # 할 일 개수와 관계없이 GET /tasks 의 쿼리 수가 일정해야 합니다(N+1 회귀 방지).
    for i in range(10):
        client.post("/tasks", json={"title": f"할 일 {i}", "tags": [f"태그{i}", "공통"]})
    db_session.expire_all()

    count = 0

    def count_query(*_):
        nonlocal count
        count += 1

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_query)
    try:
        res = client.get("/tasks")
    finally:
        event.remove(engine, "before_cursor_execute", count_query)

    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 10
    assert all(len(t["tags"]) == 2 for t in tasks)
    assert count == 2  # 할 일 목록 1회 + 태그 1회
