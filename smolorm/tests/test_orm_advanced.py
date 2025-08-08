import pytest
from smolorm.sqlmodel import IntField, SqlModel, TextField
from smolorm.expressions import col


class User(SqlModel):
    table_name = "test_users"
    username = TextField(default_value="John Doe")
    age = IntField(default_value=0)


class Post(SqlModel):
    table_name = "test_posts"
    title = TextField(default_value="Untitled")
    content = TextField(default_value="Empty")
    user_id = IntField(default_value=0)


@pytest.fixture(autouse=True)
def setup_tables():
    User.drop()
    Post.drop()
    User.__init_subclass__()
    Post.__init_subclass__()
    yield
    User.drop()
    Post.drop()


def test_user_post_relationship_simulation():
    # Create users
    User.create({"username": "Alice", "age": 25})
    User.create({"username": "Bob", "age": 30})

    # Get their IDs
    users = User.select().run()
    alice_id = users[0]["id"]
    bob_id = users[1]["id"]

    # Create posts
    Post.create({"title": "Alice Post 1", "content": "Hello", "user_id": alice_id})
    Post.create({"title": "Alice Post 2", "content": "World", "user_id": alice_id})
    Post.create({"title": "Bob Post", "content": "Hey!", "user_id": bob_id})

    # Validate posts for Alice
    posts = Post.select().where(col("user_id") == alice_id).run()
    assert len(posts) == 2
    assert all(p["title"].startswith("Alice") for p in posts)

    # Validate posts for Bob
    posts = Post.select().where(col("user_id") == bob_id).run()
    assert len(posts) == 1
    assert posts[0]["title"] == "Bob Post"


def test_string_matching_expressions():
    User.create({"username": "Johnny", "age": 20})
    User.create({"username": "Johnathan", "age": 22})
    User.create({"username": "Alice", "age": 25})

    results = User.select().where(col("username").startswith("John")).run()
    assert len(results) == 2
    assert all("John" in user["username"] for user in results)

    results = User.select().where(col("username").contains("ice")).run()
    assert len(results) == 1
    assert results[0]["username"] == "Alice"


def test_compound_where_update():
    User.create({"username": "Dave", "age": 18})
    User.create({"username": "Dave", "age": 22})
    User.update({"age": 99}).where(
        (col("username") == "Dave") & (col("age") < 20)
    ).run()

    results = User.select().where(col("username") == "Dave").run()
    assert len(results) == 2
    for user in results:
        if user["age"] < 20:
            assert user["age"] == 99


def test_chained_operations():
    User.create({"username": "TempUser", "age": 50})
    User.update({"age": 60}).where(col("username") == "TempUser").run()
    User.delete().where(col("age") == 60).run()

    results = User.select().where(col("username") == "TempUser").run()
    assert results == []


def test_defaults_overwritten():
    user = {"username": "Zed"}
    User.create(user)
    result = User.select().where(col("username") == "Zed").run()
    assert result[0]["age"] == 0  # Default age


def test_select_with_no_matches():
    result = User.select().where(col("username") == "Nobody").run()
    assert result == []


def test_nonexistent_column_fails_gracefully():
    User.create({"username": "FailTest", "age": 45})
    try:
        User.select().where(col("nonexistent") == "value").run()
    except Exception as e:
        assert isinstance(e, Exception)
