'use strict';

// Keep host visibility gating separate from the viewer's choice in OBS.
function createCaptures({ request, sceneName, filterName, log = () => {} }) {
  let targets = [], selected = null;
  function configure(items) {
    const previous = selected;
    targets = items.map(item => ({ name: item.sourceName, id: item.sceneItemId,
      enabled: item.sceneItemEnabled, index: item.sceneItemIndex || 0, echoes: [], quad: null }));
    selected = targets.some(t => t.name === previous) ? previous
      : targets.filter(t => t.enabled).sort((a, b) => b.index - a.index)[0]?.name || null;
  }
  function visibility(event) {
    if (event.sceneName !== sceneName) return false;
    const target = targets.find(t => t.id === event.sceneItemId);
    if (!target) return false;
    target.enabled = event.sceneItemEnabled;
    // Our automatic hide/show events must never overwrite the user's selection.
    if (target.echoes[0] === event.sceneItemEnabled) { target.echoes.shift(); return false; }
    if (event.sceneItemEnabled) selected = target.name;
    else if (selected === target.name) selected = null;
    log(`screen source: ${selected || 'none'}`);
    return true;
  }
  async function enabled(target, value) {
    if (target.enabled === value) return;
    target.echoes.push(value);
    target.enabled = value;
    try {
      await request('SetSceneItemEnabled', { sceneName, sceneItemId: target.id, sceneItemEnabled: value });
    } catch (error) { target.echoes = []; target.enabled = !value; throw error; }
  }
  async function render({ film, quad, active = true }) {
    const settings = { ...(quad || {}), Cinema_Visible: !!(active && film && quad) };
    const key = JSON.stringify(settings);
    // Host visibility uses shader alpha, leaving the selected eye icon enabled.
    for (const target of targets) {
      if (target.quad !== key) {
        await request('SetSourceFilterSettings', { sourceName: target.name,
          filterName, filterSettings: settings, overlay: true });
        target.quad = key;
      }
    }
    const chosen = targets.find(t => t.name === selected);
    for (const target of targets) if (!active || target !== chosen) await enabled(target, false);
    if (active && chosen) await enabled(chosen, true);
  }
  return { configure, visibility, render, selected: () => selected };
}
module.exports = { createCaptures };
