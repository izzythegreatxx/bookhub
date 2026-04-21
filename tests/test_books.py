def test_create_book(client, auth_headers):
    response = client.post(
        "/books",
        json={
            "title": "Dracula",
            "author": "Bram Stoker",
            "year": 1897,
            "status": "want_to_read",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Dracula"
    assert data["author"] == "Bram Stoker"