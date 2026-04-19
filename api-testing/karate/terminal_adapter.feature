Feature: Terminal Adapter API
  Background:
    * url terminalUrl
  Scenario: Health Check
    Given path 'health'
    When method GET
    Then status 200
