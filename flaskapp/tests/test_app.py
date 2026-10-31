import pytest
from unittest.mock import patch, MagicMock
from app import app


# Fixture to create a test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = "test_secret"
    with app.test_client() as client:
        yield client


# Test the home page
def test_home_page(client):
    """GET / should return index.html"""
    response = client.get('/')
    assert response.status_code == 200


# Test the signup page
def test_show_signup_page(client):
    """GET /showSignUp should return signup.html"""
    response = client.get('/showSignUp')
    assert response.status_code == 200


# Test the signup page with missing fields
def test_signup_missing_fields(client):
    """POST /signUp with missing data should return error JSON"""
    response = client.post('/signUp', data={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Enter all required fields"


# Test the signup page with success
@patch('app.mysql')
def test_signup_success(mock_mysql, client):
    """POST /signUp should create user when all fields are present"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.post('/signUp', data={
        'inputName': 'John',
        'inputEmail': 'john@example.com',
        'inputPassword': 'pass123'
    })

    assert response.status_code == 200
    assert b"User created successfully" in response.data


# Test the signin page
def test_show_signin_page(client):
    """GET /showSignIn should return signin.html"""
    response = client.get('/showSignIn')
    assert response.status_code == 200


# Test the validate login page with success


# Test the user home page without session
def test_user_home_unauthorized(client):
    """GET /userHome without session should return unauthorized"""
    response = client.get('/userHome')
    assert b"Unauthorized Access" in response.data


# Test the logout page
def test_logout(client):
    with client.session_transaction() as sess:
        sess['user'] = 1
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/' in response.headers['Location']


# Test the show add wish page with session
def test_show_add_wish_with_session(client):
    with client.session_transaction() as sess:
        sess['user'] = 1
    response = client.get('/showAddWish')
    assert response.status_code == 200


# Test the show add wish page without session
def test_show_add_wish_without_session(client):
    response = client.get('/showAddWish')
    assert response.status_code == 200


# Test the add wish page with success
@patch('app.mysql')
def test_add_wish_success(mock_mysql, client):
    with client.session_transaction() as sess:
        sess['user'] = 1
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.post('/addWish', data={
        'inputTitle': 'Test Wish',
        'inputDescription': 'Description'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/userHome' in response.headers['Location']


# Test the add wish page without session
def test_add_wish_unauthorized(client):
    response = client.post('/addWish', data={
        'inputTitle': 'Test Wish',
        'inputDescription': 'Description'
    })
    assert b"Unauthorized Access" in response.data


# Test the add wish page with DB error


# Test the get wish page with success
@patch('app.mysql')
def test_get_wish_success(mock_mysql, client):
    with client.session_transaction() as sess:
        sess['user'] = 1
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, "Title", "Description", "ignored", "2025-01-01")
    ]

    response = client.get('/getWish')
    assert response.status_code == 200
    assert b"Title" in response.data


# Test the get wish page without session
def test_get_wish_unauthorized(client):
    response = client.get('/getWish')
    assert b"Unauthorized Access" in response.data


# Test the get wish page with DB error


# Test the signup page with DB error
@patch('app.mysql')
def test_signup_db_error_returned(mock_mysql, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = ["Duplicate user"]

    response = client.post("/signUp", data={
        "inputName": "John",
        "inputEmail": "john@example.com",
        "inputPassword": "pass123"
    })
    assert response.status_code == 400
    assert b"Duplicate user" in response.data


# Test the signup page with DB down


# Test the validate login page with wrong password
@patch('app.mysql')
def test_validate_login_wrong_password(mock_mysql, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, "John", "john@example.com", "wrongpass")
    ]

    response = client.post("/validateLogin", data={
        "inputEmail": "john@example.com",
        "inputPassword": "pass123"
    })
    assert b"Wrong Email address" in response.data


# Test the validate login page with DB error


# Test the add wish page with error template
@patch('app.mysql')
def test_add_wish_returns_error_template(mock_mysql, client):
    with client.session_transaction() as sess:
        sess["user"] = 1
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = ["Some error"]

    response = client.post("/addWish", data={
        "inputTitle": "Wish",
        "inputDescription": "Desc"
    })
    assert b"An error occurred" in response.data


# Test the healthz page
def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert b"ok" in response.data


# Test the readiness page with success
@patch('app.mysql')
def test_readiness_success(mock_mysql, client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_mysql.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    response = client.get("/readiness")
    assert response.status_code == 200
    assert b"ready" in response.data


# Test the readiness page with failure
@patch('app.mysql')
def test_readiness_failure(mock_mysql, client):
    mock_mysql.connect.side_effect = Exception("DB not reachable")
    response = client.get("/readiness")
    assert response.status_code == 503
    assert b"not ready" in response.data
