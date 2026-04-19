Feature: AI Gateway API Tests

Background:
  * url aiGatewayUrl

Scenario: Verify AI Gateway Health (Liveness)
  Given path 'health/live'
  When method get
  Then status 200
  And match response.status == 'ok'

Scenario: Verify AI Gateway Health (Readiness)
  Given path 'health/ready'
  When method get
  # Might be 503 if DB/Redis not ready, but validates the endpoint
  Then status 200 or status 503

Scenario: Verify AI Gateway Version
  Given path 'version'
  When method get
  Then status 200
  And match response.version == '0.1.0'

Scenario: Verify List Models (Unauthenticated)
  Given path 'v1/models'
  When method get
  Then status 403
  # AI Gateway uses AuthContext middleware which should reject missing keys
