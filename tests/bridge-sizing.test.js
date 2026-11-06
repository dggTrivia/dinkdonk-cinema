'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {fitCapture}=require('../bridge-sizing');
function harness(helper=false) {
 const calls=[];
 const target={sourceName:'capture',sceneItemId:2,sourceType:helper?'OBS_SOURCE_TYPE_SCENE':'OBS_SOURCE_TYPE_INPUT'};
 return {calls,async request(type,data){calls.push({type,data});
 if(type==='GetVideoSettings') return {baseWidth:1920,baseHeight:1080};
 if(type==='GetSceneItemList') return {sceneItems:data.sceneName==='main'?[target]:[
 {sceneItemId:3,inputKind:'window_capture'},{sceneItemId:4,inputKind:'text_gdiplus_v2'}]};
 return {};}};
}
test('direct captured window has a fixed full-canvas box after the corner-pin filter',async()=>{
 const h=harness();await fitCapture(h.request,'main','capture');
 const t=h.calls.find(c=>c.type==='SetSceneItemTransform').data.sceneItemTransform;
 assert.equal(t.boundsType,'OBS_BOUNDS_STRETCH');assert.equal(t.boundsWidth,1920);assert.equal(t.boundsHeight,1080);
 assert.equal(t.positionX,0);assert.equal(t.positionY,0);assert.equal(t.rotation,0);assert.equal(t.cropLeft,0);
 assert(!('sourceWidth' in t)); // persistent bounds, independent of current window size
});
test('helper preserves capture aspect ratio and crops without touching unrelated sources',async()=>{
 const h=harness(true);await fitCapture(h.request,'main','capture');
 const writes=h.calls.filter(c=>c.type==='SetSceneItemTransform');assert.equal(writes.length,2);
 assert.equal(writes[1].data.sceneName,'capture');assert.equal(writes[1].data.sceneItemId,3);
 assert.equal(writes[1].data.sceneItemTransform.boundsType,'OBS_BOUNDS_SCALE_INNER');
 assert(!('cropLeft' in writes[1].data.sceneItemTransform));
});
test('missing target and invalid canvas cannot change transforms',async()=>{
 const h=harness();await assert.rejects(fitCapture(h.request,'main','missing'),/missing/);
 assert(!h.calls.some(c=>c.type==='SetSceneItemTransform'));
 await assert.rejects(fitCapture(async()=>({baseWidth:0,baseHeight:1080}),'main','capture'),/canvas/);
});
