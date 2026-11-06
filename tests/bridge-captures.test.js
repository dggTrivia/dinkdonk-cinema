'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createCaptures}=require('../bridge-captures');
const names=['firefoxBrowserCinema','mpvCinema'];
const quad={Top_Left_X:-70,Top_Left_Y:-50};
function make(initial=[true,false]){
 const calls=[],visible=new Map(initial.map((v,i)=>[i+1,v]));let c;
 c=createCaptures({sceneName:'main',filterName:'pin',async request(type,data){calls.push({type,data});
 if(type==='SetSceneItemEnabled'){visible.set(data.sceneItemId,data.sceneItemEnabled);c.visibility({...data});}return {};}});
 c.configure(names.map((name,i)=>({sourceName:name,sceneItemId:i+1,sceneItemIndex:i,sceneItemEnabled:initial[i]})));
 const user=(id,value)=>{visible.set(id,value);return c.visibility({sceneName:'main',sceneItemId:id,sceneItemEnabled:value})};
 return {c,calls,visible,user};
}
test('OBS-selected capture follows corners and the other stays hidden',async()=>{
 const h=make();await h.c.render({film:true,quad});
 assert.equal(h.visible.get(1),true);assert.equal(h.visible.get(2),false);
 assert.equal(h.calls.filter(c=>c.type==='SetSourceFilterSettings').length,2);
 h.user(2,true);await h.c.render({film:true,quad});
 assert.equal(h.c.selected(),names[1]);assert.equal(h.visible.get(1),false);assert.equal(h.visible.get(2),true);
});
test('auditorium dim phase hides pixels through the shader while keeping the selected eye enabled',async()=>{
 const h=make([false,true]);await h.c.render({film:false,quad});
 assert.deepEqual([...h.visible.values()],[false,true]);assert.equal(h.c.selected(),names[1]);
 assert(h.calls.filter(c=>c.type==='SetSourceFilterSettings').every(c=>c.data.filterSettings.Cinema_Visible===false));
 await h.c.render({film:true,quad});assert.deepEqual([...h.visible.values()],[false,true]);
});
test('choosing another source while hidden keeps its eye on with transparent output',async()=>{
 const h=make();await h.c.render({film:false,quad});h.user(2,true);
 await h.c.render({film:false,quad});assert.equal(h.c.selected(),names[1]);
 assert.deepEqual([...h.visible.values()],[false,true]);
 const settings=h.calls.filter(c=>c.type==='SetSourceFilterSettings');
 assert(settings.every(c=>c.data.filterSettings.Cinema_Visible===false));
 await h.c.render({film:true,quad});assert.deepEqual([...h.visible.values()],[false,true]);
});
test('manually hiding the selected source leaves the screen empty',async()=>{
 const h=make();await h.c.render({film:true,quad});h.user(1,false);
 await h.c.render({film:true,quad});assert.equal(h.c.selected(),null);
 assert.deepEqual([...h.visible.values()],[false,false]);
});
test('starts with no capture when both are hidden and ignores unrelated events',async()=>{
 const h=make([false,false]);assert.equal(h.c.selected(),null);
 assert.equal(h.c.visibility({sceneName:'elsewhere',sceneItemId:1,sceneItemEnabled:true}),false);
 await h.c.render({film:true,quad});assert.deepEqual([...h.visible.values()],[false,false]);
});
test('latest user choice wins; repeated identical frames do not repeat OBS writes',async()=>{
 const h=make();h.user(2,true);h.user(1,true);await h.c.render({film:true,quad});
 assert.equal(h.c.selected(),names[0]);assert.deepEqual([...h.visible.values()],[true,false]);
 const n=h.calls.length;await h.c.render({film:true,quad});assert.equal(h.calls.length,n);
});


test('lobby closes both eyes and auditorium restores the remembered selection even in dim phase',async()=>{
 const h=make([false,true]);
 await h.c.render({active:false,film:false,quad});
 assert.deepEqual([...h.visible.values()],[false,false]);
 assert.equal(h.c.selected(),names[1]);
 await h.c.render({active:true,film:false,quad});
 assert.deepEqual([...h.visible.values()],[false,true]);
 assert(h.calls.filter(c=>c.type==='SetSourceFilterSettings').every(c=>c.data.filterSettings.Cinema_Visible===false));
});
