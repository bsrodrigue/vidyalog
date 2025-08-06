import pytest
from smolorm.sqlmodel import SqlModel
from smolorm.expressions import col


class TestUser(SqlModel):
    table_name = "test_users"
    age = 0
    username = "default"
    password = "default"


@pytest.fixture(autouse=True)
def clean_table():
    TestUser.drop()
    TestUser.__init_subclass__()  # recreate table
    yield
    TestUser.drop()


def test_create_user():
    TestUser.create({"username": "alice", "password": "secret", "age": 30})

    results = TestUser.select().run()
    assert len(results) == 1
    user = results[0]
    assert user["username"] == "alice"
    assert user["password"] == "secret"
    assert user["age"] == 30


def test_multiple_creations():
    TestUser.create({"username": "bob", "password": "pass", "age": 22})
    TestUser.create({"username": "eve", "password": "xyz", "age": 25})

    results = TestUser.select().run()
    assert len(results) == 2
    usernames = [r["username"] for r in results]
    assert "bob" in usernames and "eve" in usernames


def test_update_user():
    TestUser.create({"username": "charlie", "password": "1234", "age": 28})
    TestUser.update({"password": "updated"}).where(col("password") == "1234").run()

    results = TestUser.select().run()
    assert results[0]["password"] == "updated"


def test_delete_user():
    TestUser.create({"username": "david", "password": "qwerty", "age": 40})
    TestUser.delete().where(col("username") == "david").run()

    results = TestUser.select().run()
    assert results == []


def test_select_specific_columns():
    TestUser.create({"username": "erin", "password": "hidden", "age": 18})
    results = TestUser.select("username").run()

    assert len(results) == 1
    assert "username" in results[0]
    assert "password" not in results[0]
    assert results[0]["username"] == "erin"


def test_and_where_clause_combination():
    TestUser.create({"username": "user1", "password": "123", "age": 20})
    TestUser.create({"username": "user2", "password": "123", "age": 30})

    results = (
        TestUser.select().where((col("age") > 25) & (col("password") == "123")).run()
    )
    assert len(results) == 1
    assert results[0]["username"] == "user2"


def test_or_where_clause_combination():
    TestUser.create({"username": "user1", "password": "123", "age": 20})
    TestUser.create({"username": "user2", "password": "123", "age": 30})

    results_1 = TestUser.select().where((col("age") == 20) | (col("age") == 30)).run()
    assert len(results_1) == 2

    assert results_1[0]["username"] == "user1"
    assert results_1[1]["username"] == "user2"


def test_limit_clause():
    for i in range(100):
        TestUser.create({"username": f"user{i}", "password": f"pass{i}", "age": i})

    results_1 = TestUser.select().where(col("age") >= 0).limit(1).run()
    results_2 = TestUser.select().where(col("age") >= 0).limit(10).run()
    results_3 = TestUser.select().where(col("age") >= 0).limit(100).run()
    results_4 = TestUser.select().where(col("age") >= 0).limit(1000).run()

    results_5 = TestUser.select().limit(1000).run()

    assert len(results_1) == 1
    assert len(results_2) == 10
    assert len(results_3) == 100
    assert len(results_4) == 100
    assert len(results_5) == 100


def test_offset_clause():
    for i in range(100):
        TestUser.create({"username": f"user{i}", "password": f"pass{i}", "age": i})

    results_1 = TestUser.select().offset(5).run()
    results_2 = TestUser.select().offset(50).run()
    results_3 = TestUser.select().offset(100).run()
    results_4 = TestUser.select().offset(1000).run()

    assert len(results_1) == 95
    assert len(results_2) == 50
    assert len(results_3) == 0
    assert len(results_4) == 0


def test_order_by_clause():
    for i in range(100):
        TestUser.create({"username": f"user{i}", "password": f"pass{i}", "age": i})

    results_1 = TestUser.select().order_by("age", True).run()
    results_2 = TestUser.select().order_by("age").run()

    assert results_1[0]["age"] == 99
    assert results_2[0]["age"] == 0

    results_1 = TestUser.select().order_by("username", True).run()
    results_2 = TestUser.select().order_by("username").run()

    assert results_1[0]["username"] == "user99"
    assert results_2[0]["username"] == "user0"


def test_complex_clause_combination():
    for i in range(100):
        TestUser.create({"username": f"user{i}", "password": f"pass{i}", "age": i})

    results = (
        TestUser.select("username", "password")
        .where((col("age") > 50) & (col("age") < 61))  # 51 to 60 years
        .order_by("age", descending=True)  # 60 to 51 years
        .limit(10)  # 60 to 51 years
        .offset(5)  # 55 to 51 years
        .run()
    )

    r = results[0]
    last_r = results[-1]

    assert len(results) == 5

    assert "age" not in r
    assert "age" not in last_r

    assert r["username"] == "user55"
    assert last_r["username"] == "user51"
