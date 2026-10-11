// @ts-check
import { test, expect } from '@playwright/test';

test.describe('여행 상품 탐색, 권역 필터링 및 상세 페이지 테스트', () => {
  // 1. 전체 및 6대 모든 권역 탭 전환 동작 및 각 권역 상품 일치 여부 검증
  const tabCases = [
    { name: '수도권', tabId: '#pills-sudo-tab', paneId: '#pills-sudo', expectedRegionText: '서울/경기' },
    { name: '강원권', tabId: '#pills-gang-tab', paneId: '#pills-gang', expectedRegionText: '강원' },
    { name: '충청권', tabId: '#pills-chung-tab', paneId: '#pills-chung', expectedRegionText: '충청' },
    { name: '경상권', tabId: '#pills-gyeong-tab', paneId: '#pills-gyeong', expectedRegionText: '경상' },
    { name: '전라권', tabId: '#pills-jeon-tab', paneId: '#pills-jeon', expectedRegionText: '전라' },
    { name: '제주권', tabId: '#pills-jeju-tab', paneId: '#pills-jeju', expectedRegionText: '제주' },
    { name: '전체', tabId: '#pills-all-tab', paneId: '#pills-all', expectedRegionText: null },
  ];

  test('전체 및 6대 권역(수도권/강원/충청/경상/전라/제주) 탭 전환 및 해당 권역 상품 표시 검증', async ({ page }) => {
    await page.goto('/product/main_product');

    // 초기 상태: '전체' 탭 활성화 확인
    await expect(page.locator('#pills-all-tab')).toHaveClass(/active/);
    await expect(page.locator('#pills-all .product-grid .card').first()).toBeVisible();

    // 모든 권역 탭을 순차적으로 클릭하며 전환 및 권역 일치 검증
    for (const item of tabCases) {
      const tabBtn = page.locator(item.tabId);
      await tabBtn.click();

      // 1. 탭 버튼 활성화 클래스 확인
      await expect(tabBtn).toHaveClass(/active/);

      // 2. 해당 탭 패널 활성화 및 그리드 노출 확인
      const pane = page.locator(item.paneId);
      await expect(pane).toHaveClass(/active/);
      await expect(pane).toHaveClass(/show/);
      const grid = pane.locator('.product-grid');
      await expect(grid).toBeVisible();

      // 3. 특정 권역인 경우, 탭 내 노출된 모든 카드가 해당 권역 태그를 가지는지 확인
      if (item.expectedRegionText) {
        const cards = pane.locator('.product-grid .card');
        const count = await cards.count();
        expect(count).toBeGreaterThan(0);

        for (let i = 0; i < count; i++) {
          const regionBadge = cards.nth(i).locator('#on_img_box2');
          await expect(regionBadge).toHaveText(item.expectedRegionText);
        }
      }
    }
  });

  // 2. 키워드 검색 후 권역 선택 시 해당 권역 결과만 필터링되어 출력되는지 검증
  test('키워드 검색 후 권역 탭 선택 시 해당 권역의 결과만 출력되는지 검증', async ({ page }) => {
    await page.goto('/product/main_product');

    // 여러 권역에 걸쳐 존재하는 대표 키워드 '투어' 검색
    const searchInput = page.locator('input.header-search-input');
    await searchInput.fill('투어');
    await page.locator('button.header-search-btn').click();

    // 검색 결과 문구 노출 확인
    await expect(page.locator('#main_text')).toContainText('투어');
    await expect(page.locator('#main_text')).toContainText('검색 결과');

    // 전체 탭에 검색된 상품들이 노출되는지 확인
    const allCards = page.locator('#pills-all .product-grid .card');
    const allCount = await allCards.count();
    expect(allCount).toBeGreaterThan(0);

    // [강원권 탭 선택] -> 강원권의 '투어' 상품만 노출되는지 검증
    await page.locator('#pills-gang-tab').click();
    await expect(page.locator('#pills-gang-tab')).toHaveClass(/active/);
    const gangCards = page.locator('#pills-gang .product-grid .card');
    const gangCount = await gangCards.count();
    expect(gangCount).toBeGreaterThan(0);

    for (let i = 0; i < gangCount; i++) {
      const card = gangCards.nth(i);
      // 권역 배지가 '강원'인지 확인
      await expect(card.locator('#on_img_box2')).toHaveText('강원');
      // 제목에 검색어 '투어'가 포함되어 있는지 확인
      const title = await card.locator('.card-title').textContent();
      expect(title).toContain('투어');
    }

    // [경상권 탭 선택] -> 경상권의 '투어' 상품만 노출되는지 검증
    await page.locator('#pills-gyeong-tab').click();
    await expect(page.locator('#pills-gyeong-tab')).toHaveClass(/active/);
    const gyeongCards = page.locator('#pills-gyeong .product-grid .card');
    const gyeongCount = await gyeongCards.count();
    expect(gyeongCount).toBeGreaterThan(0);

    for (let i = 0; i < gyeongCount; i++) {
      const card = gyeongCards.nth(i);
      await expect(card.locator('#on_img_box2')).toHaveText('경상');
      const title = await card.locator('.card-title').textContent();
      expect(title).toContain('투어');
    }

    // [제주권 탭 선택] -> 제주권의 '투어' 상품만 노출되는지 검증
    await page.locator('#pills-jeju-tab').click();
    await expect(page.locator('#pills-jeju-tab')).toHaveClass(/active/);
    const jejuCards = page.locator('#pills-jeju .product-grid .card');
    const jejuCount = await jejuCards.count();
    expect(jejuCount).toBeGreaterThan(0);

    for (let i = 0; i < jejuCount; i++) {
      const card = jejuCards.nth(i);
      await expect(card.locator('#on_img_box2')).toHaveText('제주');
      const title = await card.locator('.card-title').textContent();
      expect(title).toContain('투어');
    }
  });

  test('키워드 검색 후 해당 권역에 결과가 없을 경우 검색 결과 없음 메시지 노출 확인', async ({ page }) => {
    await page.goto('/product/main_product');

    // '온천' 검색 (강원, 경상에만 존재하고 제주에는 없음)
    const searchInput = page.locator('input.header-search-input');
    await searchInput.fill('온천');
    await page.locator('button.header-search-btn').click();

    // 강원권 탭 선택 시 강원권 온천 상품 정상 노출 확인
    await page.locator('#pills-gang-tab').click();
    const gangCards = page.locator('#pills-gang .product-grid .card');
    expect(await gangCards.count()).toBeGreaterThan(0);
    await expect(gangCards.first().locator('#on_img_box2')).toHaveText('강원');

    // 경상권 탭 선택 시 경상권 온천 상품 정상 노출 확인
    await page.locator('#pills-gyeong-tab').click();
    const gyeongCards = page.locator('#pills-gyeong .product-grid .card');
    expect(await gyeongCards.count()).toBeGreaterThan(0);
    await expect(gyeongCards.first().locator('#on_img_box2')).toHaveText('경상');

    // 제주권 탭 선택 시 온천 상품이 없으므로 '검색 결과가 없습니다' 노출 확인
    await page.locator('#pills-jeju-tab').click();
    const jejuPane = page.locator('#pills-jeju');
    await expect(jejuPane).toContainText('검색 결과가 없습니다');
  });

  test('검색 결과 없는 임의 키워드 처리 및 안내 문구 노출', async ({ page }) => {
    await page.goto('/product/main_product');

    // 결과가 없을 만한 임의의 키워드 입력
    const searchInput = page.locator('input.header-search-input');
    await searchInput.fill('존재하지않는여행지12345');
    await page.locator('button.header-search-btn').click();

    // '검색 결과가 없습니다' 안내 표시 확인
    const noResultMsg = page.locator('.tab-pane.active');
    await expect(noResultMsg).toContainText('검색 결과가 없습니다');
    await expect(page.locator('a:has-text("전체 여행 상품 보기")').first()).toBeVisible();
  });

  test('상품 상세 페이지 진입 및 상세 정보/일정/구매 버튼 확인', async ({ page }) => {
    await page.goto('/product/main_product');

    // 첫 번째 카드의 '상세보기' 클릭
    const detailLink = page.locator('.tab-pane.active .product-grid .card a.btn-primary:has-text("상세보기")').first();
    await detailLink.click();

    // 상세 페이지로 이동 확인
    await expect(page).toHaveURL(/\/product\/sub_product\/\d+/);

    // 상품명 및 가격 영역 노출 확인
    await expect(page.locator('.tour-hero, h1, h2, .product-title').first()).toBeVisible();

    // '바로 구매하기' 버튼 클릭 시 예약 페이지로 이동 확인
    const purchaseBtn = page.locator('#people button:has-text("구매하기")');
    await expect(purchaseBtn).toBeVisible();
    await purchaseBtn.click();

    await expect(page).toHaveURL(/\/order\/reserve\?product_id=\d+/);
  });
});
