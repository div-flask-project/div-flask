// payment.js - 결제 화면 수단 선택 및 중복 결제 방지 스크립트

document.addEventListener('DOMContentLoaded', function() {
  const paymentForm = document.getElementById('paymentForm');
  const payBtn = document.querySelector('.btn-pay-complete');

  if (paymentForm && payBtn) {
    paymentForm.addEventListener('submit', function() {
      payBtn.disabled = true;
      payBtn.innerText = '결제 처리 중입니다...';
    });
  }

  // 결제 수단 카드 클릭 활성화 효과
  const methodRadios = document.querySelectorAll('input[name="payment_method"]');
  methodRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      methodRadios.forEach(r => {
        const box = r.closest('.pay-method-card').querySelector('.method-box');
        if (box) {
          if (r.checked) {
            box.style.borderColor = 'var(--primary)';
            box.style.background = 'var(--primary-light)';
            box.style.color = 'var(--primary)';
          } else {
            box.style.borderColor = 'var(--border-color)';
            box.style.background = '#ffffff';
            box.style.color = '#334155';
          }
        }
      });
    });
  });
});

