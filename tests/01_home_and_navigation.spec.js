// @ts-check
import { test, expect } from '@playwright/test';

test.describe('메인 홈 및 헤더 네비게이션 테스트', () => {
  test('홈페이지 메인 타이틀, 로고, 슬로건 확인', async ({ page }) => {
    await page.goto('/');

    // 타이틀 확인
    await expect(page).toHaveTitle(/길마중/);

    // 로고 링크 및 슬로건
    const logoLink = page.locator('.logo-area a.logo-link');
    await expect(logoLink).toBeVisible();
    await expect(logoLink).toContainText('길마중');

    const slogan = page.locator('.logo-area .slogan');
    await expect(slogan).toBeVisible();
    await expect(slogan).toContainText('오늘, 더 특별한 여행');
  });

  test('상단 유틸리티 메뉴 (로그인, 예약확인, 고객센터) 링크 확인', async ({ page }) => {
    await page.goto('/');

    // 로그인 링크
    const loginLink = page.locator('.top-util-menu a[href*="/auth/login"]');
    await expect(loginLink).toBeVisible();

    // 예약확인 링크
    const lookupLink = page.locator('.top-util-menu a[href*="/order/lookup"]');
    await expect(lookupLink).toBeVisible();

    // 고객센터 링크
    const csLink = page.locator('.top-util-menu a[href*="/customer/faq"]');
    await expect(csLink).toBeVisible();
  });

  test('다국어 선택 드롭다운 토글 및 언어 목록 표시 확인', async ({ page }) => {
    await page.goto('/');

    const langBtn = page.locator('#languageDropdown');
    await expect(langBtn).toBeVisible();
    await expect(langBtn).toContainText('한국어');

    // 드롭다운 클릭 시 메뉴 목록 노출
    await langBtn.click();
    const langMenu = page.locator('#customLangMenu');
    await expect(langMenu).toBeVisible();

    // 다국어 옵션 4종 확인
    await expect(langMenu.locator('a:has-text("한국어")')).toBeVisible();
    await expect(langMenu.locator('a:has-text("English")')).toBeVisible();
    await expect(langMenu.locator('a:has-text("日本語")')).toBeVisible();
    await expect(langMenu.locator('a:has-text("简体中文")')).toBeVisible();
  });

  // 6대 권역 (수도권, 강원권, 충청권, 경상권, 전라권, 제주권) 퀵 버튼 이동 테스트
  const regions = [
    { name: '수도권', urlPattern: /region=sudo/, tabId: '#pills-sudo-tab', paneId: '#pills-sudo' },
    { name: '강원권', urlPattern: /region=gang/, tabId: '#pills-gang-tab', paneId: '#pills-gang' },
    { name: '충청권', urlPattern: /region=chung/, tabId: '#pills-chung-tab', paneId: '#pills-chung' },
    { name: '경상권', urlPattern: /region=geong|region=gyeong/, tabId: '#pills-gyeong-tab', paneId: '#pills-gyeong' },
    { name: '전라권', urlPattern: /region=jeon/, tabId: '#pills-jeon-tab', paneId: '#pills-jeon' },
    { name: '제주권', urlPattern: /region=jeju/, tabId: '#pills-jeju-tab', paneId: '#pills-jeju' },
  ];

  for (const reg of regions) {
    test(`메인 홈 6대 권역 퀵 버튼 클릭 시 해당 권역으로 이동 (${reg.name})`, async ({ page }) => {
      await page.goto('/');

      // 6대 권역 퀵 버튼 영역에서 해당 권역 클릭
      const regBtn = page.locator(`.icon-item:has-text("${reg.name}")`);
      await expect(regBtn).toBeVisible();
      await regBtn.click();

      // 해당 권역 파라미터가 포함된 상품 목록 페이지로 이동 확인
      await expect(page).toHaveURL(reg.urlPattern);

      // 해당 권역 탭 버튼 활성화(active) 확인
      const activeTab = page.locator(reg.tabId);
      await expect(activeTab).toHaveClass(/active/);

      // 해당 권역 상품 그리드 노출 확인
      const activeGrid = page.locator(`${reg.paneId} .product-grid`);
      await expect(activeGrid).toBeVisible();
    });
  }
});
