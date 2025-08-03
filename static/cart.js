document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.rm-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const tr = btn.closest('tr');
            const pid = tr.dataset.id;
            const res = await fetch(`/api/cart/remove/${pid}`, {method:'POST'});
            if (res.ok) window.location.reload();
        });
    });

    // تأیید خرید (هنوز هیچی نمی‌کنیم)
    document.getElementById('checkout')?.addEventListener('click', async ()=>{
  const btn=document.getElementById('checkout');
  btn.disabled=true; btn.textContent='در حال پردازش…';
  const res=await fetch('/api/checkout',{method:'POST'});
  if(res.ok){
    const data=await res.json();
    showToast(`✅ خرید انجام شد (سفارش #${data.order_id})`,'success');
    setTimeout(()=>location.href='/profile',1500);
  }else{
    const err=await res.json();
    showToast(`❌ ${err.detail}`,'error');
    btn.disabled=false; btn.textContent='تأیید خرید';
  }
});
});
