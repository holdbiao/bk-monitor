import { request } from '../base'

export const listUpgradeItems = request('GET', 'rest/v2/upgrade/list_upgrade_items/')
export const executeUpgrade = request('POST', 'rest/v2/upgrade/execute_upgrade/')
export const exportCollectorAsPlugin = request('POST', 'rest/v2/upgrade/export_collector_as_plugin/')
export const createBuildInStrategy = request('POST', 'rest/v2/upgrade/create_build_in_strategy/')
export const disableOldStrategy = request('POST', 'rest/v2/upgrade/disable_old_strategy/')
export const migrateStrategy = request('POST', 'rest/v2/upgrade/migrate_strategy/')

export default {
  listUpgradeItems,
  executeUpgrade,
  exportCollectorAsPlugin,
  createBuildInStrategy,
  disableOldStrategy,
  migrateStrategy
}
