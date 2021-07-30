import { request } from '../base'

export const test = request('GET', 'rest/v2/grafana/')
export const getLabel = request('GET', 'rest/v2/grafana/get_label/')
export const getTopoTree = request('GET', 'rest/v2/grafana/topo_tree/')
export const getDimensionValues = request('GET', 'rest/v2/grafana/get_dimension_values/')
export const getVariableValue = request('POST', 'rest/v2/grafana/get_variable_value/')
export const getVariableField = request('GET', 'rest/v2/grafana/get_variable_field/')
export const timeSeriesQuery = request('POST', 'rest/v2/grafana/time_series/query/')
export const timeSeriesMetric = request('POST', 'rest/v2/grafana/time_series/metric/')
export const logQuery = request('POST', 'rest/v2/grafana/log/query/')
export const getDashboardList = request('GET', 'rest/v2/grafana/dashboards/')
export const setDefaultDashboard = request('POST', 'rest/v2/grafana/set_default_dashboard/')
export const getDefaultDashboard = request('GET', 'rest/v2/grafana/get_default_dashboard/')
export const migrateOldDashboard = request('POST', 'rest/v2/grafana/migrate_old_dashboard/')
export const getOldDashboards = request('GET', 'rest/v2/grafana/get_old_dashboards/')
export const getDirectoryTree = request('GET', 'rest/v2/grafana/get_directory_tree/')
export const createDashboardOrFolder = request('POST', 'rest/v2/grafana/create_dashboard_or_folder/')
export const saveToDashboard = request('POST', 'rest/v2/grafana/save_to_dashboard/')

export default {
  test,
  getLabel,
  getTopoTree,
  getDimensionValues,
  getVariableValue,
  getVariableField,
  timeSeriesQuery,
  timeSeriesMetric,
  logQuery,
  getDashboardList,
  setDefaultDashboard,
  getDefaultDashboard,
  migrateOldDashboard,
  getOldDashboards,
  getDirectoryTree,
  createDashboardOrFolder,
  saveToDashboard
}
