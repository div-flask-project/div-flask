// @ts-check
import { test, expect } from '@playwright/test';

test.describe('여행 후기(Review) 권한 및 라이프사이클 테스트', () => {

  test('1. 비로그인 상태에서 메인 화면에 여행 후기 내용이 보이지 않는지 확인 (오버레이 및 블러)', async ({ page }) => {
    await page.goto('/');

    // 메인 홈의 여행 후기 섹션 존재 확인
    const reviewSection = page.locator('.travel-reviews');
    await expect(reviewSection).toBeVisible();

    // 1-1. 비로그인 시 상단에 덮이는 로그인 안내 오버레이 박스 확인
    const overlayBox = reviewSection.locator('.review-login-overlay');
    await expect(overlayBox).toBeVisible();
    await expect(overlayBox).toContainText('로그인이 필요한 서비스입니다');

    // 1-2. 실제 후기 내용 영역에 블러(blur) 클래스가 적용되어 가려져 있는지 확인
    const blurredContent = reviewSection.locator('.review-blurred-content');
    await expect(blurredContent).toBeVisible();
  });

  test('2. 비로그인 상태에서 후기 메뉴 선택 시 로그인 화면으로 이동하는지 확인', async ({ page }) => {
    await page.goto('/');

    // 상단 네비게이션의 '후기' 링크 클릭
    const navReviewLink = page.locator('.main-nav a[href*="/review/list"], .nav-links a:has-text("후기")').first();
    await expect(navReviewLink).toBeVisible();
    await navReviewLink.click();

    // 로그인 화면(/auth/login)으로 리다이렉트 확인
    await expect(page).toHaveURL(/\/auth\/login/);

    // 로그인이 필요한 서비스 안내 플래시 메시지 및 로그인 폼 노출 확인
    const alertMessage = page.locator('.alert-danger, .flash-message, body');
    await expect(alertMessage).toContainText('로그인이 필요한 서비스입니다');
    await expect(page.locator('#user_id')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
  });

  test.describe.serial('로그인 사용자의 여행확인(예약조회) 화면 후기 등록/수정/삭제 라이프사이클', () => {

    test('3. 여행확인 화면에서 로그인된 사용자의 후기 등록 가능 여부 확인', async ({ page }) => {
      // 3-1. 회원 로그인 (hong / 12341234 - 가평 투어 예약 내역 보유)
      await page.goto('/auth/login/');
      await page.fill('#user_id', 'hong');
      await page.fill('#password', '12341234');
      await page.click('button.login-button');
      await expect(page).toHaveURL('/');

      // 3-2. 여행확인(예약 확인 및 조회) 페이지 이동
      await page.goto('/order/lookup');
      await expect(page).toHaveURL(/\/order\/lookup/);
      await expect(page.locator('.member-lookup-container')).toBeVisible();

      // 혹시 이전 실행으로 등록된 리뷰가 있다면 삭제하여 'Review 작성' 상태로 초기화
      const deleteBtn = page.locator('a:has-text("Review 삭제")').first();
      if (await deleteBtn.isVisible()) {
        page.once('dialog', dialog => dialog.accept());
        await deleteBtn.click();
        await page.waitForLoadState('load');
      }

      // 3-3. '✍️ Review 작성' 버튼 노출 확인 및 클릭
      const createBtn = page.locator('a:has-text("Review 작성")').first();
      await expect(createBtn).toBeVisible();
      await createBtn.click();

      // 3-4. 후기 작성 페이지 이동 및 폼 입력
      await expect(page).toHaveURL(/\/review\/create/);
      await expect(page.locator('h3:has-text("여행자 후기 작성")')).toBeVisible();

      await page.fill('#title', '가평 아침고요수목원 힐링 투어 만족 후기');
      await page.fill('#content', '수목원 산책로와 자연 풍경이 정말 훌륭했습니다. 재방문 의사 있습니다!');
      await page.selectOption('#rating', '5');
      await page.click('button[type="submit"]:has-text("후기 등록하기")');

      // 3-5. 등록 성공 메시지 및 후기 상세 화면 이동 확인
      await expect(page).toHaveURL(/\/review\/detail/);
      await expect(page.locator('body')).toContainText('성공적으로 등록되었습니다');
    });

    test('4. 여행확인 화면에서 이미 후기가 등록되어 있는 경우 후기 수정 가능 여부 확인', async ({ page }) => {
      // 4-1. 로그인 상태로 여행확인(/order/lookup) 화면 이동
      await page.goto('/auth/login/');
      await page.fill('#user_id', 'hong');
      await page.fill('#password', '12341234');
      await page.click('button.login-button');

      await page.goto('/order/lookup');
      await expect(page).toHaveURL(/\/order\/lookup/);

      // 4-2. 이미 후기가 등록되어 있으므로 'Review 수정' 및 'Review 삭제' 버튼이 노출되는지 확인
      const modifyBtn = page.locator('a:has-text("Review 수정")').first();
      await expect(modifyBtn).toBeVisible();
      await expect(page.locator('a:has-text("Review 삭제")').first()).toBeVisible();

      // 4-3. '✏️ Review 수정' 버튼 클릭
      await modifyBtn.click();
      await expect(page).toHaveURL(/\/review\/modify|\/review\/edit/);
      await expect(page.locator('h3:has-text("여행자 후기 수정")')).toBeVisible();

      // 4-4. 내용 수정 및 폼 제출
      await page.fill('#content', '수목원 산책로와 자연 풍경이 정말 훌륭했습니다. 코스가 알차서 가족 여행으로 최고였습니다. (수정 완료)');
      await page.click('button[type="submit"]:has-text("수정 완료하기")');

      // 4-5. 수정 완료 메시지 및 반영 확인
      await expect(page).toHaveURL(/\/review\/detail/);
      await expect(page.locator('body')).toContainText('성공적으로 수정되었습니다');
    });

    test('5. 여행확인 화면에서 이미 후기가 등록되어 있는 경우 후기 삭제 가능 여부 확인', async ({ page }) => {
      // 5-1. 로그인 상태로 여행확인(/order/lookup) 화면 이동
      await page.goto('/auth/login/');
      await page.fill('#user_id', 'hong');
      await page.fill('#password', '12341234');
      await page.click('button.login-button');

      await page.goto('/order/lookup');
      await expect(page).toHaveURL(/\/order\/lookup/);

      // 5-2. 'Review 삭제' 버튼 확인
      const deleteBtn = page.locator('a:has-text("Review 삭제")').first();
      await expect(deleteBtn).toBeVisible();

      // 브라우저 confirm 다이얼로그 자동 수락 설정
      page.once('dialog', async dialog => {
        expect(dialog.message()).toContain('삭제');
        await dialog.accept();
      });

      // 5-3. 삭제 버튼 클릭
      await deleteBtn.click();

      // 5-4. 여행확인 페이지로 리다이렉트 및 삭제 완료 메시지 확인
      await expect(page).toHaveURL(/\/order\/lookup/);
      await expect(page.locator('body')).toContainText('성공적으로 삭제되었습니다');

      // 5-5. 후기가 삭제되었으므로 다시 'Review 작성' 버튼으로 전환되었는지 검증
      await expect(page.locator('a:has-text("Review 작성")').first()).toBeVisible();
    });
  });
});

