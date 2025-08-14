import { test, expect } from '@playwright/test';

test.describe('Game Modes', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.getByPlaceholder('Nombre de usuario').fill('shadow_monarch');
    await page.getByPlaceholder('Contraseña').fill('demo123');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText(/bienvenido/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display mode toggle on dashboard', async ({ page }) => {
    // Check for mode toggle
    await expect(page.getByText('Modo Casual')).toBeVisible();
    await expect(page.getByText('Modo Progresión')).toBeVisible();
    
    // Default should be progression mode
    const progressionButton = page.getByRole('button', { name: /modo progresión/i });
    await expect(progressionButton).toHaveClass(/bg-purple-600/);
  });

  test('should switch between game modes', async ({ page }) => {
    // Switch to casual mode
    await page.getByRole('button', { name: /modo casual/i }).click();
    
    // Casual button should be active
    const casualButton = page.getByRole('button', { name: /modo casual/i });
    await expect(casualButton).toHaveClass(/bg-blue-600/);
    
    // Mode description should update
    await expect(page.getByText(/practica libremente sin restricciones/i)).toBeVisible();
    
    // Switch back to progression
    await page.getByRole('button', { name: /modo progresión/i }).click();
    
    // Progression button should be active
    const progressionButton = page.getByRole('button', { name: /modo progresión/i });
    await expect(progressionButton).toHaveClass(/bg-purple-600/);
  });

  test('should show mode info modal', async ({ page }) => {
    // Click info button (using more specific selector)
    const infoButton = page.locator('button:has(svg.lucide-info)').first();
    await infoButton.click();
    
    // Modal should appear
    await expect(page.getByText('Modos de Juego')).toBeVisible();
    await expect(page.getByText('Exploración Libre')).toBeVisible();
    await expect(page.getByText('Aprendizaje Estructurado')).toBeVisible();
    
    // Check mode features are displayed
    await expect(page.getByText('Acceso libre a todo el contenido')).toBeVisible();
    await expect(page.getByText('Contenido desbloqueado por logros')).toBeVisible();
    
    // Close modal
    await page.getByRole('button', { name: 'Cerrar' }).click();
    await expect(page.getByText('Modos de Juego')).not.toBeVisible();
  });

  test('should persist mode selection', async ({ page }) => {
    // Switch to casual mode
    await page.getByRole('button', { name: /modo casual/i }).click();
    
    // Reload page
    await page.reload();
    
    // Wait for dashboard to load
    await expect(page.getByText(/shadow monarch/i)).toBeVisible({ timeout: 10000 });
    
    // Casual mode should still be selected
    const casualButton = page.getByRole('button', { name: /modo casual/i });
    await expect(casualButton).toHaveClass(/bg-blue-600/);
  });

  test('should activate corresponding mode from info modal', async ({ page }) => {
    // Open info modal
    const infoButton = page.locator('button:has(svg.lucide-info)').first();
    await infoButton.click();
    
    // Click activate casual mode from modal
    await page.getByRole('button', { name: 'Activar Modo Casual' }).click();
    
    // Modal should close and casual mode should be active
    await expect(page.getByText('Modos de Juego')).not.toBeVisible();
    const casualButton = page.getByRole('button', { name: /modo casual/i });
    await expect(casualButton).toHaveClass(/bg-blue-600/);
  });
});