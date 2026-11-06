'use strict';

// OBS keeps these bounding boxes as source dimensions change (window resize/DPI).
async function fitCapture(request, sceneName, sourceName) {
  const { baseWidth, baseHeight } = await request('GetVideoSettings');
  if (!(baseWidth > 0 && baseHeight > 0)) throw new Error('OBS canvas dimensions are unavailable');
  const { sceneItems } = await request('GetSceneItemList', { sceneName });
  const target = sceneItems.find(item => item.sourceName === sourceName);
  if (!target) throw new Error(`Capture "${sourceName}" is missing from "${sceneName}"`);
  const box = { positionX: 0, positionY: 0, rotation: 0, alignment: 5, boundsAlignment: 0,
    boundsWidth: baseWidth, boundsHeight: baseHeight, scaleX: 1, scaleY: 1 };
  // Corner coordinates cover the entire canvas, so the already-warped source must
  // cover that same rectangle, regardless of the captured window's aspect ratio.
  await request('SetSceneItemTransform', { sceneName, sceneItemId: target.sceneItemId,
    sceneItemTransform: { ...box, boundsType: 'OBS_BOUNDS_STRETCH',
      cropLeft: 0, cropRight: 0, cropTop: 0, cropBottom: 0 } });
  if (target.sourceType === 'OBS_SOURCE_TYPE_SCENE' || target.isGroup) {
    const children = await request(target.isGroup ? 'GetGroupSceneItemList' : 'GetSceneItemList',
      { sceneName: sourceName });
    for (const child of children.sceneItems) {
      if (!['window_capture', 'game_capture'].includes(child.inputKind)) continue;
      // Keep intentional window-chrome crops inside the helper, before its shader.
      await request('SetSceneItemTransform', { sceneName: sourceName, sceneItemId: child.sceneItemId,
        sceneItemTransform: { ...box, boundsType: 'OBS_BOUNDS_SCALE_INNER' } });
    }
  }
  return { width: baseWidth, height: baseHeight };
}
module.exports = { fitCapture };
