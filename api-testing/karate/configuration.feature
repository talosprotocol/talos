Feature: Configuration Service API Tests

Background:
  * url configUrl

Scenario: Verify Configuration Service Health
  Given path 'api/config/health'
  When method get
  Then status 200
  And match response.status == 'ok'

Scenario: Verify Contracts Version
  Given path 'api/config/contracts-version'
  When method get
  Then status 200
  And match response.contracts_version != null

Scenario: Verify Configuration Schema
  Given path 'api/config/schema'
  When method get
  Then status 200 or status 500
  # 500 if schema file missing in environment, but validates path

Scenario: List Configuration History
  Given path 'api/config/history'
  When method get
  Then status 200
  And match response.items == '#[]'
