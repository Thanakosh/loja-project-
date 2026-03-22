import { expect, test as base } from '@playwright/test'
import type { Page } from '@playwright/test'

import { mockAuthenticatedSession } from './helpers'

export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page }, use) => {
    await mockAuthenticatedSession(page)
    await use(page)
  },
})

export { expect }
