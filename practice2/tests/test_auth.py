import pytest
import httpx

BASE = "http://localhost:8000"

def test_register():
    r = httpx.post(f"{BASE}/auth/register", json={
        "username": "testuser", "password": "testpass", "role": "user"
    })
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"

def test_login():
    r = httpx.post(f"{BASE}/auth/login", json={
        "username": "testuser", "password": "testpass"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_validate_token():
    login_r = httpx.post(f"{BASE}/auth/login", json={
        "username": "testuser", "password": "testpass"
    })
    token = login_r.json()["access_token"]
    r = httpx.post(f"{BASE}/auth/validate", json={"token": token})
    assert r.status_code == 200
    assert r.json()["valid"] == True

def test_logout_and_validate():
    login_r = httpx.post(f"{BASE}/auth/login", json={
        "username": "testuser", "password": "testpass"
    })
    token = login_r.json()["access_token"]
    httpx.post(f"{BASE}/auth/logout", json={"token": token})
    r = httpx.post(f"{BASE}/auth/validate", json={"token": token})
    assert r.status_code == 401

def test_wrong_password():
    r = httpx.post(f"{BASE}/auth/login", json={
        "username": "testuser", "password": "wrongpass"
    })
    assert r.status_code == 401