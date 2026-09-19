
var S = { posts:[], intel:[], channels:{}, scan:{}, heartbeat:{} };
var lastLen = 0;
function arr(x){ return Array.isArray(x) ? x : (x ? [x] : []); }
function esc(s){ return (s==null?'':String(s)).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
function chWrap(stateTitle){var c=stateTitle;return '<span class="chan" style="background:var(--'+c+')"></span>';}

function renderChips(){
  var h='';
  function chip(k,label,on){ return '<span class="chip"><span class="dot '+((S.channels[k]>0||on)?'ok':'off')+'"></span><b>'+label+'</b> '+ (+S.channels[k]||0)+'</span>'; }
  h += chip('tg','Telegram');
  var dz = S.dzen||{};
  h += '<span class="chip"><span class="dot '+(dz.linked?'ok':'off')+'"></span><b>Дзен</b> '+(dz.linked?('автокросс TG→Дзен активен с '+esc(dz.linkedAt)):'не связан')+'</span>';
  h += '<div class="sub" style="margin:8px 0 12px">Дзен — авто-зеркало Telegram на платформе Дзен (зеркалятся посты TG, включая подтянутые площадкой). Точные показы/CTR/дочиты — только в панели Дзен: у нас нет их API. Задержка репоста — платформенная.</div>';
  h += '<span class="chip"><span class="dot '+(S.heartbeat.alive?'ok':'bad')+'"></span><b>оркестратор</b> '+(S.heartbeat.alive?('жив '+S.heartbeat.ageSec+' c'):'МЁРТВ')+'</span>';
  h += '<span class="chip"><span class="dot '+(S.scan.todayDone?'ok':'warn')+'"></span><b>intel</b> '+esc(S.scan.lastDate||'—')+' ('+S.scan.rows+' строк)'+(S.scan.todayDone?'': '<span class="upd"> нет скана за сегодня</span>')+'</span>';
  h += '<span class="chip"><span class="dot '+(S.scan.nextScan?'ok':'off')+'"></span><b>скан</b> каждый час → '+esc(S.scan.nextScan)+' · intel '+esc(S.scan.nextIntel)+'</span>';
  h += '<span class="chip"><span class="dot ok"></span><b>всего постов</b> '+S.counts.total+' (на постинг '+S.counts.upcoming+', опубликовано '+S.counts.posted+')</span>';
  document.getElementById('chips').innerHTML = h;
}

function calendarHtml(){
  var mono = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
  var byMonth = {};
  S.posts.forEach(function(p){ var d=new Date(p.d); var k=d.getFullYear()+'-'+(d.getMonth()+1); (byMonth[k]=byMonth[k]||[]).push(p); });
  var today = new Date();
  var yr = today.getFullYear();
  var out = '';
  for(var mon=0; mon<12; mon++){
    var k = yr+'-'+(mon+1);
    var first=new Date(yr,mon,1); var offset=((first.getDay()+6)%7);
    var dim = new Date(yr, mon+1, 0).getDate();
    var days = (byMonth[k]||[]).slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);});
    var map={}; days.forEach(function(p){ var dd=new Date(p.d).getDate(); map[dd]=map[dd]||[]; map[dd].push(p); });
    var isEmpty = !days.length;
    out += '<div class="month'+(isEmpty?' mt-empty':'')+'"><div class="mtitle">'+mono[mon]+' '+yr+'</div>';
    ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'].forEach(function(w){ out += '<span class="wd">'+w+'</span>'; });
    for(var i=0;i<offset;i++){ out += '<span class="day empt"></span>'; }
    for(var d=1; d<=dim; d++){
      var now=new Date(yr,mon,d);
      var isToday = now.toDateString()===today.toDateString();
      out += '<span class="day'+(isToday?' today':'')+'"><span class="num">'+d+'</span>';
      (map[d]||[]).forEach(function(p){
        var chans='';
        if(p.ch.tg)chans+=chWrap('ok'); else chans+=chWrap('off');
        if(p.ch.dz)chans+=chWrap('ok'); else chans+=chWrap('off');
        var img='';
        if(p.img){ img='<img class="th" src="/img/'+esc(p.img)+'.png" alt="">'; }
        out += '<div class="pcell">'+chans+' '+esc(p.title)+img+'</div>';
      });
      out += '</span>';
    }
    out += '</div>';
  }
  return out;
}

function renderCalendar(){
  document.getElementById('p-cal').innerHTML = calendarHtml();
}

function scoreHtml(){
  var now=new Date();
  var out='';
  var posted=0,toPub=0,missed=0;
  S.posts.forEach(function(p){
    var any=p.ch.tg||p.ch.dz;
    if(any)posted++;
    else if(new Date(p.d)>now)toPub++;
    else missed++;
  });
  out+='<div class="sc"><b>'+posted+'</b><span>опубликовано</span></div>';
  out+='<div class="sc"><b>'+toPub+'</b><span>в очереди</span></div>';
  out+='<div class="sc"><b>'+missed+'</b><span>пропущено</span></div>';
  out+='<div class="sc"><b>'+S.posts.length+'</b><span>всего</span></div>';
  return out;
}

function renderMe(){
  document.getElementById('meScore').innerHTML = scoreHtml();
  document.getElementById('meTbl').innerHTML = renderMeTbl();
  document.getElementById('mePrev').innerHTML = renderMePrev();
  document.getElementById('meCal').innerHTML = calendarHtml();
}

function renderMeTbl(){
  var out='<table class="pubtbl"><tr><th>Дата</th><th>Пост</th><th>TG</th><th>ДЗ</th></tr>';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    function cell(on){return '<span class="chan" style="width:10px;height:10px;background:var(--'+(on?'ok':'off')+')"></span>';}
    var now=new Date();
    var dat = new Date(p.d);
    out+= '<tr><td'+((dat>now)?' style="color:var(--acc)"':'')+'>'+esc(p.date)+'</td><td class="pst">'+esc(p.title)+'</td>';
    out+= '<td>'+cell(p.ch.tg)+'</td><td>'+cell(p.ch.dz)+'</td>';
    out+= '</tr>';
  });
  out+='</table>';
  return out;
}

function renderMePrev(){
  var out='';
  var now=new Date();
  var next = S.posts.slice()
    .sort(function(a,b){return new Date(a.d)-new Date(b.d);})
    .filter(function(p){ return !(p.ch.tg||p.ch.dz) && new Date(p.d)>=new Date(now.getTime()-86400000); })
    .slice(0,3);
  if(!next.length){ next = S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).slice(0,3); }
  next.forEach(function(p){
    out += '<div class="item" style="overflow:hidden">';
    if(p.img){ out += '<img style="width:150px;border-radius:6px;float:left;margin-right:12px" src="/img/'+esc(p.img)+'.png" alt="">'; }
    out += '<div class="tt">'+esc(p.title)+'</div>';
    out += '<div style="font-size:11px;color:var(--muted);margin:2px 0 4px">'+esc(p.date)+' · '+esc(p.guid)+'</div>';
    var ds = p.desc ? p.desc.replace(/\\n/g,' ') : '';
    if(ds.length>400){ ds = ds.slice(0,397)+'...'; }
    out += '<div style="font-size:12px;color:var(--head)">'+esc(ds)+'</div>';
    out += '</div>';
  });
  if(!next.length){ out='<div class="sub">постов нет</div>'; }
  return out;
}

function renderNews(){
  var out='<div class="sub">первоисточники, на которые ссылаются посты (из evidence)</div>';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    var n = arr(p.news);
    out += '<div class="item"><div class="tt">'+esc(p.date)+' · '+esc(p.title)+'</div>';
    n.forEach(function(x){
      out += '<div class="newsrow"><a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.title)+'</a> <span class="src">· '+esc(x.file)+'</span></div>';
    });
    out += '</div>';
  });
  document.getElementById('p-news').innerHTML = out;
}

function renderPosts(){
  var out='';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    var chans='';
    function cd(k,nm){ return '<span class="chip"><span class="dot '+((p.ch[k])?'ok':'off')+'"></span>'+nm+'</span>'; }
    chans=cd('tg','TG')+cd('dz','ДЗ');
    var img='';
    if(p.img){ img='<img style="width:110px;border-radius:6px;float:left;margin-right:10px" src="/img/'+esc(p.img)+'.png" alt="">'; }
    out += '<div class="item" style="overflow:hidden">'+img+'<div class="tt">'+esc(p.title)+'</div><div style="font-size:11px;color:var(--muted);margin:2px 0 4px">'+esc(p.date)+' · '+esc(p.guid)+'</div>'+chans+'</div>';
  });
  document.getElementById('p-posts').innerHTML = out;
}

function renderScan(){
  var out='<div class="sub">свежие сканы (intel · '+esc(S.scan.lastDate||'—')+') · '+S.scan.rows+' строк · evidence '+esc(S.scan.evidence)+'</div>';
  arr(S.intel).forEach(function(r){
    out += '<div class="item"><a href="'+esc(r.url)+'" target="_blank" rel="noopener">'+esc(r.title)+'</a><span class="tag">'+esc(r.src)+' · t'+esc(r.tier)+' · score '+esc(r.score)+'</span></div>';
  });
  document.getElementById('p-scan').innerHTML = out;
}

function renderAll(){
  renderChips(); renderCalendar(); renderNews(); renderPosts(); renderScan(); renderMe();
  var g=S.generated||S.now||'';
  var u=document.querySelector('.sub');
  document.getElementById('clk').textContent = new Date().toLocaleTimeString('ru-RU')+' · обновлено '+g;
  document.getElementById('upSince').textContent = S.backend?S.backend.upSince:'';
  document.getElementById('req').textContent = S.backend?S.backend.requests:'';
  document.getElementById('port').textContent = S.backend?S.backend.port:'';
  document.getElementById('meSub').textContent = 'сводка на '+new Date().toLocaleString('ru-RU')+' · обновлено '+g+ (S.backend?' · бэкенд PID '+S.backend.upSince:'');
}

function poll(){
  fetch('/api/state.json').then(function(r){return r.json();}).then(function(s){
    var sig=JSON.stringify(s).length;
    if(sig!==lastLen){ lastLen=sig; S=s; renderAll(); }
  }).catch(function(){ });
}

document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.pane').forEach(function(x){x.classList.remove('on');});
    t.classList.add('on');
    document.getElementById('p-'+t.getAttribute('data-t')).classList.add('on');
  });
});

function switchWin(showId){
  var wins = ['view-main','view-me'];
  wins.forEach(function(w){
    var el = document.getElementById(w);
    if(w===showId){ el.setAttribute('data-active','1'); }
    else { el.setAttribute('data-active','0'); }
  });
  document.getElementById('btnWin').dataset.next = (showId==='view-me' ? 'view-main' : 'view-me');
}
document.getElementById('btnWin').addEventListener('click', function(){
  var nxt = document.getElementById('btnWin').dataset.next || 'view-me';
  switchWin(nxt);
});
document.getElementById('btnMeBack').addEventListener('click', function(){ switchWin('view-main'); });
poll();
setInterval(poll, 10000);
