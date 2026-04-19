Feature: Governance Agent (TGA) API
  Background:
    * url tgaUrl
  Scenario: List Traces
    Given path 'v1/tga/traces'
    When method GET
    Then status 200
