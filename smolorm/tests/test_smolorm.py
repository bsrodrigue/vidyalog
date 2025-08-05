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


def test_where_clause_combination():
    TestUser.create({"username": "user1", "password": "123", "age": 20})
    TestUser.create({"username": "user2", "password": "123", "age": 30})

    results = (
        TestUser.select().where((col("age") > 25) & (col("password") == "123")).run()
    )
    assert len(results) == 1
    assert results[0]["username"] == "user2"
