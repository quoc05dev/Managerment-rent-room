const { createProxyMiddleware } = require('http-proxy-middleware');

// Dev-only proxy so `npm start` can talk to the backend.
// Override with REACT_APP_DEV_API_TARGET if the backend runs somewhere else.
const TARGET = process.env.REACT_APP_DEV_API_TARGET || 'http://localhost:8081';

// Must stay in sync with the `location` blocks in rent-manager-app/nginx.conf.
// A root matches on a path-segment boundary only, so "/room" never swallows the
// "/room-hired" page and "/request" never swallows the "/request-status" page.
const API_ROOTS = [
  '/auth',
  '/api',
  '/health',
  '/room',
  '/user',
  '/account',
  '/contract',
  '/maintenance',
  '/request',
  '/follow',
  '/blog-store',
  '/statistical',
  '/customer',
  '/authorization',
  '/export-bill',
  '/document',
  '/view-file',
  '/image',
  '/oauth2/authorize',
  '/oauth2/callback',
];

// "/admin" and "/rentaler" are both UI prefixes and API prefixes, so only these
// sub-paths are API calls - the rest are pages handled by react-router.
const API_EXACT = new Set(['/admin/me', '/rentaler/me']);

// react-scripts 5 serves its HMR socket on "/ws" (webpack-dev-server default),
// so the dev server has to keep that exact path.
const DEV_SERVER_PATHS = new Set(['/ws']);

const underRoot = (pathname, root) => pathname === root || pathname.startsWith(root + '/');

const isApiRequest = (pathname) =>
  !DEV_SERVER_PATHS.has(pathname) &&
  (API_EXACT.has(pathname) || API_ROOTS.some((root) => underRoot(pathname, root)));

const apiProxy = createProxyMiddleware({
  target: TARGET,
  changeOrigin: true,
  secure: false,
  ws: false,
});

// Only "/ws/..." is forwarded (matches `location /ws/` in nginx.conf); the bare
// "/ws" stays local so hot reloading keeps working.
const wsProxy = createProxyMiddleware({
  target: TARGET,
  changeOrigin: true,
  secure: false,
  ws: true,
});

module.exports = function (app) {
  app.use((req, res, next) => {
    if (underRoot(req.path, '/ws')) return wsProxy(req, res, next);
    if (!isApiRequest(req.path)) return next();
    return apiProxy(req, res, next);
  });
};
