from app.models import User

def test_register(client, app):
    response = client.post('/register', data={
        'full_name': 'Jane Doe',
        'email': 'jane@solar.app',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='jane@solar.app').first()
        assert user is not None
        assert user.full_name == 'Jane Doe'


def test_register_duplicate(client, auth_user, app):
    response = client.post('/register', data={
        'full_name': 'Duplicate User',
        'email': 'testuser@solar.app',
        'password': 'password123'
    }, follow_redirects=True)

    assert b'An account with this email already exists' in response.data


def test_login_logout(client, auth_user):
    # Valid login
    response = client.post('/login', data={
        'email': 'testuser@solar.app',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Executive Dashboard' in response.data

    # Logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b'Log In' in logout_res.data


def test_invalid_login(client, auth_user):
    response = client.post('/login', data={
        'email': 'testuser@solar.app',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in response.data
