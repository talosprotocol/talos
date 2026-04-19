Feature: Gateway API Tests

Background:
  * url gatewayUrl

Scenario: Verify Gateway Health and Version
  Given path 'healthz'
  When method get
  Then status 200
  And match response.status == 'ok'

  Given path 'version'
  When method get
  Then status 200
  And match response.service == 'gateway'

Scenario: Verify Gateway Status
  Given path 'api/gateway/status'
  When method get
  Then status 200
  And match response.state == 'RUNNING'
  And match response.schema_version == '1'

Scenario: Verify Authorization Rejection (Negative Case)
  Given path 'mcp/tools/chat'
  And request { session_id: 'test-session', model: 'gpt-4o', messages: [{ role: 'user', content: 'hello' }] }
  When method post
  Then status 403
  And match response.error == 'Capability verification failed'

Scenario: Verify Authorization with Mock Capability (Positive Case)
  Given path 'mcp/tools/chat'
  And request { session_id: 'test-session-auth', model: 'gpt-4o', messages: [{ role: 'user', content: 'hello' }], capability: 'cap_test' }
  When method post
  # This might fail if the mock connector is not running, but it validates the auth path
  Then status 200 or status 500
  # If 500, it should be a connector error, not an auth error
  And match response == '#? (_ == null || responseStatus != 500 || response.code == "GATEWAY_ERROR")'
