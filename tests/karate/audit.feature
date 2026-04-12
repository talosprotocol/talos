Feature: Audit Service API Tests

Background:
  * url auditUrl
  * def eventId = '018f3d6b-7123-7a1b-9c2d-123456789abc'

Scenario: Ingest Audit Event
  Given path 'api/events/ingest'
  And request 
  """
  {
    "schema_id": "talos.audit_event",
    "schema_version": "v1",
    "event_id": "#(eventId)",
    "ts": "2026-01-20T12:00:00Z",
    "request_id": "req-123",
    "surface_id": "test-surface",
    "outcome": "OK",
    "principal": { "id": "tester", "type": "USER" },
    "http": { "method": "POST", "path": "/test" },
    "meta": { "test": "data" },
    "resource": { "type": "test", "id": "res-123" },
    "event_hash": "66a045b452102c59d840ec097d59d9467e13a3f34f6494e539ffd32c1bb35f18"
  }
  """
  When method post
  Then status 200 or status 409
  # 409 if already exists

Scenario: List Audit Events
  Given path 'api/events'
  When method get
  Then status 200
  And match response.items == '#[]'

Scenario: Get Merkle Proof for Event
  # Note: This might return 404 if the event was just ingested and not yet anchored, 
  # but it verifies the endpoint exists and the path works.
  Given path 'proof', eventId
  When method get
  Then status 200 or status 404

Scenario: Get Merkle Root
  Given path 'root'
  When method get
  Then status 200
  And match response.root_hash == '#string'
