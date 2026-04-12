function fn() {
  var env = karate.env; // get system property 'karate.env'
  if (!env) {
    env = 'dev';
  }
  var config = {
    env: env,
    gatewayUrl: 'http://localhost:8000',
    auditUrl: 'http://localhost:8002'
  };
  
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 5000);
  
  return config;
}
