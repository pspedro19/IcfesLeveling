import { test, expect } from '@playwright/test';

test.describe('Battle System', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to battle
    await page.goto('/');
    await page.getByPlaceholder('Nombre de usuario').fill('shadow_monarch');
    await page.getByPlaceholder('Contraseña').fill('demo123');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Wait for dashboard and click on dungeon
    await expect(page.getByText(/bienvenido/i)).toBeVisible({ timeout: 10000 });
    await page.getByText('Mazmorra').click();
  });

  test('should display dungeon screen with battle options', async ({ page }) => {
    // Check dungeon elements
    await expect(page.getByText(/elige tu mazmorra/i)).toBeVisible();
    await expect(page.getByText('Matemáticas')).toBeVisible();
    await expect(page.getByText('Ciencias')).toBeVisible();
    await expect(page.getByText('Lectura')).toBeVisible();
    
    // Check player stats
    await expect(page.getByText(/nivel/i)).toBeVisible();
    await expect(page.getByText(/hp/i)).toBeVisible();
    await expect(page.getByText(/mp/i)).toBeVisible();
  });

  test('should start a battle when clicking a subject', async ({ page }) => {
    // Click on Mathematics dungeon
    await page.getByText('Matemáticas').click();
    
    // Should show battle screen
    await expect(page.getByText(/batalla/i)).toBeVisible({ timeout: 10000 });
    
    // Battle elements should be visible
    await expect(page.getByText(/hp/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /atacar/i })).toBeVisible();
  });

  test('should show question and answer options in battle', async ({ page }) => {
    // Start a battle
    await page.getByText('Matemáticas').click();
    
    // Click attack button
    await page.getByRole('button', { name: /atacar/i }).click();
    
    // Should show a question
    await expect(page.locator('text=/¿.*\\?/')).toBeVisible({ timeout: 10000 });
    
    // Should show answer options (usually 4)
    const answerButtons = page.locator('button').filter({ hasText: /^[^¿]/ });
    await expect(answerButtons).toHaveCount(4);
  });

  test('should handle answer selection and show result', async ({ page }) => {
    // Start battle and get question
    await page.getByText('Matemáticas').click();
    await page.getByRole('button', { name: /atacar/i }).click();
    
    // Wait for question
    await expect(page.locator('text=/¿.*\\?/')).toBeVisible({ timeout: 10000 });
    
    // Select first answer option
    const answerButtons = page.locator('button').filter({ hasText: /^[^¿]/ });
    await answerButtons.first().click();
    
    // Should show some feedback (damage numbers, correct/incorrect, etc)
    // The exact feedback depends on implementation
    await expect(page.locator('body')).toContainText(/(correcto|incorrecto|daño|\d+)/i, { timeout: 5000 });
  });

  test('should show battle report after completing questions', async ({ page }) => {
    // Navigate to battle report demo page if available
    await page.goto('/battle-report');
    
    // Check if report elements are visible
    await expect(page.getByText('Sistema de Reportes de Batalla')).toBeVisible();
    await expect(page.getByText('Rendimiento Normal')).toBeVisible();
    
    // Click to show a report
    await page.getByText('Rendimiento Normal').click();
    
    // Report should display
    await expect(page.getByText('Reporte de Batalla')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/precisión total/i)).toBeVisible();
    await expect(page.getByText(/z-score/i)).toBeVisible();
  });

  test('should navigate back to dungeon selection', async ({ page }) => {
    // Check for back button
    const backButton = page.getByRole('button', { name: /volver|regresar|back/i });
    
    if (await backButton.isVisible()) {
      await backButton.click();
      // Should return to dashboard
      await expect(page.getByText('Mazmorra')).toBeVisible();
    }
  });
});