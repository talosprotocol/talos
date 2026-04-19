Feature: UCP Connector API
  Background:
    * url ucpUrl
  Scenario: Health Check
    Given path 'health'
    When method GET
    Then status 200
