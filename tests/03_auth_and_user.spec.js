// @ts-check
import { test, expect } from '@playwright/test';

test.describe('회원 가입, 로그인/로그아웃 인증 플로우 테스트', () => {
  test('회원가입 페이지 요소 렌더링 및 아이디 중복 확인 AJAX 동작 검증', async ({ page }) => {
    await page.goto('/auth/signup/');

    // 회원가입 폼 요소 확인
    await expect(page.locator('h2:has-text("회원가입")')).toBeVisible();
    await expect(page.locator('#user_id')).toBeVisible();
    await expect(page.locator('#name')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#phone')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#password_confirm')).toBeVisible();

    // 기존 회원 아이디('hong') 입력 후 중복 확인 버튼 클릭
    await page.fill('#user_id', 'hong');
    await page.click('#btnCheckId');

    // '이미 사용 중인 아이디입니다.' 메시지 출력 확인
    const checkMsg = page.locator('#idCheckMessage');
    await expect(checkMsg).toBeVisible();
    await expect(checkMsg).toContainText('이미 사용 중인 아이디');
  });

  test('로그인 실패 - 존재하지 않는 사용자 또는 비밀번호 불일치', async ({ page }) => {
    await page.goto('/auth/login/');

    await page.fill('#user_id', 'hong');
    await page.fill('#password', 'wrong_pass_123');
    await page.click('button.login-button');

    // 에러 메시지 확인
    const errorAlert = page.locator('.alert-danger, body');
    await expect(errorAlert).toContainText('아이디 또는 비밀번호가 올바르지 않습니다');
  });

  test('로그인 성공 및 로그아웃 전체 라이프사이클 검증', async ({ page }) => {
    await page.goto('/auth/login/');

    // 정상 테스트 계정(hong / 12341234) 로그인
    await page.fill('#user_id', 'hong');
    await page.fill('#password', '12341234');
    await page.click('button.login-button');

    // 로그인 후 메인 홈 복귀 및 사용자명(홍길동님) 표시 확인
    await expect(page).toHaveURL('/');
    const userGreeting = page.locator('.util-user-name');
    await expect(userGreeting).toBeVisible();
    await expect(userGreeting).toContainText('홍길동님');

    // 로그아웃 버튼 노출 및 클릭
    const logoutBtn = page.locator('.logout-btn');
    await expect(logoutBtn).toBeVisible();
    await logoutBtn.click();

    // 로그아웃 완료 후 '로그인' 버튼으로 전환 확인
    await expect(page.locator('a.util-link:has-text("로그인")')).toBeVisible();
  });
});

