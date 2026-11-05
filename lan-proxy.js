// LAN access for watching the standby screens on a phone/tablet in the same network.
// Both servers stay bound to 127.0.0.1; this proxy listens on the PC's LAN address and forwards:
//   everything            -> standby-server.js (127.0.0.1:18770)
//   /__dgg_chat_ws (ws)   -> the DSA overlay relay (127.0.0.1:18765)
// Usage: node lan-proxy.js [lanAddress] [port] [--control]   (default: the first private IPv4, port 18780)
// View-only by default (QA 05 Nov): the standby server refuses control requests only when they carry a foreign Origin, so
// through this proxy any device on the LAN / tailnet could POST /ctl/cmd (a fake chatter saying anything on stream,
// remove, reset). Now only GET/HEAD pass, and of /ctl/ only the command stream to watching screens (GET /ctl/events).
// --control passes everything, as before (e.g. control.html on your own phone over Tailscale).
// Then open  http://<lan>:18780/auditorium.html?everyone=1&relay=<lan>:18780  on the phone.
'use strict';
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');

const STANDBY = { host: '127.0.0.1', port: Number(process.env.STANDBY_PORT || 18770) };
const RELAY = { host: '127.0.0.1', port: Number(process.env.DGG_OBS_PORT || 18765) };
const isPrivate = (a) => /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(a);
const lan = process.argv.slice(2).filter((a) => a !== '--control')[0] || Object.values(os.networkInterfaces()).flat()
  .find((i) => i && i.family === 'IPv4' && !i.internal && isPrivate(i.address))?.address;
const args = process.argv.slice(2).filter((a) => a !== '--control');
const CONTROL = process.argv.includes('--control');
const PORT = Number(args[1] || 18780);
if (!lan) { console.error('No private LAN IPv4 address found; pass one: node lan-proxy.js 192.168.x.y'); process.exit(1); }

const server = http.createServer((req, res) => {
  const path0 = (req.url || '').split('?')[0];
  if (!CONTROL && ((req.method !== 'GET' && req.method !== 'HEAD') || (path0.startsWith('/ctl/') && path0 !== '/ctl/events'))) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('view-only proxy (start it with --control to allow the control panel)');
    return;
  }
  const up = http.request({ ...STANDBY, method: req.method, path: req.url, headers: { ...req.headers, host: `${STANDBY.host}:${STANDBY.port}` } }, (r) => {
    res.writeHead(r.statusCode || 502, r.headers);
    r.pipe(res);
    // the server restarted mid-stream: end the phone's response too, so its EventSource reconnects
    r.on('close', () => { if (!r.complete) res.destroy(); });
  });
  // the phone left (reload, lock): close the upstream request too, else the server kept it as an open screen forever
  res.on('close', () => up.destroy());
  up.on('error', () => { if (!res.headersSent) res.writeHead(502); res.end('standby server not running'); });
  req.pipe(up);
});

// WebSocket upgrades: chat goes to the relay, anything else (e.g. live reload) to the standby server
server.on('upgrade', (req, socket, head) => {
  const target = req.url.startsWith('/__dgg_chat_ws') ? RELAY : STANDBY;
  const up = net.connect(target.port, target.host, () => {
    const headers = { ...req.headers, host: `${target.host}:${target.port}` };
    delete headers.origin;   // the relay only expects local pages
    up.write(`${req.method} ${req.url} HTTP/1.1\r\n${Object.entries(headers).map(([k, v]) => `${k}: ${v}`).join('\r\n')}\r\n\r\n`);
    if (head?.length) up.write(head);
    up.pipe(socket);
    socket.pipe(up);
  });
  const close = () => { up.destroy(); socket.destroy(); };
  up.on('error', close);
  socket.on('error', close);
});

// one line per new device connection, so "the phone never got here" is easy to tell apart from a page error
const seen = new Set();
server.on('connection', (s) => {
  const ip = s.remoteAddress;
  if (!seen.has(ip)) { seen.add(ip); console.log(`${new Date().toLocaleTimeString()} connection from ${ip}`); }
});
server.on('request', (req) => { if (req.socket.remoteAddress !== lan) console.log(`${req.socket.remoteAddress} ${req.method} ${req.url.slice(0, 80)}`); });

server.listen(PORT, lan, () => {
  console.log(`LAN proxy on http://${lan}:${PORT}/`);
  console.log(`Phone: http://${lan}:${PORT}/auditorium.html?everyone=1&relay=${lan}:${PORT}`);
});
