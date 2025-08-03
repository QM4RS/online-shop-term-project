// ---- Dark-Mode ----
(function(){
  const root=document.documentElement;
  const toggle=document.createElement('button');
  toggle.id='themeToggle';      // استایل میدیمش
  toggle.innerHTML='🌙';        // پیش‌فرض آیکن ماه
  document.body.appendChild(toggle);

  // حالت فعلی
  let dark = localStorage.getItem('dark') === '1';
  setTheme(dark);

  function setTheme(enableDark){
    dark = enableDark;
    root.classList.toggle('dark', dark);
    toggle.innerHTML = dark ? '☀️' : '🌙';
    localStorage.setItem('dark', dark ? '1' : '0');
  }

  toggle.addEventListener('click', ()=> setTheme(!dark));
})();

function showToast(message, type='success', duration=2800){
  const t=document.getElementById('toast');
  t.textContent=message;
  t.className=`toast ${type} show`;
  setTimeout(()=>{ t.className='toast'; }, duration);
}
const styleFab=document.createElement('style');
styleFab.textContent=`.cart-fab.bounce{animation:fabBounce .6s ease;}`;
document.head.appendChild(styleFab);

(function(){
  const overlay=document.getElementById('authOverlay');
  const loginPane=document.getElementById('loginPane');
  const regPane=document.getElementById('regPane');

  // باز کردن مودال
  document.getElementById('navLogin')?.addEventListener('click',e=>{
    e.preventDefault(); showPane('login');
  });
  document.getElementById('navRegister')?.addEventListener('click',e=>{
    e.preventDefault(); showPane('reg');
  });

  document.getElementById('ctaRegister')?.addEventListener('click', e=>{
  e.preventDefault(); showPane('reg');
});

  // سوییچ داخل مودال
  document.getElementById('showReg')?.addEventListener('click',e=>{
    e.preventDefault(); showPane('reg');
  });
  document.getElementById('showLogin')?.addEventListener('click',e=>{
    e.preventDefault(); showPane('login');
  });

  // بستن
  document.getElementById('closeAuth').addEventListener('click', hide);
  overlay.addEventListener('click',e=>{ if(e.target===overlay) hide(); });

  function showPane(type){
    loginPane.style.display= type==='login' ? 'block':'none';
    regPane.style.display  = type==='reg'   ? 'block':'none';
    overlay.classList.add('show');
  }
  function hide(){ overlay.classList.remove('show'); }
})();

function showConfirm(message){
  return new Promise(resolve=>{
    const ov=document.getElementById('confirmOverlay');
    document.getElementById('confirmMsg').textContent=message;
    ov.classList.add('show');
    const yes = ()=>{ cleanup(); resolve(true); };
    const no  = ()=>{ cleanup(); resolve(false); };
    function cleanup(){
      ov.classList.remove('show');
      y.removeEventListener('click',yes); n.removeEventListener('click',no);
    }
    const y=document.getElementById('confirmYes');
    const n=document.getElementById('confirmNo');
    y.addEventListener('click',yes); n.addEventListener('click',no);
  });
}

function askQuantity(action){
  return new Promise(resolve=>{
    const ov = document.getElementById('qtyOverlay');
    const msg= document.getElementById('qtyMsg');
    const inp= document.getElementById('qtyInput');
    msg.textContent = action==='inc' ? 'چند عدد اضافه شود؟' : 'چند عدد کم شود؟';
    inp.value = 1; inp.focus();
    ov.classList.add('show');

    const yes = ()=>{ const v=parseInt(inp.value,10)||0; cleanup(); resolve(v>0?v:null); };
    const no  = ()=>{ cleanup(); resolve(null); };
    function cleanup(){
      ov.classList.remove('show');
      y.removeEventListener('click',yes);
      n.removeEventListener('click',no);
    }
    const y=document.getElementById('qtyYes');
    const n=document.getElementById('qtyNo');
    y.addEventListener('click',yes);
    n.addEventListener('click',no);
  });
}


document.addEventListener('DOMContentLoaded', () => {
    // کارت‌ها
    document.querySelectorAll('.product-card').forEach(card=>{
const wrap = card.querySelector('.img-wrap');
const img  = wrap.querySelector('img');
wrap.classList.add('loading');

const skel = document.createElement('div');
skel.className = 'skeleton';
wrap.appendChild(skel);

function removeSkeleton(){
  wrap.classList.remove('loading');
  skel.remove();            // خود اسکلت هم حذف می‌شه
}

img.addEventListener('load', removeSkeleton);

/* اگر تصویر همین حالا لود شده (کش)، فوراً Skeleton رو بردار */
if(img.complete){
  removeSkeleton();
}

  const pid = card.dataset.id;
  const btn = card.querySelector('.add-btn');
  const inStock = parseInt(card.querySelector('.stock-badge').textContent) > 0;

  if(!inStock){
    btn.disabled = true;
    btn.textContent = 'ناموجود';
    btn.style.background = 'var(--secondary)';
    return;                    // ⬅️ دیگه لیسنر اضافه نکن
  }

  btn.addEventListener('click', async e=>{
    e.stopPropagation();
    e.preventDefault();

    const loggedIn = document.body.classList.contains('logged-in');
    if(!loggedIn){ window.location.href='/login'; return; }

    const res = await fetch(`/api/cart/add/${pid}`,{method:'POST'});
const fab=document.querySelector('.cart-fab');
if(fab){
  fab.classList.add('pulse');
  setTimeout(()=>fab.classList.remove('pulse'),500);
}

    if(res.ok) window.location.reload();
  });
});

});

const adminMenu = document.getElementById('adminMenu');
let drag = false, offsetX = 0, offsetY = 0;
adminMenu.addEventListener('mousedown', e=>{
  drag = true;
  offsetX = e.offsetX;
  offsetY = e.offsetY;
});
document.addEventListener('mousemove', e=>{
  if(!drag) return;
  adminMenu.style.top  = (e.pageY - offsetY) + 'px';
  adminMenu.style.left = (e.pageX - offsetX) + 'px';
});
document.addEventListener('mouseup', ()=> drag=false);

if (adminMenu) {
    let targetCard = null;

    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('contextmenu', e => {
            e.preventDefault();
            targetCard = card;
            adminMenu.style.top = e.pageY + 'px';
            adminMenu.style.left = e.pageX + 'px';
            adminMenu.style.display = 'block';
        });
    });

    document.addEventListener('click', () => adminMenu.style.display = 'none');

    adminMenu.addEventListener('click', async e => {
        const action = e.target.dataset.action;
        if (!action) return;
        const pid = targetCard.dataset.id;

        let method = 'POST', url = '';
        if(action==='inc' || action==='dec'){
            const qty = await askQuantity(action);
            adminMenu.style.display='none';
            if(!qty) return;                 // لغو شد
            url = `/api/admin/product/${pid}/${action}?step=${qty}`;
        }

        if(action === 'del'){
          const ok = await showConfirm('محصول حذف شود؟');
          if(!ok){ adminMenu.style.display='none'; return; }
          url=`/api/admin/product/${pid}`; method='DELETE';
        }


        const res = await fetch(url, {method});
        if (res.ok) {
            if (action === 'del') targetCard.remove();
            else alert('موجودی جدید: ' + (await res.json()).stock);
        } else {
            alert('خطا!');
        }
        adminMenu.style.display = 'none';
    });
}

(function(){
  if(!location.pathname.startsWith('/profile')) return;

  /* ----- Top-up فرم ----- */
  const topForm=document.querySelector('form[action="/profile/topup"]');
  topForm?.addEventListener('submit', async e=>{
    e.preventDefault();
    const amount=parseInt(topForm.amount.value,10)||0;
    if(amount<=0){
      showToast('مبلغ نامعتبر ❌','error'); return;
    }
    const res=await fetch('/profile/topup',{method:'POST',body:new FormData(topForm)});
    if(res.ok){
      showToast('موجودی شارژ شد ✅');
      setTimeout(()=>location.reload(),1000);
    }else{
      const err=await res.json();
      showToast(`❌ ${err.detail}`,'error');
    }
  });

  /* ----- Update پروفایل ----- */
  const updForm=document.querySelector('form[action="/profile/update"]');
  updForm?.addEventListener('submit', async e=>{
    e.preventDefault();
    const email=updForm.email.value.trim();
    if(!/^[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)){
      showToast('ایمیل معتبر نیست ❌','error'); return;
    }
    const res=await fetch('/profile/update',{method:'POST',body:new FormData(updForm)});
    if(res.ok){
      showToast('ذخیره شد ✅');
      setTimeout(()=>location.reload(),800);
    }else{
      const err=await res.json();
      showToast(`❌ ${err.detail}`,'error');
    }
  });
})();
