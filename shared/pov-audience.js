(() => {
  'use strict';

  const STAGE_WIDTH = 1920;
  const STAGE_HEIGHT = 1080;
  const Z_PIXELS_PER_METRE = 73.48469228349535;
  const SCREEN_MARGIN = 16;
  const SCREEN_FADE = 24;
  const SEATED_ROW_SCALE = { E: 1.6, D: 1.4, C: 1.1 };
  const unit = (value) => Math.max(0, Math.min(1, value));

  async function load(layer) {
    const response = await fetch('assets/auditorium-pov-audience.json');
    if (!response.ok) throw new Error('POV camera data is unavailable');
    const { matrix, quad, width, height, depth, seatBacks } = await response.json();
    if (!seatBacks) throw new Error('POV seat-back anchors are unavailable');
    const roomDepth = Uint8Array.from(atob(depth), (byte) => byte.charCodeAt(0));
    if (roomDepth.length !== width * height) throw new Error('POV depth dimensions do not match');
    const [mx, my, , mw] = matrix;
    const cellWidth = STAGE_WIDTH / width;
    const cellHeight = STAGE_HEIGHT / height;
    const views = new WeakMap();
    const screen = {
      left: Math.min(...quad.map(([x]) => x)) - SCREEN_MARGIN,
      right: Math.max(...quad.map(([x]) => x)) + SCREEN_MARGIN,
      top: Math.min(...quad.map(([, y]) => y)) - SCREEN_MARGIN,
      bottom: Math.max(...quad.map(([, y]) => y)) + SCREEN_MARGIN,
    };

    function project(u, v, z) {
      // Auditorium routes use metres across/down the room and layout pixels for elevation.
      const dot = (row) => row[0] * u - row[1] * v + row[2] * z + row[3];
      const distance = dot(mw);
      if (distance < .35) return null;
      return [(dot(mx) / distance + 1) * STAGE_WIDTH / 2,
        (1 - dot(my) / distance) * STAGE_HEIGHT / 2, distance];
    }

    function visiblePath(left, top, spriteWidth, exposedHeight, topDepth, bottomDepth, seated) {
      const col0 = Math.max(0, Math.floor(left / cellWidth));
      const col1 = Math.min(width, Math.ceil((left + spriteWidth) / cellWidth));
      const row0 = Math.max(0, Math.floor(top / cellHeight));
      const row1 = Math.min(height, Math.ceil((top + exposedHeight) / cellHeight));
      let path = '';
      let occluded = seated;
      for (let row = row0; row < row1; row++) {
        const y0 = Math.max(0, row * cellHeight - top);
        const y1 = Math.min(exposedHeight, (row + 1) * cellHeight - top);
        const spriteDepth = topDepth + (bottomDepth - topDepth) * (y0 + y1) / (2 * exposedHeight);
        let run = -1;
        for (let col = col0; col <= col1; col++) {
          if (col < col1 && roomDepth[row * width + col] / 10 + .075 >= spriteDepth) {
            if (run < 0) run = col;
            continue;
          }
          if (col < col1) occluded = true;
          if (run < 0) continue;
          const x0 = Math.max(0, run * cellWidth - left);
          const x1 = Math.min(spriteWidth, col * cellWidth - left);
          path += `M${x0} ${y0}H${x1}V${y1}H${x0}Z`;
          run = -1;
        }
      }
      if (!path) return null;
      return occluded ? `path('${path}')` : '';
    }

    function remove(walker) {
      views.get(walker)?.element.remove();
      views.delete(walker);
    }

    function seatedBounds(walker, lift) {
      const { row, u } = walker.seat;
      const back = seatBacks[`${row.name}:${u.toFixed(3)}`];
      if (!back) return null;
      const [center, crest, backWidth, depth] = back;
      // The front row only peeks over the crest. The next rows show a little more
      // of each emote, with every sprite kept narrower than its own backrest.
      const front = row.name === 'B';
      const distancePeek = front ? Math.min(18, 124 / depth) : Math.min(52, 26 + 48 / depth);
      const rise = Math.min(2, lift * .35) - 2 * (walker.dozeK || 0);
      const rowScale = SEATED_ROW_SCALE[row.name] ?? 1;
      const peek = Math.round(Math.min(backWidth * .30, distancePeek) * rowScale + rise);
      const spriteHeight = Math.round(peek * (front ? 2.5 : 2.2));
      const spriteWidth = Math.round(Math.min(backWidth * .59, spriteHeight * walker.emW / walker.emH));
      const top = Math.round(crest) - peek;
      return { left: Math.round(center - spriteWidth / 2), top, spriteWidth, spriteHeight,
        exposedHeight: peek, topDepth: depth, bottomDepth: depth };
    }

    function walkingBounds(walker, lift) {
      const [u, v, z] = walker.pos;
      const elevation = (z + lift) / Z_PIXELS_PER_METRE;
      const base = project(u, v, elevation);
      const head = base && project(u, v, elevation + .78);
      if (!head || base[1] <= head[1]) return null;

      const projectedHeight = base[1] - head[1];
      const spriteHeight = Math.min(Math.round(projectedHeight), 104);
      const spriteWidth = Math.round(spriteHeight * Math.min(walker.emW / walker.emH, .92));
      const top = Math.round(base[1] - spriteHeight);
      const depthAt = (y) => head[2] + (base[2] - head[2]) * unit((y - head[1]) / projectedHeight);
      return { left: Math.round(head[0] - spriteWidth / 2), top, spriteWidth, spriteHeight,
        exposedHeight: spriteHeight, topDepth: depthAt(top), bottomDepth: base[2] };
    }

    function draw(walker, lift, tilt, squash) {
      const current = views.get(walker);
      const bounds = walker.seen && (walker.sitting ? seatedBounds(walker, lift) : walkingBounds(walker, lift));
      if (!bounds) { remove(walker); return; }
      const { left, top, spriteWidth, spriteHeight, exposedHeight, topDepth, bottomDepth } = bounds;
      if (spriteHeight < 2 || spriteWidth < 2 || left >= STAGE_WIDTH || left + spriteWidth <= 0
          || top >= STAGE_HEIGHT || top + exposedHeight <= 0) { remove(walker); return; }

      // Fade the whole avatar near the screen to avoid cutting it off at the movie frame.
      const clearance = Math.max(screen.left - left - spriteWidth, left - screen.right,
        screen.top - top - exposedHeight, top - screen.bottom);
      const screenFade = unit(clearance / SCREEN_FADE);
      const nearFade = unit((bottomDepth - .65) / 1.05);
      const alpha = walker.alpha * screenFade * nearFade;
      if (alpha < .005) { remove(walker); return; }

      const geometry = `${left},${top},${spriteWidth},${spriteHeight},${exposedHeight},${topDepth.toFixed(2)},${bottomDepth.toFixed(2)}`;
      const clip = current?.geometry === geometry ? current.clip
        : visiblePath(left, top, spriteWidth, exposedHeight, topDepth, bottomDepth, walker.sitting);
      if (clip === null) { remove(walker); return; }

      const view = current || { element: layer.appendChild(document.createElement('div')) };
      const source = walker.em.firstElementChild;
      if (view.source !== source) {
        view.sprite = walker.em.cloneNode(true);
        view.sprite.style.cssText = walker.em.style.cssText;
        Object.assign(view.sprite.style, { position: 'absolute', top: '0', left: '0', bottom: 'auto',
          clipPath: 'none', transformOrigin: 'center bottom' });
        view.element.replaceChildren(view.sprite);
        view.source = source;
        view.motion = null;
      }
      if (view.geometry !== geometry) {
        Object.assign(view.element.style, { position: 'absolute', width: `${spriteWidth}px`, height: `${spriteHeight}px`,
          transform: `translate(${left}px, ${top}px)`, clipPath: clip, zIndex: String(3000 - Math.round(bottomDepth * 100)) });
        view.geometry = geometry;
        view.clip = clip;
      }
      const flip = walker.em.dataset.flip === 'true' ? -1 : 1;
      // Scale the original live emote so animated sprite sheets and fallbacks keep working.
      const lean = walker.sitting ? tilt * .4 : tilt;
      const motion = `translateX(${(spriteWidth - walker.emW) / 2}px) translateY(${spriteHeight - walker.emH}px) rotate(${lean.toFixed(1)}deg) scale(${(flip * spriteWidth / walker.emW * (2 - squash)).toFixed(3)}, ${(spriteHeight / walker.emH * squash).toFixed(3)})`;
      if (view.motion !== motion) { view.sprite.style.transform = motion; view.motion = motion; }
      const opacity = alpha.toFixed(3);
      if (view.opacity !== opacity) { view.element.style.opacity = opacity; view.opacity = opacity; }
      if (!current) views.set(walker, view);
    }

    return { quad, draw, remove };
  }

  window.CinemaPovAudience = { load };
})();

