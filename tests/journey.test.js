'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { create } = require('../shared/journey');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

test('a guest has one case-insensitive location and must start in the lobby', () => {
  const journey = create();
  assert.equal(journey.handoff({ nick: 'Guest' }), false);
  assert.equal(journey.claimLobby('Guest'), true);
  assert.equal(journey.claimLobby('guest'), false);
  assert.equal(journey.location('GUEST'), 'lobby');
});

test('a door handoff is delivered once with the same avatar and snack', () => {
  const journey = create(), received = [];
  journey.onAuditoriumArrival((message) => received.push(message));
  journey.claimLobby('Guest');
  const payload = { nick: 'Guest', emote: 'PEPE', carry: 'soda', tokens: [] };
  assert.equal(journey.handoff(payload), true);
  assert.equal(journey.handoff(payload), false);
  journey.retry();
  assert.deepEqual(received, [payload]);
  assert.notEqual(received[0], payload);
  journey.release('Guest', 'lobby'); // lobby removes its departing character
  assert.equal(journey.location('Guest'), 'auditorium');
  assert.equal(journey.claimLobby('Guest'), false);
});

test('a door transfer waits for the auditorium to be ready', () => {
  const journey = create(), received = [];
  journey.claimLobby('Guest');
  journey.handoff({ nick: 'Guest', emote: 'YEE' });
  journey.onAuditoriumArrival((message) => received.push(message));
  journey.retry();
  assert.equal(received.length, 1);
  assert.deepEqual(journey.stats(), { lobby: 0, auditorium: 1, transfers: 1 });
});

test('temporarily rejected delivery can retry without counting another transfer', () => {
  const journey = create();
  let attempts = 0;
  journey.onAuditoriumArrival(() => ++attempts > 1);
  journey.claimLobby('Guest');
  journey.handoff({ nick: 'Guest' });
  journey.retry();
  journey.retry();
  assert.equal(attempts, 2);
  assert.equal(journey.stats().transfers, 1);
});

test('leaving releases membership so a later visit can start at the lobby', () => {
  const journey = create();
  journey.claimLobby('Guest');
  journey.handoff({ nick: 'Guest' });
  journey.release('guest', 'auditorium');
  assert.equal(journey.location('Guest'), null);
  assert.equal(journey.claimLobby('Guest'), true);
});

test('refreshing only the auditorium can recover its current guests', () => {
  const journey = create();
  journey.onAuditoriumArrival(() => true);
  journey.claimLobby('Guest');
  journey.handoff({ nick: 'Guest' });
  const restored = [];
  journey.onAuditoriumArrival((message) => restored.push(message.nick));
  assert.deepEqual(restored, ['Guest']);
  assert.equal(journey.stats().transfers, 1);
});

// Exercise the actual queue-drain function with virtual time, without creating
// browser chatters, connecting chat or injecting traffic into any scene.
test('lobby pacing admits one at a time and never catches up with a burst', () => {
  const html = fs.readFileSync(path.join(__dirname, '../lobby-qa.html'), 'utf8');
  const start = html.indexOf('  function stepLobbyArrivals(now) {');
  const end = html.indexOf('  Cinema.onWalkIn(receiveArrival);', start);
  const admitted = [];
  const pending = new Map([
    ['first', { message: { nick: 'first' }, updated: 0 }],
    ['second', { message: { nick: 'second' }, updated: 0 }],
  ]);
  let crowded = false;
  const ctx = { journey: { release() {} }, pendingArrivals: pending, nextLobbyArrival: 0, arrivalBurstRemaining: 0,
    liveCount: () => 0, CAP: 40, CROWD: 14, crowdEvery: () => crowded ? 2 : 1,
    spawn: (message) => admitted.push(message.nick), rand: () => 1800 };
  vm.createContext(ctx);
  vm.runInContext(html.slice(start, end), ctx);
  ctx.stepLobbyArrivals(0);
  ctx.stepLobbyArrivals(100);
  ctx.stepLobbyArrivals(1799);
  assert.deepEqual(admitted, ['first']);
  crowded = true;
  ctx.stepLobbyArrivals(5000);
  assert.equal(pending.size, 1);
  crowded = false;
  ctx.stepLobbyArrivals(5000);
  assert.deepEqual(admitted, ['first', 'second']);
  assert.equal(ctx.nextLobbyArrival, 6800);
});

test('busy lobby queues form small spaced groups and slow down as the backlog clears', () => {
  const html = fs.readFileSync(path.join(__dirname, '../lobby-qa.html'), 'utf8');
  const start = html.indexOf('  function stepLobbyArrivals(now) {');
  const end = html.indexOf('  Cinema.onWalkIn(receiveArrival);', start);
  function setup(count) {
    let occupants = 0, crowded = false;
    const pending = new Map(Array.from({ length: count }, (_, i) =>
      [String(i), { message: { nick: String(i) }, updated: 0 }]));
    const admitted = [];
    const ctx = { journey: { release() {} }, pendingArrivals: pending,
      nextLobbyArrival: 0, arrivalBurstRemaining: 0,
      liveCount: () => occupants, CAP: 40, CROWD: 14, crowdEvery: () => crowded ? 2 : 1,
      spawn: m => { admitted.push(m.nick); occupants++; }, rand: (lo, hi) => (lo + hi) / 2 };
    vm.createContext(ctx);
    vm.runInContext(html.slice(start, end), ctx);
    return { ctx, pending, admitted, crowd: value => { crowded = value; }, full: () => { occupants = 40; } };
  }
  const busy = setup(50);
  busy.ctx.stepLobbyArrivals(0);
  assert.equal(busy.ctx.nextLobbyArrival, 350);
  busy.ctx.stepLobbyArrivals(349);
  assert.equal(busy.admitted.length, 1);
  busy.ctx.stepLobbyArrivals(350);
  busy.ctx.stepLobbyArrivals(700);
  assert.equal(busy.admitted.length, 3);
  assert.equal(busy.ctx.nextLobbyArrival, 1850); // pause between groups
  busy.crowd(true);
  busy.ctx.stepLobbyArrivals(5000);
  assert.equal(busy.admitted.length, 3);
  busy.crowd(false);
  busy.ctx.stepLobbyArrivals(5000);
  assert.equal(busy.admitted.length, 4); // no catch-up flood
  busy.full();
  busy.ctx.stepLobbyArrivals(10000);
  assert.equal(busy.admitted.length, 4);

  const medium = setup(20);
  medium.ctx.stepLobbyArrivals(0);
  medium.ctx.stepLobbyArrivals(350);
  assert.equal(medium.ctx.nextLobbyArrival, 1500); // pair, then pause
  for (const [key] of medium.pending) if (Number(key) >= 7) medium.pending.delete(key);
  medium.ctx.stepLobbyArrivals(1500);
  assert.equal(medium.ctx.nextLobbyArrival, 3300); // five left: relaxed again

  const moderate = setup(8);
  moderate.ctx.stepLobbyArrivals(0);
  assert.equal(moderate.ctx.nextLobbyArrival, 1150);
  assert.deepEqual(busy.admitted, ['0', '1', '2', '3']); // FIFO preserved
});
