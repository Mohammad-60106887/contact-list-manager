import pytest
from app import app, db
from models import Contact

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    # Create test client
    with app.test_client() as client:
        with app.app_context():
            # Create all tables in the test database
            db.create_all()
            yield client
            # Clean up after tests
            db.session.remove()
            db.drop_all()

@pytest.fixture
def sample_contact(client):
    # Create and add a sample contact to the in-memory database
    contact = Contact(
        name='John Doe',
        phone='1234567890',
        email='john@example.com',
        type='Personal'
    )
    db.session.add(contact)
    db.session.commit()
    return contact

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_addsourc_contact(client):
    data = {
        'name': 'Jane Doe',
        'phone': '9876543210',
        'email': 'jane@example.com',
        'type': 'Personal'
    }
    response = client.post('/add', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Jane Doe' in response.data

def test_update_contact(client, sample_contact):
    data = {
        'name': 'John Smith',
        'phone': sample_contact.phone,
        'email': sample_contact.email,
        'type': sample_contact.type,
        'submit': 'Update'
    }
    response = client.post(
        f'/update/{sample_contact.id}',
        data=data,
        follow_redirects=True
    )
    assert response.status_code == 200
    updated_contact = db.session.get(Contact, sample_contact.id)
    assert updated_contact.name == 'John Smith'

# Test Case: Delete Contact
def test_delete_contact(client, sample_contact):
    response = client.get(f'/delete/{sample_contact.id}', follow_redirects=True)
    assert response.status_code == 200

    # Ensure contact is deleted
    deleted_contact = db.session.get(Contact, sample_contact.id)
    assert deleted_contact is None

# Test Case: Search Contact
def test_search_contact(client, sample_contact):
    response = client.get('/contacts?search=John')
    assert response.status_code == 200
    assert b'John Doe' in response.data

def test_get_contacts_api(client, sample_contact):
    response = client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'John Doe'

def test_get_single_contact_api(client, sample_contact):
    response = client.get(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'John Doe'

def test_create_contact_api(client):
    data = {
        'name': 'API User',
        'phone': '5555555555',
        'email': 'api@example.com',
        'type': 'work'
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 201
    assert response.get_json()['name'] == 'API User'

def test_update_contact_api(client, sample_contact):
    data = {
        'name': 'Updated Name',
        'phone': '5551234567',
        'email': 'updated@example.com',
        'type': 'family'
    }
    response = client.put(f'/api/contacts/{sample_contact.id}', json=data)
    assert response.status_code == 200
    updated_contact = response.get_json()
    assert updated_contact['name'] == 'Updated Name'
    assert updated_contact['phone'] == '5551234567'
    assert updated_contact['email'] == 'updated@example.com'
    assert updated_contact['type'] == 'family'

def test_delete_contact_api(client, sample_contact):
    response = client.delete(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 204
    get_response = client.get(f'/api/contacts/{sample_contact.id}')
    assert get_response.status_code == 404

def test_list_contact_api(client, sample_contact):
    # Ensure sample contact is added before this test runs
    contact_in_db = db.session.query(Contact).first()
    assert contact_in_db is not None  # Ensure there is at least one contact in the database

    response = client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0  # Ensure there is at least one contact in the response
    assert data[0]['name'] == 'John Doe'

# Test error cases
def test_invalid_contact_creation(client):
    data = {
        'name': 'Invalid User',
        # Missing required fields
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 400

def test_get_nonexistent_contact(client):
    response = client.get('/api/contacts/999')
    assert response.status_code == 404  
