// @ts-check
import { test, expect } from '@playwright/test';

test.describe('여행 상품 예약 및 연관 숙박 필터링 테스트', () => {
  test('비회원 예약 화면 기본 필드 및 약관 일괄 동의 동작 확인', async ({ page }) => {
    // 상품 1번 예약 화면 직접 접속
    await page.goto('/order/reserve?product_id=1');

    // 비회원 주문 배지 노출 확인
    await expect(page.locator('.badge:has-text("비회원 주문")')).toBeVisible();

    // 예약자 정보 입력 필드 확인
    await expect(page.locator('#guest_name')).toBeVisible();
    await expect(page.locator('#guest_phone')).toBeVisible();
    await expect(page.locator('#guest_email')).toBeVisible();

    // 여행 출발일 필드 존재 및 기본값 확인
    const travelDateInput = page.locator('#travel_date');
    await expect(travelDateInput).toBeVisible();
    const minVal = await travelDateInput.getAttribute('min');
    expect(minVal).toBeTruthy();

    // 약관 전체 동의 체크박스 클릭
    const agreeAll = page.locator('#agreeAll');
    await expect(agreeAll).toBeVisible();
    await agreeAll.click();

    // 하위 필수 약관들이 모두 체크되었는지 검증
    const agreeSpecial = page.locator('#agreeSpecial');
    const agreePrivacy = page.locator('#agreePrivacy');
    await expect(agreeSpecial).toBeChecked();
    await expect(agreePrivacy).toBeChecked();
  });

  test('회원 로그인 상태 예약 - 연관 숙박(호텔/민박) 전용 필터 탭 동작 검증', async ({ page }) => {
    // 1. 회원 로그인 (hong / 12341234)
    await page.goto('/auth/login/');
    await page.fill('#user_id', 'hong');
    await page.fill('#password', '12341234');
    await page.click('button.login-button');
    await expect(page).toHaveURL('/');

    // 2. 예약 화면으로 이동
    await page.goto('/order/reserve?product_id=1');

    // 회원 특별 우대 배지 확인
    await expect(page.locator('.badge:has-text("회원 특별 우대")')).toBeVisible();

    // 6. 연관 숙박 예약(호텔 & 민박) 섹션 확인
    const accSection = page.locator('#accommodationSection');
    await expect(accSection).toBeVisible();

    // 호텔만 보기 탭 버튼 클릭
    const hotelTabBtn = page.locator('button.btn-acc-tab[data-category="호텔"]');
    if (await hotelTabBtn.isVisible()) {
      await hotelTabBtn.click();
      await expect(hotelTabBtn).toHaveClass(/active/);

      // 호텔 카드가 표시되는 경우 카테고리가 '호텔'인지 검증
      const visibleAccItems = page.locator('.acc-item:visible');
      const count = await visibleAccItems.count();
      for (let i = 0; i < count; i++) {
        const cat = await visibleAccItems.nth(i).getAttribute('data-category');
        expect(cat).toBe('호텔');
      }
    }

    // 민박만 보기 탭 버튼 클릭
    const minbakTabBtn = page.locator('button.btn-acc-tab[data-category="민박"]');
    if (await minbakTabBtn.isVisible()) {
      await minbakTabBtn.click();
      await expect(minbakTabBtn).toHaveClass(/active/);

      // 민박 카드가 표시되는 경우 카테고리가 '민박'인지 검증
      const visibleAccItems = page.locator('.acc-item:visible');
      const count = await visibleAccItems.count();
      for (let i = 0; i < count; i++) {
        const cat = await visibleAccItems.nth(i).getAttribute('data-category');
        expect(cat).toBe('민박');
      }
    }

    // 숙소 선택 안 함 라디오 버튼이 기본 선택되어 있는지 확인
    const noneRadio = page.locator('input[name="accommodation_id"][value=""]');
    await expect(noneRadio).toBeChecked();
  });

  test('예약 내역 조회(/order/lookup) 페이지 정상 접근 확인', async ({ page }) => {
    await page.goto('/order/lookup');
    await expect(page).toHaveURL(/\/order\/lookup/);
    await expect(page.locator('body')).toBeVisible();
  });
});

