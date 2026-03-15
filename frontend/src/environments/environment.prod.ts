const websocketOrigin =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost';

export const environment = {
  production: true,
  apiUrl: '/api/v1',
  wsUrl: `${websocketOrigin}/ws`,
  platformRootDomain: 'agentbroker.app',
  platformAppDomain: 'app.agentbroker.app',
  platformMarketingDomain: 'agentbroker.app',
  platformTemplate: 'vercel-platforms-starter-kit',
  platformDeploymentTarget: 'vercel',
  platformTenancy: 'multi-tenant',
  platformAdminSurface: 'shared-dashboard'
};
