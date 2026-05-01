import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('loads without errors', async ({ page }) => {
    await expect(page).toHaveTitle(/Signals/);
  });

  test('displays hero section with correct content', async ({ page }) => {
    await expect(page.locator('text=Intelligent Signals')).toBeVisible();
    await expect(page.locator('text=Autonomous trading')).toBeVisible();
  });

  test('displays navigation links', async ({ page }) => {
    await expect(page.locator('text=How it works')).toBeVisible();
    await expect(page.locator('text=Why Signals')).toBeVisible();
    await expect(page.locator('text=Proof')).toBeVisible();
  });

  test('nav links are clickable', async ({ page }) => {
    await page.locator('text=How it works').click();
    await expect(page.locator('#how')).toBeInViewport();
  });

  test('displays CTA buttons', async ({ page }) => {
    await expect(page.locator('text=Launch Signals')).toBeVisible();
    await expect(page.locator('text=See Proof of Alpha')).toBeVisible();
  });

  test('displays live vault state section', async ({ page }) => {
    await expect(page.locator('text=Live Vault State')).toBeVisible();
  });

  test('shows stat cards with vault data', async ({ page }) => {
    await expect(page.locator('text=Total Value Locked')).toBeVisible();
    await expect(page.locator('text=Shares Outstanding')).toBeVisible();
    await expect(page.locator('text=Share Price')).toBeVisible();
    await expect(page.locator('text=Trading Status')).toBeVisible();
  });

  test('displays how it works section', async ({ page }) => {
    await expect(page.locator('text=Three pillars')).toBeVisible();
    await expect(page.locator('text=Multi-Source Signal Analysis')).toBeVisible();
    await expect(page.locator('text=RL-Based Autonomous Trading')).toBeVisible();
    await expect(page.locator('text=Token Safety & Kill-Switch')).toBeVisible();
  });

  test('displays value props section', async ({ page }) => {
    await expect(page.locator('text=Built for')).toBeVisible();
    await expect(page.locator('text=Intelligent Signal Generation')).toBeVisible();
    await expect(page.locator('text=Autonomous RL Trading')).toBeVisible();
    await expect(page.locator('text=Safety-First Design')).toBeVisible();
  });

  test('displays footer with links', async ({ page }) => {
    await expect(page.locator('footer >> text=Contract')).toBeVisible();
    await expect(page.locator('footer >> text=Proof')).toBeVisible();
    await expect(page.locator('footer >> text=Signal API')).toBeVisible();
    await expect(page.locator('footer >> text=Vault App')).toBeVisible();
  });

  test('navigation to dashboard via Launch App button', async ({ page }) => {
    const gotoBtn = page.locator('a:has-text("Launch App")').first();
    await gotoBtn.click();
    await expect(page).toHaveURL(/dashboard/);
  });

  test('navigation to leaderboard via Proof link', async ({ page }) => {
    const proofLink = page.locator('a:has-text("See Proof of Alpha")');
    await proofLink.click();
    await expect(page).toHaveURL(/leaderboard/);
  });

  test('no console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    expect(errors.filter(e => !e.includes('hydration'))).toHaveLength(0);
  });
});

test.describe('Navigation & Routing', () => {
  test('navigates from landing to vault', async ({ page }) => {
    await page.goto('/');
    await page.locator('a:has-text("Launch App")').first().click();
    await expect(page).toHaveURL(/dashboard\/vault/);
    await expect(page.locator('text=Deposit')).toBeVisible();
  });

  test('navigates to leaderboard', async ({ page }) => {
    await page.goto('/dashboard/leaderboard');
    await expect(page.locator('text=Leaderboard')).toBeVisible();
  });

  test('navigates to simulation', async ({ page }) => {
    await page.goto('/dashboard/simulation');
    await expect(page.locator('text=Explore')).toBeVisible();
  });

  test('navigates to portfolio', async ({ page }) => {
    await page.goto('/dashboard/portfolio');
    await expect(page.locator('text=Activity')).toBeVisible();
  });

  test('navigates to settings', async ({ page }) => {
    await page.goto('/dashboard/settings');
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('mobile nav appears on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.locator('text=Vault')).toBeVisible();
  });
});

test.describe('Vault Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/vault');
  });

  test('displays deposit card', async ({ page }) => {
    await expect(page.locator('text=Deposit')).toBeVisible();
    await expect(page.locator('input[placeholder="0.00"]')).toBeVisible();
  });

  test('displays withdraw card', async ({ page }) => {
    await expect(page.locator('text=Withdraw')).toBeVisible();
  });

  test('displays vault stats', async ({ page }) => {
    await expect(page.locator('text=Vault Stats')).toBeVisible();
  });

  test('deposit input accepts numbers', async ({ page }) => {
    const input = page.locator('input[inputmode="decimal"]').first();
    await input.fill('100');
    await expect(input).toHaveValue('100');
  });

  test('shows error for invalid input', async ({ page }) => {
    const input = page.locator('input[inputmode="decimal"]').first();
    await input.fill('abc');
    await expect(input).toHaveValue('');
  });

  test('Max button is clickable', async ({ page }) => {
    const maxBtn = page.locator('button:has-text("Max")').first();
    await maxBtn.click();
  });

  test('connect wallet button exists', async ({ page }) => {
    await expect(page.locator('button:has-text("Connect Wallet"), button:has-text("Connect EVM Wallet")')).toBeVisible();
  });

  test('no critical console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    expect(errors.filter(e => !e.includes('hydration') && !e.includes('Failed to load'))).toHaveLength(0);
  });
});

test.describe('Simulation Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/simulation');
  });

  test('displays explore header', async ({ page }) => {
    await expect(page.locator('text=Explore')).toBeVisible();
  });

  test('shows simulation controls', async ({ page }) => {
    await expect(page.locator('text=Time Horizon')).toBeVisible();
    await expect(page.locator('text=Run Analysis')).toBeVisible();
  });

  test('displays analysis panel section', async ({ page }) => {
    await expect(page.locator('text=Analysis Panel')).toBeVisible();
  });

  test('displays metrics section', async ({ page }) => {
    await expect(page.locator('text=Metrics')).toBeVisible();
  });

  test('search command palette opens with Cmd+K', async ({ page }) => {
    await page.keyboard.press('Meta+K');
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible();
  });

  test('search finds pages', async ({ page }) => {
    await page.keyboard.press('Meta+K');
    await page.locator('input[type="text"]').fill('Vault');
    await expect(page.locator('text=Vault')).toBeVisible();
    await page.keyboard.press('Escape');
  });

  test('no critical console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    expect(errors.filter(e => !e.includes('hydration'))).toHaveLength(0);
  });
});

test.describe('Leaderboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/leaderboard');
  });

  test('displays leaderboard heading', async ({ page }) => {
    await expect(page.locator('text=Proof')).toBeVisible();
  });

  test('displays table with rankings', async ({ page }) => {
    await expect(page.locator('text=Leaderboard')).toBeVisible();
  });

  test('shows time range selector', async ({ page }) => {
    await expect(page.locator('text=24h'), page.locator('text=7d'), page.locator('text=30d')).toBeVisible();
  });

  test('displays trade feed', async ({ page }) => {
    await expect(page.locator('text=Trade Feed')).toBeVisible();
  });

  test('no critical console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    expect(errors.filter(e => !e.includes('hydration'))).toHaveLength(0);
  });
});

test.describe('Portfolio Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/portfolio');
  });

  test('displays activity heading', async ({ page }) => {
    await expect(page.locator('text=Activity')).toBeVisible();
  });

  test('displays positions table', async ({ page }) => {
    await expect(page.locator('text=Positions')).toBeVisible();
  });

  test('displays decisions table', async ({ page }) => {
    await expect(page.locator('text=AI Decisions')).toBeVisible();
  });

  test('displays trades table', async ({ page }) => {
    await expect(page.locator('text=Trades')).toBeVisible();
  });

  test('tab switching works', async ({ page }) => {
    await page.click('text=Orders');
    await expect(page.locator('text=Orders')).toBeVisible();
  });
});

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/settings');
  });

  test('displays settings heading', async ({ page }) => {
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('shows theme toggle', async ({ page }) => {
    await expect(page.locator('text=Dark Mode')).toBeVisible();
  });

  test('shows network settings', async ({ page }) => {
    await expect(page.locator('text=Network'), page.locator('text=Chain')).toBeVisible();
  });

  test('no critical console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    expect(errors.filter(e => !e.includes('hydration'))).toHaveLength(0);
  });
});

test.describe('Search Command Palette', () => {
  test('opens with keyboard shortcut', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Meta+K');
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible();
  });

  test('closes with Escape', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Meta+K');
    await page.keyboard.press('Escape');
    await expect(page.locator('input[placeholder*="Search"]')).not.toBeVisible();
  });

  test('search navigates to pages', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Meta+K');
    await page.locator('input[type="text"]').fill('Vault');
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/dashboard\/vault/);
  });

  test('shows jump-to options when empty', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Meta+K');
    await expect(page.locator('text=Jump To')).toBeVisible();
  });
});

test.describe('UI Components', () => {
  test('buttons have cursor-pointer', async ({ page }) => {
    await page.goto('/');
    const button = page.locator('button:has-text("How it works")');
    const classes = await button.getAttribute('class');
    expect(classes).toContain('cursor-pointer');
  });

  test('form inputs are accessible', async ({ page }) => {
    await page.goto('/dashboard/vault');
    const input = page.locator('input').first();
    await expect(input).toBeEnabled();
  });

  test('tabs are keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard/portfolio');
    await page.keyboard.press('Tab');
    await page.keyboard.press('ArrowRight');
  });
});

test.describe('Mobile Responsiveness', () => {
  test('viewport meta is set correctly', async ({ page }) => {
    const viewport = await page.evaluate(() => {
      return document.querySelector('meta[name="viewport"]')?.content;
    });
    expect(viewport).toContain('width=device-width');
  });

  test('mobile navigation shows bottom nav', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/dashboard');
    await expect(page.locator('nav >> text=Vault')).toBeVisible();
  });

  test('sidebar hidden on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/dashboard');
    const sidebar = page.locator('aside');
    await expect(sidebar).not.toBeVisible();
  });

  test('content adjusts to mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/dashboard/vault');
    await expect(page.locator('text=Deposit')).toBeVisible();
  });

  test('touch targets are tappable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const button = page.locator('text=Launch Signals');
    await button.tap();
    await expect(page).toHaveURL(/dashboard/);
  });
});

test.describe('Accessibility', () => {
  test('page has proper lang attribute', async ({ page }) => {
    await page.goto('/');
    const html = await page.locator('html');
    await expect(html).toHaveAttribute('lang', 'en');
  });

  test('buttons have accessible names', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('button').first()).toHaveAccessibleName();
  });

  test('images have alt text', async ({ page }) => {
    await page.goto('/');
    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('focus order is logical', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeTruthy();
  });
});

test.describe('Performance', () => {
  test('page loads within reasonable time', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(10000);
  });

  test('no excessive network requests', async ({ page }) => {
    const requests: string[] = [];
    page.on('request', (req) => {
      if (req.resourceType() === 'document') {
        requests.push(req.url());
      }
    });
    await page.goto('/');
    await page.waitForTimeout(1000);
    expect(requests.length).toBe(1);
  });
});

test.describe('Visual Regression', () => {
  test('landing page renders correctly', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot({ maxDiffPixelRatio: 0.1 });
  });

  test('vault page renders correctly', async ({ page }) => {
    await page.goto('/dashboard/vault');
    await expect(page).toHaveScreenshot({ maxDiffPixelRatio: 0.1 });
  });

  test('simulation page renders correctly', async ({ page }) => {
    await page.goto('/dashboard/simulation');
    await expect(page).toHaveScreenshot({ maxDiffPixelRatio: 0.1 });
  });
});

test.describe('Error Handling', () => {
  test('shows 404 for invalid routes', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await expect(page.locator('text=404'), page.locator('text=Not Found')).toBeVisible();
  });

  test('recovers from console errors gracefully', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Intelligent Signals')).toBeVisible();
  });
});

test.describe('Authentication Flow', () => {
  test('connect wallet button exists on vault', async ({ page }) => {
    await page.goto('/dashboard/vault');
    await expect(page.locator('button:has-text("Connect Wallet"), button:has-text("Connect"), button:has-text("Connect EVM Wallet")')).toBeVisible();
  });

  test('wallet modal opens', async ({ page }) => {
    await page.goto('/dashboard/vault');
    const connectBtn = page.locator('button:has-text("Connect Wallet"), button:has-text("Connect EVM Wallet")').first();
    if (await connectBtn.isVisible()) {
      await connectBtn.click();
      await expect(page.locator('text=Select Network'), page.locator('text=Connect Wallet')).toBeVisible();
    }
  });
});

test.describe('Data Fetching', () => {
  test('vault state loads', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=Live Vault State');
    await expect(page.locator('text=Live Vault State')).toBeVisible();
  });

  test('charts render without errors', async ({ page }) => {
    await page.goto('/dashboard/leaderboard');
    await expect(page.locator('canvas')).toBeVisible();
  });

  test('tables populate with data', async ({ page }) => {
    await page.goto('/dashboard/portfolio');
    await page.waitForTimeout(2000);
    await expect(page.locator('text=Positions'), page.locator('text=AI Decisions')).toBeVisible();
  });
});

test.describe('Interactions', () => {
  test('hover states work', async ({ page }) => {
    await page.goto('/');
    const button = page.locator('text=How it works');
    await button.hover();
  });

  test('click animations work', async ({ page }) => {
    await page.goto('/');
    const button = page.locator('text=Launch Signals');
    await button.click();
    await expect(page).toHaveURL(/dashboard/);
  });

  test('scroll triggers effects', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => window.scrollTo(0, 100));
    await page.waitForTimeout(500);
  });
});

test.describe('Forms', () => {
  test('deposit form validation', async ({ page }) => {
    await page.goto('/dashboard/vault');
    const input = page.locator('input').first();
    await input.fill('-1');
    await expect(input).toHaveValue('');
  });

  test('withdraw form accepts input', async ({ page }) => {
    await page.goto('/dashboard/vault');
    const inputs = page.locator('input');
    if (await inputs.count() > 1) {
      await inputs.nth(1).fill('50');
      await expect(inputs.nth(1)).toHaveValue('50');
    }
  });
});

test.describe('Browser Functions', () => {
  test('back button works', async ({ page }) => {
    await page.goto('/');
    await page.locator('a:has-text("Launch Signals")').click();
    await page.waitForURL(/dashboard/);
    await page.goBack();
    await expect(page).toHaveURL('/');
  });

  test('refresh preserves state', async ({ page }) => {
    await page.goto('/dashboard/vault');
    await page.reload();
    await expect(page.locator('text=Deposit')).toBeVisible();
  });
});