// reserve.js - 예약 페이지 여행객 관리, 금액 계산 및 약관 동의 스크립트

document.addEventListener('DOMContentLoaded', function() {
  const app = document.getElementById('reserveApp');
  if (!app) return;

  const originalPricePerPerson = parseInt(app.dataset.unitOriginalPrice, 10) || 0;
  const discountPerPerson = parseInt(app.dataset.unitDiscount, 10) || 0;
  const finalPricePerPerson = parseInt(app.dataset.unitFinalPrice, 10) || 0;
  let currentHeadcount = parseInt(app.dataset.headcount, 10) || 1;
  const isMember = app.dataset.isMember === 'true';
  const loggedUserName = app.dataset.userName || '';
  const loggedUserPhone = app.dataset.userPhone || '';

  let isSameAsReserver = false; // 대표여행객 = 예약자와 동일 여부

  function getReserverInfo() {
    if (isMember && loggedUserName) {
      return {
        name: loggedUserName,
        phone: loggedUserPhone
      };
    } else {
      const gNameEl = document.getElementById('guest_name');
      const gPhoneEl = document.getElementById('guest_phone');
      const gName = gNameEl ? gNameEl.value.trim() : '';
      const gPhone = gPhoneEl ? gPhoneEl.value.trim() : '';
      return {
        name: gName || '예약자 (미입력)',
        phone: gPhone || '연락처 미입력'
      };
    }
  }

  // 대표여행객 '예약자와 동일' 토글 함수 (전역 window 바인딩)
  window.toggleSameAsReserver = function() {
    isSameAsReserver = !isSameAsReserver;
    renderTravelerForms(currentHeadcount);
  };

  // 인원수 변경 함수 (전역 window 바인딩)
  window.changeHeadcount = function(delta) {
    let newCount = currentHeadcount + delta;
    if (newCount < 1) newCount = 1;
    if (newCount > 20) newCount = 20;
    if (newCount === currentHeadcount) return;

    currentHeadcount = newCount;
    const inputEl = document.getElementById('headcountInput');
    const formCountEl = document.getElementById('formHeadcount');
    const labelCountEl = document.getElementById('labelTravelerCount');

    if (inputEl) inputEl.value = currentHeadcount;
    if (formCountEl) formCountEl.value = currentHeadcount;
    if (labelCountEl) labelCountEl.innerText = currentHeadcount;

    renderTravelerForms(currentHeadcount);
    updateSummary(currentHeadcount);
  };

  // 금액 요약 갱신
  function updateSummary(count) {
    const totalOrig = originalPricePerPerson * count;
    const totalDisc = discountPerPerson * count;
    const totalFin = finalPricePerPerson * count;

    const summaryOrig = document.getElementById('summaryOriginal');
    if (summaryOrig) summaryOrig.innerText = totalOrig.toLocaleString() + '원';

    const discEl = document.getElementById('summaryDiscount');
    if (discEl) {
      if (isMember) {
        discEl.innerText = '- ' + totalDisc.toLocaleString() + '원';
      } else {
        discEl.innerText = '0원 (비회원 정가)';
      }
    }

    const summaryHeadcount = document.getElementById('summaryHeadcount');
    if (summaryHeadcount) summaryHeadcount.innerText = count + '명';

    const summaryFinal = document.getElementById('summaryFinal');
    if (summaryFinal) summaryFinal.innerText = totalFin.toLocaleString() + '원';
  }

  // 대표 여행객 미리보기 실시간 동기화
  function syncReserverPreview() {
    if (!isSameAsReserver) return;
    const reserver = getReserverInfo();
    const namePrev = document.getElementById('repNamePreview');
    const phonePrev = document.getElementById('repPhonePreview');
    const hiddenName = document.getElementById('repHiddenName');
    const hiddenPhone = document.getElementById('repHiddenPhone');

    if (namePrev) namePrev.innerText = reserver.name;
    if (phonePrev) phonePrev.innerText = reserver.phone;
    if (hiddenName) hiddenName.value = reserver.name;
    if (hiddenPhone) hiddenPhone.value = reserver.phone;
  }

  // 여행객 폼 렌더링
  function renderTravelerForms(count) {
    const container = document.getElementById('travelersContainer');
    if (!container) return;

    const prevNames = Array.from(document.querySelectorAll('input[name="traveler_name[]"]')).map(el => el.value);
    const prevGenders = Array.from(document.querySelectorAll('select[name="traveler_gender[]"]')).map(el => el.value);
    const prevPhones = Array.from(document.querySelectorAll('input[name="traveler_phone[]"]')).map(el => el.value);
    const prevBirths = Array.from(document.querySelectorAll('input[name="traveler_birth[]"]')).map(el => el.value);

    container.innerHTML = '';
    const reserver = getReserverInfo();

    for (let i = 0; i < count; i++) {
      const card = document.createElement('div');
      card.className = 'traveler-card';

      const isRep = (i === 0);
      const title = isRep ? '여행객 1 (대표 여행자)' : `여행객 ${i + 1}`;
      const nameVal = prevNames[i] || '';
      const genderVal = prevGenders[i] || '남';
      const phoneVal = prevPhones[i] || '';
      const birthVal = prevBirths[i] || '';

      if (isRep) {
        // 대표 여행객 카드
        card.innerHTML = `
          <div class="traveler-card-header">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>👤 ${title}</span>
              <span style="font-size:12px; color:var(--primary); font-weight:600;">대표자</span>
            </div>
            <button type="button" class="btn-same-as-reserver ${isSameAsReserver ? 'active' : ''}" onclick="toggleSameAsReserver()">
              <span>${isSameAsReserver ? '✓' : '＋'}</span> 예약자와 동일
            </button>
          </div>
          ${isSameAsReserver ? `
            <div class="rep-same-notice">
              <div class="rep-notice-content">
                <span class="rep-notice-icon">📋</span>
                <div class="rep-notice-text">
                  <strong>예약자 정보로 자동 등록됩니다.</strong>
                  <p>성명: <span id="repNamePreview">${reserver.name}</span> | 연락처: <span id="repPhonePreview">${reserver.phone}</span> (추가 입력 불필요)</p>
                </div>
              </div>
              <button type="button" class="btn-rep-edit" onclick="toggleSameAsReserver()">직접 입력</button>
            </div>
            <input type="hidden" name="traveler_name[]" id="repHiddenName" value="${reserver.name}">
            <input type="hidden" name="traveler_gender[]" value="미지정">
            <input type="hidden" name="traveler_phone[]" id="repHiddenPhone" value="${reserver.phone}">
            <input type="hidden" name="traveler_birth[]" value="-">
          ` : `
            <div class="traveler-form-grid">
              <div class="form-group">
                <label class="form-label">이름 *</label>
                <input type="text" name="traveler_name[]" value="${nameVal}" required class="form-control" placeholder="성함">
              </div>
              <div class="form-group">
                <label class="form-label">성별 *</label>
                <select name="traveler_gender[]" class="form-control">
                  <option value="남" ${genderVal === '남' ? 'selected' : ''}>남</option>
                  <option value="여" ${genderVal === '여' ? 'selected' : ''}>여</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">전화번호 *</label>
                <input type="tel" name="traveler_phone[]" value="${phoneVal}" required class="form-control" placeholder="010-0000-0000">
              </div>
              <div class="form-group">
                <label class="form-label">생년월일 *</label>
                <input type="date" name="traveler_birth[]" value="${birthVal}" required class="form-control">
              </div>
            </div>
          `}
        `;
      } else {
        // 동행 여행객 카드 (2번, 3번 ...)
        card.innerHTML = `
          <div class="traveler-card-header">
            <span>👤 ${title}</span>
          </div>
          <div class="traveler-form-grid">
            <div class="form-group">
              <label class="form-label">이름 *</label>
              <input type="text" name="traveler_name[]" value="${nameVal}" required class="form-control" placeholder="성함">
            </div>
            <div class="form-group">
              <label class="form-label">성별 *</label>
              <select name="traveler_gender[]" class="form-control">
                <option value="남" ${genderVal === '남' ? 'selected' : ''}>남</option>
                <option value="여" ${genderVal === '여' ? 'selected' : ''}>여</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">전화번호 *</label>
              <input type="tel" name="traveler_phone[]" value="${phoneVal}" required class="form-control" placeholder="010-0000-0000">
            </div>
            <div class="form-group">
              <label class="form-label">생년월일 *</label>
              <input type="date" name="traveler_birth[]" value="${birthVal}" required class="form-control">
            </div>
          </div>
        `;
      }
      container.appendChild(card);
    }
  }

  // 비회원 예약자 입력 시 실시간 연동 리스너
  const gNameEl = document.getElementById('guest_name');
  const gPhoneEl = document.getElementById('guest_phone');
  if (gNameEl) gNameEl.addEventListener('input', syncReserverPreview);
  if (gPhoneEl) gPhoneEl.addEventListener('input', syncReserverPreview);

  // 약관 전체 동의 핸들러
  window.handleAgreeAllChange = function(isChecked) {
    const termChecks = document.querySelectorAll('.term-item-check');
    termChecks.forEach(chk => {
      chk.checked = isChecked;
    });
  };

  window.toggleAgreeAll = function(event) {
    if (event.target.tagName.toLowerCase() === 'input') return;
    const agreeAll = document.getElementById('agreeAll');
    if (!agreeAll) return;
    agreeAll.checked = !agreeAll.checked;
    window.handleAgreeAllChange(agreeAll.checked);
  };

  function updateAgreeAllStatus() {
    const termChecks = document.querySelectorAll('.term-item-check');
    const allChecked = Array.from(termChecks).every(chk => chk.checked);
    const agreeAll = document.getElementById('agreeAll');
    if (agreeAll) agreeAll.checked = allChecked;
  }

  const termChecks = document.querySelectorAll('.term-item-check');
  termChecks.forEach(chk => {
    chk.addEventListener('change', updateAgreeAllStatus);
  });

  // 전문보기 토글
  window.toggleDetail = function(detailId) {
    const el = document.getElementById(detailId);
    if (!el) return;
    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
  };

  // 폼 제출 시 필수 약관 체크 여부 검증
  const form = document.getElementById('reserveForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      const requiredTerms = document.querySelectorAll('.term-required');
      let allRequiredChecked = true;
      let firstUnchecked = null;

      requiredTerms.forEach(chk => {
        if (!chk.checked) {
          allRequiredChecked = false;
          if (!firstUnchecked) firstUnchecked = chk;
        }
      });

      if (!allRequiredChecked) {
        e.preventDefault();
        alert('필수 약관(국내여행 특별약관, 개인정보 제3자 제공동의, 민감정보 수집 및 이용 동의)에 모두 동의하셔야 결제를 진행하실 수 있습니다.');
        if (firstUnchecked) {
          firstUnchecked.focus();
          const termsSection = document.getElementById('termsSection');
          if (termsSection) {
            termsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      }
    });
  }

  // 초기 실행
  renderTravelerForms(currentHeadcount);
  updateSummary(currentHeadcount);
});

