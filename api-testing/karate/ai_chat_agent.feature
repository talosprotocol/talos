Feature: AI Chat Agent API
  Background:
    * url chatUrl
  Scenario: Health Check
    Given path 'health'
    When method GET
    Then status 200
