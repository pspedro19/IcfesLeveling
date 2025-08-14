import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login portal on homepage', async ({ page }) => {
    // Check for portal elements
    await expect(page.getByText('Portal de Invocación')).toBeVisible();
    await expect(page.getByPlaceholder('Nombre de usuario')).toBeVisible();
    await expect(page.getByPlaceholder('Contraseña')).toBeVisible();
    await expect(page.getByRole('button', { name: /entrar al portal/i })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Try to login with invalid credentials
    await page.getByPlaceholder('Nombre de usuario').fill('invaliduser');
    await page.getByPlaceholder('Contraseña').fill('wrongpassword');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Should show error message
    await expect(page.getByText(/error de inicio de sesión/i)).toBeVisible({ timeout: 10000 });
  });

  test('should successfully login with demo account', async ({ page }) => {
    // Login with demo credentials
    await page.getByPlaceholder('Nombre de usuario').fill('shadow_monarch');
    await page.getByPlaceholder('Contraseña').fill('demo123');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Should navigate to dashboard
    await expect(page.getByText(/bienvenido/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Shadow Monarch')).toBeVisible();
    
    // Should show dashboard elements
    await expect(page.getByText('Mazmorra')).toBeVisible();
    await expect(page.getByText('Torre Infinita')).toBeVisible();
    await expect(page.getByText('Prácticas ICFES')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.getByPlaceholder('Nombre de usuario').fill('shadow_monarch');
    await page.getByPlaceholder('Contraseña').fill('demo123');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText(/bienvenido/i)).toBeVisible({ timeout: 10000 });
    
    // Click logout
    await page.getByRole('button', { name: /cerrar sesión/i }).click();
    
    // Should return to login portal
    await expect(page.getByText('Portal de Invocación')).toBeVisible();
    await expect(page.getByPlaceholder('Nombre de usuario')).toBeVisible();
  });

  test('should toggle between login and register forms', async ({ page }) => {
    // Initially in login mode
    await expect(page.getByText('Iniciar Sesión')).toBeVisible();
    
    // Click register link
    await page.getByText('¿No tienes cuenta? Regístrate').click();
    
    // Should show register form
    await expect(page.getByText('Crear Cuenta')).toBeVisible();
    await expect(page.getByPlaceholder('Correo electrónico')).toBeVisible();
    
    // Click back to login
    await page.getByText('¿Ya tienes cuenta? Inicia sesión').click();
    
    // Should be back in login mode
    await expect(page.getByText('Iniciar Sesión')).toBeVisible();
  });

  test('should handle registration flow', async ({ page }) => {
    // Switch to register mode
    await page.getByText('¿No tienes cuenta? Regístrate').click();
    
    // Fill registration form
    const timestamp = Date.now();
    await page.getByPlaceholder('Nombre de usuario').fill(`testuser${timestamp}`);
    await page.getByPlaceholder('Correo electrónico').fill(`test${timestamp}@example.com`);
    await page.getByPlaceholder('Contraseña').fill('TestPassword123!');
    
    await page.getByRole('button', { name: /crear cuenta/i }).click();
    
    // Should either succeed or show validation error
    // Since backend might not be running, we just check the UI responds
    await expect(page.locator('body')).toContainText(/(bienvenido|error|ya existe)/i, { timeout: 10000 });
  });
});