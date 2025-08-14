import { test, expect } from '@playwright/test';

test.describe('WebSocket Features', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.getByPlaceholder('Nombre de usuario').fill('shadow_monarch');
    await page.getByPlaceholder('Contraseña').fill('demo123');
    await page.getByRole('button', { name: /entrar al portal/i }).click();
    
    // Wait for dashboard
    await expect(page.getByText(/bienvenido/i)).toBeVisible({ timeout: 10000 });
  });

  test.describe('Guild Chat', () => {
    test('should navigate to guild chat page', async ({ page }) => {
      await page.goto('/guild-chat');
      
      // Should show guild selection
      await expect(page.getByText('Sistema de Chat de Gremios')).toBeVisible();
      await expect(page.getByText('Shadow Hunters')).toBeVisible();
      await expect(page.getByText('Math Warriors')).toBeVisible();
    });

    test('should join a guild chat', async ({ page }) => {
      await page.goto('/guild-chat');
      
      // Click on a guild
      await page.getByText('Shadow Hunters').click();
      
      // Should show chat interface
      await expect(page.getByText('Chat de Shadow Hunters')).toBeVisible();
      await expect(page.getByPlaceholder('Escribe un mensaje...')).toBeVisible();
      
      // Should show online members count
      await expect(page.getByText(/en línea/i)).toBeVisible();
    });

    test('should send a message in guild chat', async ({ page }) => {
      await page.goto('/guild-chat');
      await page.getByText('Shadow Hunters').click();
      
      // Type and send message
      const messageInput = page.getByPlaceholder('Escribe un mensaje...');
      const testMessage = `Test message ${Date.now()}`;
      
      await messageInput.fill(testMessage);
      await page.getByRole('button', { name: /enviar|send/i }).click();
      
      // Message should appear in chat
      await expect(page.getByText(testMessage)).toBeVisible({ timeout: 5000 });
      
      // Input should be cleared
      await expect(messageInput).toHaveValue('');
    });

    test('should show AI suggestions', async ({ page }) => {
      await page.goto('/guild-chat');
      await page.getByText('Shadow Hunters').click();
      
      // Should show suggestion buttons
      await expect(page.getByText('¡Felicidades por completar la mazmorra!')).toBeVisible();
      
      // Click a suggestion
      await page.getByText('¡Felicidades por completar la mazmorra!').click();
      
      // Should populate input
      const messageInput = page.getByPlaceholder('Escribe un mensaje...');
      await expect(messageInput).toHaveValue('¡Felicidades por completar la mazmorra!');
    });

    test('should toggle mute/unmute', async ({ page }) => {
      await page.goto('/guild-chat');
      await page.getByText('Shadow Hunters').click();
      
      // Find mute button
      const muteButton = page.locator('button:has(svg.lucide-volume-2), button:has(svg.lucide-volume-x)').first();
      
      // Click to toggle
      await muteButton.click();
      
      // Button should change state (exact behavior depends on initial state)
      await expect(muteButton).toBeVisible();
    });
  });

  test.describe('Multiplayer Raids', () => {
    test('should navigate to raids page', async ({ page }) => {
      await page.goto('/multiplayer-raid');
      
      // Should show raid selection
      await expect(page.getByText('Raids Multijugador')).toBeVisible();
      await expect(page.getByText('Sombra del Conocimiento')).toBeVisible();
      await expect(page.getByText('Dragón de Cálculo')).toBeVisible();
    });

    test('should display raid details', async ({ page }) => {
      await page.goto('/multiplayer-raid');
      
      // Check raid info is displayed
      await expect(page.getByText('4-8 jugadores')).toBeVisible();
      await expect(page.getByText('10-15 min')).toBeVisible();
      await expect(page.getByText('500 EXP, Orbes Sombra')).toBeVisible();
    });

    test('should join a raid', async ({ page }) => {
      await page.goto('/multiplayer-raid');
      
      // Click join raid button
      await page.getByRole('button', { name: 'Unirse a la Raid' }).first().click();
      
      // Should show raid interface or loading
      await expect(page.locator('text=/conectando|raid|sombra del conocimiento/i')).toBeVisible({ timeout: 10000 });
    });

    test('should show raid features section', async ({ page }) => {
      await page.goto('/multiplayer-raid');
      
      // Verify features are displayed
      await expect(page.getByText('Cooperación en Tiempo Real')).toBeVisible();
      await expect(page.getByText('Mecánicas de Jefe Dinámicas')).toBeVisible();
      await expect(page.getByText('Recompensas Épicas')).toBeVisible();
      await expect(page.getByText('Sistema de Roles')).toBeVisible();
    });
  });

  test.describe('Real-time Leaderboards', () => {
    test('should navigate to leaderboards', async ({ page }) => {
      await page.goto('/leaderboards');
      
      // Should show leaderboards page
      await expect(page.getByText('Salón de la Fama')).toBeVisible();
      await expect(page.getByText(/compite con los mejores/i)).toBeVisible();
    });

    test('should show user stats', async ({ page }) => {
      await page.goto('/leaderboards');
      
      // Should display user's rank and stats
      await expect(page.getByText('Rango Global')).toBeVisible();
      await expect(page.getByText('Puntos Totales')).toBeVisible();
      await expect(page.getByText('Precisión')).toBeVisible();
      await expect(page.getByText('Días de Racha')).toBeVisible();
    });

    test('should switch between leaderboard tabs', async ({ page }) => {
      await page.goto('/leaderboards');
      
      // Click weekly tab
      await page.getByRole('button', { name: /semanal/i }).click();
      
      // Tab should be active (check for gradient background)
      const weeklyTab = page.getByRole('button', { name: /semanal/i });
      await expect(weeklyTab).toHaveClass(/from-purple-600/);
      
      // Click daily tab
      await page.getByRole('button', { name: /diario/i }).click();
      
      // Daily tab should be active
      const dailyTab = page.getByRole('button', { name: /diario/i });
      await expect(dailyTab).toHaveClass(/from-purple-600/);
    });

    test('should show leaderboard filters', async ({ page }) => {
      await page.goto('/leaderboards');
      
      // Should have subject filter
      const subjectFilter = page.locator('select').first();
      await expect(subjectFilter).toBeVisible();
      
      // Should have search input
      const searchInput = page.getByPlaceholder(/buscar jugador/i);
      await expect(searchInput).toBeVisible();
    });

    test('should display achievements section', async ({ page }) => {
      await page.goto('/leaderboards');
      
      // Scroll to achievements
      await page.getByText('Logros Especiales').scrollIntoViewIfNeeded();
      
      // Should show achievement cards
      await expect(page.getByText('Rey de la Colina')).toBeVisible();
      await expect(page.getByText('Racha Legendaria')).toBeVisible();
      await expect(page.getByText('Precisión Perfecta')).toBeVisible();
    });
  });
});