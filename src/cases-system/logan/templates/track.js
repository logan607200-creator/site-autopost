// 전화·카톡 클릭 전환 기록(position = 링크가 든 가장 가까운 구역) · 모바일 메뉴 Esc/바깥 탭으로 닫기. 없어도 페이지는 동작.
(function(){
var M='details.cases-menu,details.g-menu';
function shut(d){d.open=false;var s=d.querySelector('summary');if(s){s.setAttribute('aria-expanded','false');s.setAttribute('aria-label','메뉴 열기');}}
document.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a[href^="tel:"],a[href*="pf.kakao.com"]');
  if(a){var t=a.href.indexOf('tel:')===0?'call':'kakao';var c=a.closest('.callbar,header,footer,section,.cta,nav');
    var P=c?(c.id||c.classList[0]||c.tagName.toLowerCase()):'page';
    if(window.gtag)gtag('event','contact_'+t,{method:t,position:P,page_type:'case'});}
  document.querySelectorAll(M).forEach(function(d){if(d.open&&!d.contains(e.target))shut(d);});
  var sm=e.target.closest&&e.target.closest('summary');if(sm&&sm.parentNode.matches(M))sm.setAttribute('aria-expanded',sm.parentNode.open?'false':'true');
});
document.addEventListener('keydown',function(e){if(e.key!=='Escape')return;
  document.querySelectorAll(M).forEach(function(d){if(d.open){shut(d);var s=d.querySelector('summary');if(s)s.focus();}});});
document.querySelectorAll(M).forEach(function(d){var s=d.querySelector('summary');
  d.addEventListener('toggle',function(){if(s){s.setAttribute('aria-expanded',d.open?'true':'false');s.setAttribute('aria-label',d.open?'메뉴 닫기':'메뉴 열기');}});});
})();
