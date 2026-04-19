function fn() {
  var env = karate.env; // get system property 'karate.env'
  if (!env) {
    env = 'dev';
  }
  var config = {
    env: env,
    gatewayUrl: 'http://127.0.0.1:8000',
    aiGatewayUrl: 'http://127.0.0.1:8001',
    auditUrl: 'http://127.0.0.1:8002',
    configUrl: 'http://127.0.0.1:8003',
    mcpUrl: 'http://127.0.0.1:8082',
    ucpUrl: 'http://127.0.0.1:8084',
    tgaUrl: 'http://127.0.0.1:8083',
    chatUrl: 'http://127.0.0.1:8090',
    aiopsUrl: 'http://127.0.0.1:8200',
    terminalUrl: 'http://127.0.0.1:8085'
  };
  
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 5000);
  
  return config;
}
