/* One output's lobby-to-auditorium membership. No chat connection or fake traffic. */
(function (root) {
  'use strict';
  function create() {
    const guests = new Map();
    let receive = null, transfers = 0;
    const key = (nick) => String(nick || '').trim().toLowerCase();
    function deliver(guest) {
      if (!receive || guest.delivered || guest.place !== 'auditorium') return;
      try {
        if (receive(guest.message) !== false) guest.delivered = true;
      } catch (error) { console.error('[journey] auditorium handoff', error); }
    }
    return {
      location(nick) { return guests.get(key(nick))?.place || null; },
      claimLobby(nick) {
        const k = key(nick);
        if (!k || guests.has(k) || guests.size >= 1024) return false;
        guests.set(k, { place: 'lobby' });
        return true;
      },
      handoff(message) {
        const guest = guests.get(key(message.nick));
        if (!guest || guest.place !== 'lobby') return false;
        guest.place = 'auditorium';
        guest.message = JSON.parse(JSON.stringify(message));
        guest.delivered = false;
        transfers++;
        deliver(guest);
        return true;
      },
      release(nick, place) {
        const k = key(nick);
        if (guests.get(k)?.place === place) guests.delete(k);
      },
      onAuditoriumArrival(fn) {
        receive = fn;
        // Also recover membership if only the auditorium frame was refreshed.
        for (const guest of guests.values()) {
          guest.delivered = false;
          deliver(guest);
        }
      },
      retry() { for (const guest of guests.values()) deliver(guest); },
      stats() {
        let lobby = 0, auditorium = 0;
        for (const guest of guests.values()) guest.place === 'lobby' ? lobby++ : auditorium++;
        return { lobby, auditorium, transfers };
      },
    };
  }
  if (typeof module === 'object' && module.exports) module.exports = { create };
  else root.CinemaJourney = { create };
})(typeof window !== 'undefined' ? window : globalThis);
