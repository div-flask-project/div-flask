// @ts-check
import { test, expect } from '@playwright/test';

test.describe('공지사항 및 고객센터 안내 테스트', () => {
  test('공지사항 목록 렌더링 및 카테고리 필터링 확인', async ({ page }) => {
    await page.goto('/notice/');

    // 공지사항 페이지 헤더 확인
    await expect(page.locator('h3:has-text("공지사항")')).toBeVisible();

    // 카테고리 필터 버튼들 확인
    const allCategoryBtn = page.locator('.notice-category-btn:has-text("전체")');
    await expect(allCategoryBtn).toBeVisible();
    await expect(allCategoryBtn).toHaveClass(/active/);

    // '시스템' 카테고리 클릭
    const systemCategoryBtn = page.locator('.notice-category-btn:has-text("시스템")');
    await expect(systemCategoryBtn).toBeVisible();
    await systemCategoryBtn.click();

    await expect(page).toHaveURL(/category=%EC%8B%9C%EC%8A%A4%ED%85%9C|category=시스템/);
    await expect(page.locator('.notice-category-btn:has-text("시스템")')).toHaveClass(/active/);
  });

  test('공지사항 키워드 검색 기능 확인', async ({ page }) => {
    await page.goto('/notice/');

    // 검색창에 키워드 입력 후 검색
    const searchInput = page.locator('.notice-search-wrap input[name="kw"]');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('안내');
    await page.locator('.notice-search-wrap button[type="submit"]').click();

    // 검색 URL 확인
    await expect(page).toHaveURL(/kw=/);
    await expect(page.locator('.notice-wrapper')).toBeVisible();
  });

  test('고객센터(FAQ) 비로그인 접근 시 로그인 리다이렉트 확인', async ({ page }) => {
    // 비로그인 상태로 /customer/faq 접속
    await page.goto('/customer/faq');

    // 로그인 페이지로 리다이렉트되는지 확인 (next 파라미터 포함)
    await expect(page).toHaveURL(/\/auth\/login/);
    const flashAlert = page.locator('.alert-danger, body');
    await expect(flashAlert).toContainText('로그인이 필요한 서비스입니다');
  });
});

