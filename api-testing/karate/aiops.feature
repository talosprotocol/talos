Feature: AIOps API
  Background:
    * url aiopsUrl
  Scenario: Health Check
    Given path 'health'
    When method GET
    Then status 200
