Feature: MCP Connector API
  Background:
    * url mcpUrl
  Scenario: Health Check
    Given path 'health'
    When method GET
    Then status 200
  Scenario: List Servers
    Given path 'admin/v1/mcp/servers'
    When method GET
    Then status 200
