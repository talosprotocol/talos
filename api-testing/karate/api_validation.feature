Feature: Backend Capabilities Validation

  Background:
    * url 'http://localhost:8000'
    * def chatUrl = 'http://localhost:8090'
    * def auditUrl = 'http://localhost:8001'

  Scenario: Validate Gateway Base Endpoints
    Given path '/healthz'
    When method get
    Then status 200

  Scenario: Validate Chat Endpoint Echo
    Given url chatUrl
    And path '/v1/chat/send'
    And request { content: "test message", session_id: "test-session" }
    When method post
    Then status 200
    And match response.response != null

  Scenario: Validate Audit Endpoints
    Given url auditUrl
    And path '/health'
    When method get
    Then status 200
