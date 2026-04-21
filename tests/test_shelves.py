def test_create_shelf(client, auth_headers):
    response = client.post(
        "/shelves",
        json={"name": "Horror"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Horror"